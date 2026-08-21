"""Telemetry report endpoint + analysis pipeline tests."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Session

from app.cache import telemetry_report_cache
from app.database import engine, init_db
from app.telemetry.analysis import (
    auth_failure_rate,
    events_per_day,
)
from seed_telemetry import build_seed_events
from app.telemetry.repository import bulk_insert_events


def _seed(client) -> None:
    init_db()
    telemetry_report_cache.clear()
    events = build_seed_events(
        now=datetime(2026, 8, 21, 15, 0, 0, tzinfo=timezone.utc)
    )
    with Session(engine) as session:
        bulk_insert_events(session, events)
    # touch client so app is loaded
    assert client.get("/health").status_code == 200


def test_report_default_period_and_metrics(client):
    _seed(client)
    response = client.get(
        "/telemetry/report",
        params={"start_date": "2026-08-15", "end_date": "2026-08-21"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["period"] == {"from": "2026-08-15", "to": "2026-08-21"}
    metrics = body["metrics"]
    assert "events_per_day" in metrics
    assert "error_rate_by_type" in metrics
    assert "auth_failure_rate" in metrics
    assert "latency_by_route" in metrics
    assert len(metrics["events_per_day"]) >= 1
    assert sum(row["count"] for row in metrics["events_per_day"]) >= 20


def test_report_cache_hits_same_window(client):
    _seed(client)
    params = {"start_date": "2026-08-15", "end_date": "2026-08-21"}
    first = client.get("/telemetry/report", params=params)
    assert first.status_code == 200
    misses_before = telemetry_report_cache.stats()["misses"]
    hits_before = telemetry_report_cache.stats()["hits"]
    second = client.get("/telemetry/report", params=params)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert telemetry_report_cache.stats()["hits"] == hits_before + 1
    assert telemetry_report_cache.stats()["misses"] == misses_before


def test_analysis_functions_no_empty_crash(client):
    init_db()
    telemetry_report_cache.clear()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 8, tzinfo=timezone.utc)
    assert events_per_day(engine, start, end) == []
    assert auth_failure_rate(engine, start, end) == []
    # endpoint still returns structure
    response = client.get(
        "/telemetry/report",
        params={"start_date": "2026-01-01", "end_date": "2026-01-07"},
    )
    assert response.status_code == 200
    assert response.json()["period"]["from"] == "2026-01-01"
