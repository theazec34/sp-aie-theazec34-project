"""Telemetry storage tests: partial validation + bulk insert."""

from __future__ import annotations

from sqlmodel import Session, select

from app.database import engine
from app.telemetry.orm import TelemetryEventRow


def _valid_event(**overrides):
    base = {
        "eventId": "11111111-1111-4111-8111-111111111111",
        "timestamp": "2026-08-21T12:00:00.000Z",
        "sessionId": "22222222-2222-4222-8222-222222222222",
        "userId": "1",
        "event_type": "inbound_order_created",
        "schemaVersion": "1.0.0",
        "requestId": "33333333-3333-4333-8333-333333333333",
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
    payload = {
        "events": [
            _valid_event(),
            _valid_event(
                eventId="44444444-4444-4444-8444-444444444444",
                timestamp="2026-08-21T12:00:01.000Z",
                event_type="auth_login_failed",
                requestId="55555555-5555-4555-8555-555555555555",
                properties={
                    "result": "failure",
                    "failure_reason": "bad_credentials",
                },
            ),
        ]
    }
    response = client.post("/telemetry/events", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body == {"received": 2, "stored": 2, "rejected": 0}

    with Session(engine) as session:
        rows = session.exec(
            select(TelemetryEventRow).where(
                TelemetryEventRow.event_id.in_(
                    [
                        "11111111-1111-4111-8111-111111111111",
                        "44444444-4444-4444-8444-444444444444",
                    ]
                )
            )
        ).all()
    assert len(rows) == 2
    by_type = {row.event_type: row for row in rows}
    inbound = by_type["inbound_order_created"]
    assert inbound.service == "backoffice"
    assert inbound.tags["location_id"] == 1
    assert inbound.tags["country"] == "CO"
    assert "email" not in inbound.tags
    assert inbound.tags["schema_version"] == "1.0.0"
    assert inbound.tags["request_id"] == "33333333-3333-4333-8333-333333333333"
    assert by_type["auth_login_failed"].tags["failure_reason"] == "bad_credentials"


def test_telemetry_events_partial_acceptance(client):
    payload = {
        "events": [
            _valid_event(
                eventId="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                requestId="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            ),
            {"event_type": "broken", "properties": {}},
            _valid_event(
                eventId="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                timestamp="2026-08-21T12:00:02.000Z",
                event_type="page_viewed",
                requestId="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
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
                TelemetryEventRow.event_id.in_(
                    [
                        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                        "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    ]
                )
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
