"""SSE RFP — text/event-stream, eventos nombrados, JWT, replay Last-Event-ID."""

from __future__ import annotations

import json
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_hub():
    from app.rfp.sse_hub import reset_sse_hub_for_tests

    reset_sse_hub_for_tests()
    yield
    reset_sse_hub_for_tests()


def test_sse_event_encode_named_and_json():
    from app.rfp.sse_hub import (
        EVENT_RFP_TICKET_CREATED,
        publish_rfp_ticket_created,
    )

    ev = publish_rfp_ticket_created(
        ticket_id=42,
        status="analizando",
        original_filename="brasaland-request-1.pdf",
        client_name="Sunset Bay Resorts",
        departments_needed=["marketing", "operaciones", "procurement", "training"],
    )
    raw = ev.encode()
    assert f"event: {EVENT_RFP_TICKET_CREATED}" in raw
    assert "event: message" not in raw
    assert raw.startswith("id: ")
    assert "\ndata: " in raw
    data_line = next(line for line in raw.splitlines() if line.startswith("data: "))
    payload = json.loads(data_line[len("data: ") :])
    assert payload["ticket_id"] == 42
    assert payload["status"] == "analizando"
    assert payload["currency"] == "EUR"
    assert payload["currency_symbol"] == "€"
    assert "Sunset Bay Resorts" in payload["client_name"]


def test_sales_drop_alert_encode():
    from app.rfp.sse_hub import EVENT_SALES_DROP_ALERT, publish_sales_drop_alert

    ev = publish_sales_drop_alert(country="CO", drop_pct=18.2, week_label="2026-W42")
    raw = ev.encode()
    assert f"event: {EVENT_SALES_DROP_ALERT}" in raw
    payload = json.loads(next(l for l in raw.splitlines() if l.startswith("data: "))[6:])
    assert payload["threshold_pct"] == 15.0
    assert payload["drop_pct"] == 18.2
    assert "Mariana Restrepo" in payload["notify"]


def test_replay_since_filters_seen():
    from app.rfp.sse_hub import get_sse_hub, publish_rfp_ticket_created

    first = publish_rfp_ticket_created(ticket_id=1, status="analizando")
    second = publish_rfp_ticket_created(ticket_id=2, status="analizando")
    hub = get_sse_hub()
    replay = hub.replay_since(first.id)
    assert [e.id for e in replay] == [second.id]
    assert hub.replay_since(None) == []
    assert hub.replay_since(second.id) == []


def test_stream_requires_jwt(client: TestClient):
    res = client.get("/rfp/events/stream")
    assert res.status_code in (401, 403)


def test_stream_headers_named_event_and_json(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    """Stream finito (monkeypatch) para no colgar TestClient en el loop SSE."""
    from app.rfp.sse_hub import EVENT_RFP_TICKET_CREATED, publish_rfp_ticket_created

    ev = publish_rfp_ticket_created(
        ticket_id=7,
        status="analizando",
        original_filename="demo.pdf",
    )

    async def finite_stream(
        *, last_event_id: int | None = None, keepalive_seconds: float = 15.0
    ) -> AsyncIterator[str]:
        yield ev.encode()
        yield ": keepalive\n\n"

    monkeypatch.setattr("app.rfp.router.stream_events", finite_stream)

    with client.stream(
        "GET",
        "/rfp/events/stream",
        headers={**auth_header, "Accept": "text/event-stream"},
    ) as res:
        assert res.status_code == 200
        ctype = res.headers.get("content-type", "")
        assert "text/event-stream" in ctype
        text = res.read().decode("utf-8")

    assert f"event: {EVENT_RFP_TICKET_CREATED}" in text
    assert "event: message" not in text
    assert ": keepalive" in text
    data_line = next(line for line in text.splitlines() if line.startswith("data:"))
    payload = json.loads(data_line.split("data:", 1)[1].strip())
    assert payload["ticket_id"] == 7
    assert payload["status"] == "analizando"
    assert payload["original_filename"] == "demo.pdf"


def test_stream_replays_last_event_id(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    from app.rfp.sse_hub import get_sse_hub, publish_rfp_ticket_created, stream_events

    first = publish_rfp_ticket_created(ticket_id=1, status="analizando")
    second = publish_rfp_ticket_created(ticket_id=2, status="analizando")

    async def finite_replay(
        *, last_event_id: int | None = None, keepalive_seconds: float = 15.0
    ) -> AsyncIterator[str]:
        # Solo replay (sin loop infinito)
        for ev in get_sse_hub().replay_since(last_event_id):
            yield ev.encode()

    monkeypatch.setattr("app.rfp.router.stream_events", finite_replay)

    with client.stream(
        "GET",
        "/rfp/events/stream",
        headers={
            **auth_header,
            "Accept": "text/event-stream",
            "Last-Event-ID": str(first.id),
        },
    ) as res:
        assert res.status_code == 200
        text = res.read().decode("utf-8")

    assert '"ticket_id": 2' in text
    assert '"ticket_id": 1' not in text
    assert second.data["ticket_id"] == 2
    assert stream_events is not None


def test_post_sales_drop_alert_publishes(
    client: TestClient,
    auth_header: dict[str, str],
):
    res = client.post(
        "/rfp/events/sales-drop-alert",
        headers=auth_header,
        json={"country": "US", "drop_pct": 16.0, "week_label": "2026-W41"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["event"] == "sales_drop_alert"
    assert body["drop_pct"] == 16.0

    bad = client.post(
        "/rfp/events/sales-drop-alert",
        headers=auth_header,
        json={"country": "US", "drop_pct": 10.0, "week_label": "2026-W41"},
    )
    assert bad.status_code == 400
