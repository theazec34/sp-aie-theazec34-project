"""Stub telemetry intake tests."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.database import engine
from app.telemetry.orm import TelemetryEventRow


def _valid_event(**overrides):
    base = {
        "eventId": str(uuid.uuid4()),
        "timestamp": "2026-08-21T12:00:00.000Z",
        "sessionId": "22222222-2222-4222-8222-222222222222",
        "userId": "1",
        "event_type": "inbound_order_created",
        "schemaVersion": "1.0.0",
        "requestId": str(uuid.uuid4()),
        "properties": {
            "location_id": 1,
            "country": "CO",
            "product_id": 1,
            "product_category": "meat",
            "quantity": 10,
            "unit": "kg",
            "currency": "COP",
            "supplier_name": "Test Supplier",
            "order_id": 99,
            "email": "should-not-persist@example.com",
        },
    }
    base.update(overrides)
    return base


def test_telemetry_events_stores_batch(client):
    inbound_id = str(uuid.uuid4())
    auth_id = str(uuid.uuid4())
    inbound_req = str(uuid.uuid4())
    payload = {
        "events": [
            _valid_event(eventId=inbound_id, requestId=inbound_req),
            _valid_event(
                eventId=auth_id,
                timestamp="2026-08-21T12:00:01.000Z",
                event_type="auth_login_failed",
                requestId=str(uuid.uuid4()),
                properties={
                    "result": "failure",
                    "failure_reason": "bad_credentials",
                },
            ),
        ]
    }
    response = client.post("/telemetry/events", json=payload)
    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 2, "rejected": 0}

    with Session(engine) as session:
        rows = session.exec(
            select(TelemetryEventRow).where(
                TelemetryEventRow.event_id.in_([inbound_id, auth_id])
            )
        ).all()
    assert len(rows) == 2
    by_type = {row.event_type: row for row in rows}
    inbound = by_type["inbound_order_created"]
    assert inbound.service == "backoffice"
    assert inbound.tags["location_id"] == 1
    assert "email" not in inbound.tags
    assert inbound.tags["request_id"] == inbound_req
    assert by_type["auth_login_failed"].tags["failure_reason"] == "bad_credentials"


def test_telemetry_events_partial_acceptance(client):
    good_a = str(uuid.uuid4())
    good_b = str(uuid.uuid4())
    payload = {
        "events": [
            _valid_event(eventId=good_a),
            {"event_type": "broken", "properties": {}},
            _valid_event(
                eventId=good_b,
                timestamp="2026-08-21T12:00:02.000Z",
                event_type="page_viewed",
                properties={"route": "/inventory/products"},
            ),
        ]
    }
    response = client.post("/telemetry/events", json=payload)
    assert response.status_code == 200
    assert response.json() == {"received": 3, "stored": 2, "rejected": 1}

    with Session(engine) as session:
        stored = session.exec(
            select(TelemetryEventRow).where(
                TelemetryEventRow.event_id.in_([good_a, good_b])
            )
        ).all()
    assert len(stored) == 2


def test_telemetry_events_rejects_empty_batch(client):
    response = client.post("/telemetry/events", json={"events": []})
    assert response.status_code in (400, 422)


def test_telemetry_config_exposes_endpoint(client):
    response = client.get("/telemetry/config")
    assert response.status_code == 200
    data = response.json()
    assert "TELEMETRY_ENDPOINT" in data
    assert "TELEMETRY_SERVICE" in data
