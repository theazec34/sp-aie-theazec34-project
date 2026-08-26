"""Tests for weekly location performance pipeline + reporting API."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from app.database import engine, init_db
from app.telemetry import orm as _telemetry_orm  # noqa: F401
from app.telemetry.models import TelemetryEvent
from app.telemetry.repository import bulk_insert_events


def _week_monday() -> date:
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=today.weekday())


def _seed_week_events(week_start: date | None = None) -> date:
    init_db()
    week_start = week_start or date(2020, 1, 6)  # fixed Monday — isolate from local seeds
    start = datetime(
        week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc
    )
    end = start + timedelta(days=7)
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM telemetry_events WHERE timestamp >= :start AND timestamp < :end"
            ),
            {"start": start, "end": end},
        )

    base = datetime(
        week_start.year, week_start.month, week_start.day, 12, tzinfo=timezone.utc
    )

    def evt(etype: str, props: dict, hours: int = 0) -> TelemetryEvent:
        when = base + timedelta(hours=hours)
        return TelemetryEvent(
            eventId=str(uuid.uuid4()),
            timestamp=when.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            sessionId=str(uuid.uuid4()),
            userId="1",
            event_type=etype,
            schemaVersion="1.0.0",
            requestId=str(uuid.uuid4()),
            properties=props,
        )

    events = [
        evt(
            "inbound_order_created",
            {
                "location_id": 1,
                "country": "CO",
                "product_id": 1,
                "product_category": "meat",
                "quantity": 10,
                "unit": "kg",
                "currency": "COP",
                "supplier_name": "S",
                "order_id": 1,
                "total_cost": 10000,
            },
            1,
        ),
        evt(
            "stock_waste_registered",
            {
                "location_id": 1,
                "country": "CO",
                "product_id": 1,
                "product_category": "meat",
                "quantity": 1,
                "unit": "kg",
                "currency": "COP",
                "reason": "expired",
                "order_id": 2,
                "total_cost": 1000,
            },
            2,
        ),
    ]
    with Session(engine) as session:
        bulk_insert_events(session, events)
    return week_start


def test_pipeline_idempotent_upsert():
    from data.pipelines.pipeline import weekly_location_performance_flow
    from data.pipelines.weekly_location_performance.db import (
        query_weekly_location_performance,
    )

    week_start = _seed_week_events()
    first = weekly_location_performance_flow(
        week_start=week_start, triggered_by="test"
    )
    second = weekly_location_performance_flow(
        week_start=week_start, triggered_by="test"
    )
    assert first["status"] == "completed"
    assert second["status"] == "completed"
    report = query_weekly_location_performance(week_start)
    locs = [row["location_id"] for row in report["locations"]]
    assert locs.count("1") == 1
    row = report["locations"][0]
    assert row["total_purchase_cost"] == 10000
    assert row["total_waste_cost"] == 1000
    assert abs(row["waste_ratio"] - 0.1) < 1e-6
    assert row["currency"] == "COP"


def test_reporting_endpoints(client, auth_header):
    from data.pipelines.pipeline import weekly_location_performance_flow

    week_start = _seed_week_events()
    weekly_location_performance_flow(week_start=week_start, triggered_by="test")

    latest = client.get("/reporting/pipeline-runs/latest", headers=auth_header)
    assert latest.status_code == 200
    body = latest.json()
    assert body["status"] == "completed"
    assert "started_at" in body
    assert "rows_extracted" in body

    kpis = client.get(
        f"/reporting/weekly-location-performance?week_start={week_start.isoformat()}",
        headers=auth_header,
    )
    assert kpis.status_code == 200
    payload = kpis.json()
    assert payload["week_start"] == week_start.isoformat()
    assert len(payload["locations"]) >= 1

    trigger = client.post(
        "/reporting/pipeline-runs",
        headers=auth_header,
        json={"week_start": week_start.isoformat()},
    )
    assert trigger.status_code == 200
    assert trigger.json()["status"] == "completed"
