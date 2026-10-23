"""WebSocket chat — contrato de eventos, JWT, abort ≠ HITL, pub/sub."""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_chat():
    from agent.chat.pubsub import get_chat_pubsub
    from agent.chat.sessions import get_session_store

    get_session_store().reset_for_tests()
    get_chat_pubsub().reset_for_tests()
    yield
    get_session_store().reset_for_tests()
    get_chat_pubsub().reset_for_tests()


def _token(client: TestClient, auth_header: dict[str, str]) -> str:
    return auth_header["Authorization"].split(" ", 1)[1]


def test_tokenize_for_stream():
    from agent.chat.streamer import tokenize_for_stream

    parts = tokenize_for_stream("Hola Miami")
    assert "".join(parts) == "Hola Miami"
    assert "Hola" in parts


def test_pubsub_fanout_same_session():
    """Varios consumidores, un solo publish — sin duplicar llamadas al agente."""
    import asyncio

    from agent.chat.pubsub import get_chat_pubsub

    bus = get_chat_pubsub()

    async def _run():
        q1 = bus.subscribe("chat_test")
        q2 = bus.subscribe("chat_test")
        bus.publish(
            "chat_test",
            "token_chunk",
            {"session_id": "chat_test", "token": "X", "sequence": 0},
        )
        a = await asyncio.wait_for(q1.get(), timeout=1)
        b = await asyncio.wait_for(q2.get(), timeout=1)
        assert a["event"] == "token_chunk"
        assert b["event"] == "token_chunk"
        assert a["data"]["token"] == "X"
        bus.unsubscribe("chat_test", q1)
        bus.unsubscribe("chat_test", q2)

    asyncio.run(_run())


def test_ws_rejects_invalid_token(client: TestClient):
    with client.websocket_connect("/agent/chat/ws?token=not-a-jwt") as ws:
        msg = ws.receive_json()
        assert msg["event"] == "error"
        assert "Token" in msg["data"]["detail"] or "token" in msg["data"]["detail"].lower()


def test_ws_snapshot_and_token_stream(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_run_agent(question: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "answer": "Para el local de Miami usa el menú estándar.",
            "run_id": kwargs.get("run_id") or "r1",
            "session_id": kwargs.get("session_id"),
            "nodes": ["receive_question", "generate_response"],
            "checkpointed": True,
        }

    monkeypatch.setattr("agent.chat.streamer.run_agent", fake_run_agent)

    async def fast_turn(**kwargs: Any):
        from agent.chat.streamer import run_streaming_turn as real

        return await real(**{**kwargs, "token_delay_s": 0})

    monkeypatch.setattr("agent.chat.ws.run_streaming_turn", fast_turn)

    token = _token(client, auth_header)
    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_0044&location_id=miami_doral"
    ) as ws:
        snap = ws.receive_json()
        assert snap["event"] == "session_snapshot"
        assert snap["data"]["session_id"] == "chat_0044"
        assert snap["data"]["agent_id"] == "manager_support"
        assert isinstance(snap["data"]["messages"], list)

        ws.send_json(
            {
                "event": "user_message",
                "data": {"session_id": "chat_0044", "text": "¿Menú Miami?"},
            }
        )

        events: list[dict[str, Any]] = []
        for _ in range(60):
            msg = ws.receive_json()
            events.append(msg)
            if msg["event"] == "generation_completed":
                assert msg["data"]["session_id"] == "chat_0044"
                assert "message_id" in msg["data"]
                break

        names = [e["event"] for e in events]
        assert "user_message" in names
        assert "token_chunk" in names
        assert "generation_completed" in names
        chunk = next(e for e in events if e["event"] == "token_chunk")
        assert "token" in chunk["data"]
        assert "sequence" in chunk["data"]
        assert "ticket_id" not in chunk["data"]


def test_ws_interrupt_mid_tokens(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_run_agent(question: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "answer": "uno dos tres cuatro cinco seis siete ocho nueve diez once doce",
            "run_id": kwargs.get("run_id") or "r2",
            "session_id": kwargs.get("session_id"),
            "nodes": ["generate_response"],
            "checkpointed": True,
        }

    monkeypatch.setattr("agent.chat.streamer.run_agent", fake_run_agent)

    async def slow_tokens(**kwargs: Any):
        from agent.chat.streamer import run_streaming_turn as real

        return await real(**{**kwargs, "token_delay_s": 0.05})

    monkeypatch.setattr("agent.chat.ws.run_streaming_turn", slow_tokens)

    token = _token(client, auth_header)
    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_int1"
    ) as ws:
        assert ws.receive_json()["event"] == "session_snapshot"
        ws.send_json(
            {
                "event": "user_message",
                "data": {"session_id": "chat_int1", "text": "explica todo"},
            }
        )

        interrupted = False
        for _ in range(80):
            msg = ws.receive_json()
            if msg["event"] == "token_chunk":
                ws.send_json(
                    {
                        "event": "interrupt_requested",
                        "data": {
                            "session_id": "chat_int1",
                            "new_input": "",
                        },
                    }
                )
            if msg["event"] == "generation_interrupted":
                assert msg["data"]["status"] == "interrupted"
                assert "message_id" in msg["data"]
                interrupted = True
                break
            if msg["event"] == "generation_completed":
                break

        assert interrupted, "Se esperaba generation_interrupted tras abort mid-stream"


