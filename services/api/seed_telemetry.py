"""Seed ≥20 mixed telemetry events for report demos / local verification."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.database import engine, init_db
from app.telemetry import orm as _telemetry_orm  # noqa: F401
from app.telemetry.models import TelemetryEvent
from app.telemetry.repository import bulk_insert_events


def _evt(
    event_type: str,
    properties: dict,
    *,
    when: datetime,
    user_id: str | None = "1",
) -> TelemetryEvent:
    return TelemetryEvent(
        eventId=str(uuid.uuid4()),
        timestamp=when.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        sessionId=str(uuid.uuid4()),
        userId=user_id,
        event_type=event_type,
        schemaVersion="1.0.0",
        requestId=str(uuid.uuid4()),
        properties=properties,
    )


def build_seed_events(now: datetime | None = None) -> list[TelemetryEvent]:
    now = now or datetime.now(timezone.utc)
    events: list[TelemetryEvent] = []
    for day_offset in range(7):
        day = now - timedelta(days=day_offset)
        events.append(
            _evt(
                "page_viewed",
                {"route": "/inventory/products"},
                when=day.replace(hour=10, minute=0, second=0, microsecond=0),
            )
        )
        events.append(
            _evt(
                "inbound_order_created",
                {
                    "location_id": 1,
                    "country": "CO",
                    "product_id": 1,
                    "product_category": "meat",
                    "quantity": 5,
                    "unit": "kg",
                    "currency": "COP",
                    "supplier_name": "Seed Supplier",
                    "order_id": 100 + day_offset,
                },
                when=day.replace(hour=11, minute=0, second=0, microsecond=0),
            )
        )
        events.append(
            _evt(
                "auth_login_succeeded",
                {"result": "success"},
                when=day.replace(hour=9, minute=0, second=0, microsecond=0),
            )
        )
        if day_offset % 2 == 0:
            events.append(
                _evt(
                    "auth_login_failed",
                    {"result": "failure", "failure_reason": "bad_credentials"},
                    when=day.replace(hour=9, minute=5, second=0, microsecond=0),
                    user_id=None,
                )
            )
        if day_offset % 3 == 0:
            events.append(
                _evt(
                    "frontend_error_captured",
                    {
                        "route": "/inventory/orders/outbound",
                        "error_name": "TypeError",
                        "message_sanitized": "seed error",
                    },
                    when=day.replace(hour=14, minute=0, second=0, microsecond=0),
                )
            )
        events.append(
            _evt(
                "api_latency_recorded",
                {
                    "route": "/inventory/products",
                    "method": "GET",
                    "status_code": 200,
                    "duration_ms": 40 + day_offset * 3,
                },
                when=day.replace(hour=12, minute=0, second=0, microsecond=0),
            )
        )
    return events


def main() -> None:
    init_db()
    events = build_seed_events()
    with Session(engine) as session:
        stored = bulk_insert_events(session, events)
    print(f"seeded telemetry events: attempted={len(events)} stored={stored}")


if __name__ == "__main__":
    main()
