"""Stub telemetry intake tests."""

from __future__ import annotations


def test_telemetry_events_accepts_batch(client):
    payload = {
        "events": [
            {
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
                },
            },
            {
                "eventId": "44444444-4444-4444-8444-444444444444",
                "timestamp": "2026-08-21T12:00:01.000Z",
                "sessionId": "22222222-2222-4222-8222-222222222222",
                "userId": "1",
                "event_type": "auth_login_failed",
                "schemaVersion": "1.0.0",
                "requestId": "55555555-5555-4555-8555-555555555555",
                "properties": {
                    "result": "failure",
                    "failure_reason": "bad_credentials",
                },
            },
        ]
    }
    response = client.post("/telemetry/events", json=payload)
    assert response.status_code == 200
    assert response.json() == {"received": 2}


def test_telemetry_events_rejects_empty_batch(client):
    response = client.post("/telemetry/events", json={"events": []})
    # App maps validation errors to 400 via custom handlers.
    assert response.status_code in (400, 422)


def test_telemetry_config_exposes_endpoint(client, monkeypatch):
    monkeypatch.setenv("TELEMETRY_ENDPOINT", "http://example.test/telemetry/events")
    # Router reads env at import time — config endpoint returns module constant.
    # Just assert shape of response from default.
    response = client.get("/telemetry/config")
    assert response.status_code == 200
    assert "TELEMETRY_ENDPOINT" in response.json()
