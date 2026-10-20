"""WebSocket /agent/chat/ws — JWT vía ?token= o primer frame auth."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

_REPO = Path(__file__).resolve().parents[3]
_SERVICES = Path(__file__).resolve().parents[2]
_API = _SERVICES / "api"
for _p in (_REPO, _SERVICES, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.security import decode_access_token  # noqa: E402
from app.users.repository import UserRepository  # noqa: E402

from agent.chat.pubsub import get_chat_pubsub  # noqa: E402
from agent.chat.sessions import get_session_store  # noqa: E402
from agent.chat.streamer import handle_interrupt, run_streaming_turn  # noqa: E402

logger = logging.getLogger("agent.chat.ws")

ws_router = APIRouter(tags=["agent-chat"])


def _authenticate_token(token: str | None) -> Any:
    if not token or not str(token).strip():
        return None
    try:
        payload = decode_access_token(str(token).strip())
        sub = payload.get("sub")
        if sub is None:
            return None
        user = UserRepository().get(int(sub))
        return user
    except (ValueError, TypeError, Exception):  # noqa: BLE001
        return None


def _parse_json(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


@ws_router.websocket("/agent/chat/ws")
async def agent_chat_ws(websocket: WebSocket) -> None:
    """
    Handshake: ?token=&session_id=&location_id=
    o primer frame {"event":"auth","data":{"token":"..."}}.

    Rechaza antes de eventos de chat si el JWT es inválido.
    """
    query = websocket.query_params
    token = query.get("token")
    session_id_q = query.get("session_id")
    location_id = query.get("location_id")

    await websocket.accept()

    user = _authenticate_token(token)

    # Auth frame si no vino ?token= válido
    if user is None:
        if token:
            await websocket.send_json(
                {"event": "error", "data": {"detail": "Token inválido o expirado"}}
            )
            await websocket.close(code=4401)
            return
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        except (asyncio.TimeoutError, WebSocketDisconnect):
            await websocket.close(code=4401)
            return
        frame = _parse_json(raw) or {}
        if frame.get("event") != "auth":
            await websocket.send_json(
                {
                    "event": "error",
                    "data": {"detail": "Se requiere frame auth o ?token="},
                }
            )
            await websocket.close(code=4401)
            return
        auth_token = (frame.get("data") or {}).get("token")
        user = _authenticate_token(auth_token)
        if user is None:
            await websocket.send_json(
                {"event": "error", "data": {"detail": "Token inválido o expirado"}}
            )
            await websocket.close(code=4401)
            return

    user_id = str(getattr(user, "id", None) or getattr(user, "email", "") or "unknown")
    store = get_session_store()
    bus = get_chat_pubsub()

    # session_id del handshake (mismo valor = LangGraph thread_id)
    if session_id_q:
        session = store.get_or_create(
            session_id=session_id_q, user_id=user_id, location_id=location_id
        )
    else:
        session = store.get_or_create(
            session_id=None, user_id=user_id, location_id=location_id
        )

    session_id = session.session_id
    queue = bus.subscribe(session_id)

    # Rehidratación
    await websocket.send_json(
        {
            "event": "session_snapshot",
            "data": {
                "session_id": session_id,
                "messages": session.snapshot()["messages"],
                "status": session.status,
                "agent_id": session.agent_id,
                "location_id": session.location_id,
            },
        }
    )

    async def pump_bus() -> None:
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                await websocket.send_json(item)
        except (WebSocketDisconnect, asyncio.CancelledError):
            return
        except Exception:  # noqa: BLE001
            logger.exception("ws pump failed session=%s", session_id)

    pump_task = asyncio.create_task(pump_bus())
    turn_task: asyncio.Task | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            frame = _parse_json(raw)
            if not frame:
                await websocket.send_json(
                    {"event": "error", "data": {"detail": "JSON inválido"}}
                )
                continue

            event = frame.get("event")
            data = frame.get("data") if isinstance(frame.get("data"), dict) else {}
            # Permitir session_id en data; debe coincidir con el del socket
            sid = data.get("session_id") or session_id
            if sid != session_id:
                await websocket.send_json(
                    {
                        "event": "error",
                        "data": {
                            "detail": "session_id no coincide con el handshake",
                        },
                    }
                )
                continue

            if event == "user_message":
                text = str(data.get("text") or "").strip()
                if not text:
                    continue
                # Si hay generación activa → tratar como interrupt + new_input
                current = store.get(session_id)
                if current and current.active_generation_id:
                    await handle_interrupt(
                        session_id=session_id,
                        new_input=text,
                        user_id=user_id,
                    )
                else:
                    if turn_task and not turn_task.done():
                        await handle_interrupt(
                            session_id=session_id,
                            new_input=text,
                            user_id=user_id,
                        )
                    else:
                        turn_task = asyncio.create_task(
                            run_streaming_turn(
                                session_id=session_id,
                                text=text,
                                user_id=user_id,
                            )
                        )

            elif event == "interrupt_requested":
                new_input = data.get("new_input")
                new_text = str(new_input).strip() if new_input else None
                await handle_interrupt(
                    session_id=session_id,
                    new_input=new_text,
                    user_id=user_id,
                )

            elif event == "ping":
                await websocket.send_json({"event": "pong", "data": {"session_id": session_id}})

            else:
                await websocket.send_json(
                    {
                        "event": "error",
                        "data": {"detail": f"Evento desconocido: {event}"},
                    }
                )
    except WebSocketDisconnect:
        logger.info("ws disconnected session=%s", session_id)
    finally:
        pump_task.cancel()
        bus.unsubscribe(session_id, queue)
        try:
            await pump_task
        except asyncio.CancelledError:
            pass
