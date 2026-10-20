"""SSE RFP — text/event-stream, eventos nombrados, JWT, replay Last-Event-ID."""

from __future__ import annotations

import json
import threading
import time

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


def test_stream_requires_jwt(client: TestClient):
    res = client.get("/rfp/events/stream")
    assert res.status_code in (401, 403)


def test_stream_headers_and_named_event(
    client: TestClient,
    auth_header: dict[str, str],
):
    from app.rfp.sse_hub import EVENT_RFP_TICKET_CREATED, publish_rfp_ticket_created

    def _publish():
        time.sleep(0.15)
        publish_rfp_ticket_created(
            ticket_id=7,
            status="analizando",
            original_filename="demo.pdf",
        )

    threading.Thread(target=_publish, daemon=True).start()

    with client.stream(
        "GET",
        "/rfp/events/stream",
        headers={**auth_header, "Accept": "text/event-stream"},
    ) as res:
        assert res.status_code == 200
        ctype = res.headers.get("content-type", "")
        assert "text/event-stream" in ctype

        buf = b""
        deadline = time.time() + 5
        for chunk in res.iter_bytes():
            buf += chunk
            if EVENT_RFP_TICKET_CREATED.encode() in buf and b"data:" in buf:
                break
            if time.time() > deadline:
                break

    text = buf.decode("utf-8", errors="replace")
    assert f"event: {EVENT_RFP_TICKET_CREATED}" in text
    assert "data:" in text
    data_line = next(line for line in text.splitlines() if line.startswith("data:"))
    payload = json.loads(data_line.split("data:", 1)[1].strip())
    assert payload["ticket_id"] == 7
    assert payload["status"] == "analizando"


def test_replay_since_last_event_id(
    client: TestClient,
    auth_header: dict[str, str],
):
    from app.rfp.sse_hub import publish_rfp_ticket_created

    first = publish_rfp_ticket_created(ticket_id=1, status="analizando")
    second = publish_rfp_ticket_created(ticket_id=2, status="analizando")
    assert second.id > first.id

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
        buf = b""
        deadline = time.time() + 3
        for chunk in res.iter_bytes():
            buf += chunk
            if b"ticket_id" in buf and str(second.id).encode() in buf:
                # keepalive may follow; enough to assert replay
                if b"ticket_id\": 2" in buf or b'"ticket_id": 2' in buf:
                    break
            if time.time() > deadline:
                break

    text = buf.decode("utf-8", errors="replace")
    assert '"ticket_id": 2' in text or '"ticket_id":2' in text
    # No debe reenviar el evento ya visto (id == first)
    assert f'"ticket_id": 1' not in text and '"ticket_id":1' not in text


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
