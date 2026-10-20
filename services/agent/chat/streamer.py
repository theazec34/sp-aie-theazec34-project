"""Productor de tokens desacoplado del WebSocket.

Invoca el grafo existente (`run_agent`) sin cambiar nodos/tools/memoria.
Emite `token_chunk` con abort comprobable entre tokens (no HITL interrupt()).
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Any

from agent.chat.pubsub import get_chat_pubsub
from agent.chat.sessions import ChatMessage, get_session_store
from agent.graph import run_agent

logger = logging.getLogger("agent.chat.streamer")

# Abort flags por generation_id (no confundir con LangGraph interrupt HITL)
_ABORT: dict[str, asyncio.Event] = {}
_ABORT_LOCK = asyncio.Lock()


def tokenize_for_stream(text: str) -> list[str]:
    """Parte la respuesta en tokens visibles (palabras + espacios/puntuación)."""
    if not text:
        return []
    parts = re.findall(r"\S+|\s+", text)
    return parts or [text]


async def request_abort(generation_id: str) -> None:
    async with _ABORT_LOCK:
        ev = _ABORT.get(generation_id)
        if ev is not None:
            ev.set()


def is_aborted(generation_id: str) -> bool:
    ev = _ABORT.get(generation_id)
    return bool(ev and ev.is_set())


async def _register_generation(generation_id: str) -> asyncio.Event:
    ev = asyncio.Event()
    async with _ABORT_LOCK:
        _ABORT[generation_id] = ev
    return ev


async def _unregister_generation(generation_id: str) -> None:
    async with _ABORT_LOCK:
        _ABORT.pop(generation_id, None)


async def run_streaming_turn(
    *,
    session_id: str,
    text: str,
    user_id: str | None,
    token_delay_s: float = 0.02,
) -> dict[str, Any]:
    """
    Un turno: user_message → tokens → completed | interrupted.

    El productor publica al canal `chat.<session_id>`; los WS solo consumen.
    """
    store = get_session_store()
    bus = get_chat_pubsub()
    session = store.get(session_id)
    if session is None:
        raise ValueError(f"Sesión desconocida: {session_id}")

    generation_id = f"gen_{uuid.uuid4().hex[:10]}"
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    abort_ev = await _register_generation(generation_id)

    user_msg = ChatMessage(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        role="user",
        content=text,
        status="complete",
    )
    store.append_message(session_id, user_msg)
    bus.publish(
        session_id,
        "user_message",
        {"session_id": session_id, "message_id": user_msg.message_id, "text": text},
    )

    assistant = ChatMessage(
        message_id=message_id,
        role="assistant",
        content="",
        status="streaming",
    )
    store.append_message(session_id, assistant)
    store.set_active_generation(
        session_id, generation_id=generation_id, message_id=message_id
    )
    store.set_status(session_id, "active")

    try:
        # Grafo sync en thread — la capa de canal no altera nodos
        result = await asyncio.to_thread(
            run_agent,
            text,
            session_id=session_id,
            user_id=user_id,
            run_id=generation_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent turn failed session=%s", session_id)
        store.update_message(
            session_id, message_id, content="No pude completar la respuesta.", status="complete"
        )
        store.set_active_generation(session_id, generation_id=None, message_id=None)
        await _unregister_generation(generation_id)
        bus.publish(
            session_id,
            "generation_completed",
            {
                "session_id": session_id,
                "message_id": message_id,
                "error": str(exc),
            },
        )
        return {"message_id": message_id, "status": "error"}

    # Si abortaron mientras corría el grafo: no emitir tokens; marcar interrupted
    if abort_ev.is_set():
        store.update_message(session_id, message_id, content="", status="interrupted")
        store.set_status(session_id, "interrupted")
        store.set_active_generation(session_id, generation_id=None, message_id=None)
        bus.publish(
            session_id,
            "generation_interrupted",
            {
                "session_id": session_id,
                "message_id": message_id,
                "status": "interrupted",
            },
        )
        await _unregister_generation(generation_id)
        return {"message_id": message_id, "status": "interrupted"}

    answer = str(result.get("answer") or "")
    partial: list[str] = []
    for sequence, token in enumerate(tokenize_for_stream(answer)):
        if abort_ev.is_set():
            content = "".join(partial)
            store.update_message(
                session_id, message_id, content=content, status="interrupted"
            )
            store.set_status(session_id, "interrupted")
            store.set_active_generation(session_id, generation_id=None, message_id=None)
            bus.publish(
                session_id,
                "generation_interrupted",
                {
                    "session_id": session_id,
                    "message_id": message_id,
                    "status": "interrupted",
                },
            )
            await _unregister_generation(generation_id)
            return {
                "message_id": message_id,
                "status": "interrupted",
                "partial": content,
            }

        partial.append(token)
        store.update_message(session_id, message_id, content="".join(partial))
        bus.publish(
            session_id,
            "token_chunk",
            {
                "session_id": session_id,
                "message_id": message_id,
                "token": token,
                "sequence": sequence,
            },
        )
        if token_delay_s > 0:
            await asyncio.sleep(token_delay_s)

    store.update_message(session_id, message_id, content=answer, status="complete")
    store.set_status(session_id, "active")
    store.set_active_generation(session_id, generation_id=None, message_id=None)
    bus.publish(
        session_id,
        "generation_completed",
        {"session_id": session_id, "message_id": message_id},
    )
    await _unregister_generation(generation_id)
    return {"message_id": message_id, "status": "complete", "answer": answer}


async def handle_interrupt(
    *,
    session_id: str,
    new_input: str | None = None,
    user_id: str | None = None,
) -> None:
    """Abort del stream actual (no es LangGraph HITL interrupt())."""
    store = get_session_store()
    bus = get_chat_pubsub()
    session = store.get(session_id)
    if session is None:
        return

    bus.publish(
        session_id,
        "interrupt_requested",
        {"session_id": session_id, "new_input": new_input or ""},
    )

    gen_id = session.active_generation_id
    if gen_id:
        await request_abort(gen_id)

    # Nuevo turno solo si hay texto; no sobrescribe el mensaje interrupted
    if new_input and new_input.strip():
        # Espera breve a que el productor cierre el turno abortado
        await asyncio.sleep(0.05)
        asyncio.create_task(
            run_streaming_turn(
                session_id=session_id,
                text=new_input.strip(),
                user_id=user_id,
            )
        )