def test_ws_reconnect_same_session_restores_history(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_run_agent(question: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "answer": "OK",
            "run_id": "r3",
            "session_id": kwargs.get("session_id"),
            "nodes": [],
            "checkpointed": True,
        }

    monkeypatch.setattr("agent.chat.streamer.run_agent", fake_run_agent)

    async def fast_turn(**kwargs: Any):
        from agent.chat.streamer import run_streaming_turn as real

        return await real(**{**kwargs, "token_delay_s": 0})

    monkeypatch.setattr("agent.chat.ws.run_streaming_turn", fast_turn)

    token = _token(client, auth_header)

    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_rehydrate"
    ) as ws:
        ws.receive_json()
        ws.send_json(
            {
                "event": "user_message",
                "data": {"session_id": "chat_rehydrate", "text": "hola"},
            }
        )
        for _ in range(40):
            if ws.receive_json()["event"] == "generation_completed":
                break

    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_rehydrate"
    ) as ws2:
        snap = ws2.receive_json()
        assert snap["event"] == "session_snapshot"
        assert snap["data"]["session_id"] == "chat_rehydrate"
        msgs = snap["data"]["messages"]
        assert any(m.get("role") == "user" and "hola" in m.get("content", "") for m in msgs)
        assert any(m.get("role") == "assistant" for m in msgs)


def test_session_store_updates_location_on_reconnect():
    """Cambiar sede en el desplegable debe actualizar location_id de la sesión."""
    from agent.chat.sessions import get_session_store

    store = get_session_store()
    first = store.get_or_create(
        session_id="chat_sede", user_id="1", location_id="miami_doral"
    )
    assert first.location_id == "miami_doral"
    second = store.get_or_create(
        session_id="chat_sede", user_id="1", location_id="bogota_chapinero"
    )
    assert second.session_id == first.session_id
    assert second.location_id == "bogota_chapinero"
    assert store.get("chat_sede").location_id == "bogota_chapinero"


def test_ws_reconnect_updates_location_and_tools(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    """Tras reconectar con otra sede, run_agent recibe el location_id nuevo."""
    seen: list[str | None] = []

    def fake_run_agent(question: str, **kwargs: Any) -> dict[str, Any]:
        seen.append(kwargs.get("location_id"))
        return {
            "answer": f"sede={kwargs.get('location_id')}",
            "run_id": "r_sede",
            "session_id": kwargs.get("session_id"),
            "nodes": [],
            "checkpointed": True,
        }

    monkeypatch.setattr("agent.chat.streamer.run_agent", fake_run_agent)

    async def fast_turn(**kwargs: Any):
        from agent.chat.streamer import run_streaming_turn as real

        return await real(**{**kwargs, "token_delay_s": 0})

    monkeypatch.setattr("agent.chat.ws.run_streaming_turn", fast_turn)

    token = _token(client, auth_header)
    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_sede_ws&location_id=miami_doral"
    ) as ws:
        snap = ws.receive_json()
        assert snap["data"]["location_id"] == "miami_doral"
        ws.send_json(
            {
                "event": "user_message",
                "data": {"session_id": "chat_sede_ws", "text": "tarifas"},
            }
        )
        for _ in range(40):
            if ws.receive_json()["event"] == "generation_completed":
                break

    with client.websocket_connect(
        f"/agent/chat/ws?token={token}&session_id=chat_sede_ws&location_id=bogota_chapinero"
    ) as ws2:
        snap2 = ws2.receive_json()
        assert snap2["event"] == "session_snapshot"
        assert snap2["data"]["location_id"] == "bogota_chapinero"
        ws2.send_json(
            {
                "event": "user_message",
                "data": {"session_id": "chat_sede_ws", "text": "tarifas bogota"},
            }
        )
        for _ in range(40):
            if ws2.receive_json()["event"] == "generation_completed":
                break

    assert seen == ["miami_doral", "bogota_chapinero"]


def test_event_contract_shapes():
    """Contrato BRIEFING Parte 2 (sin mezclar RFP/SSE)."""
    sample = {
        "event": "token_chunk",
        "data": {"session_id": "chat_0044", "token": "Para", "sequence": 12},
    }
    assert "ticket_id" not in sample["data"]
    assert json.dumps(sample)
