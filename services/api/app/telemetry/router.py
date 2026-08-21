"""Telemetry intake + technical report endpoint."""

from __future__ import annotations

import logging
import os
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from sqlmodel import Session

from app.cache import TELEMETRY_REPORT_TTL, telemetry_report_cache
from app.database import engine, get_db
from app.telemetry.analysis import build_report, default_period
from app.telemetry.models import (
    TelemetryBatchLoose,
    TelemetryEvent,
    TelemetryReceiveResponse,
    TelemetryReportResponse,
)
from app.telemetry.repository import DEFAULT_SERVICE, bulk_insert_events

logger = logging.getLogger("api.telemetry")

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Documented sink URL (frontends use NEXT_PUBLIC_TELEMETRY_ENDPOINT).
TELEMETRY_ENDPOINT = os.getenv(
    "TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events"
).rstrip("/")

TELEMETRY_SERVICE = os.getenv("TELEMETRY_SERVICE", DEFAULT_SERVICE).strip() or DEFAULT_SERVICE


@router.get("/config")
def telemetry_config() -> dict[str, str]:
    """Expose configured sink for ops/debug (no secrets)."""
    return {
        "TELEMETRY_ENDPOINT": TELEMETRY_ENDPOINT,
        "TELEMETRY_SERVICE": TELEMETRY_SERVICE,
    }


@router.post("/events", response_model=TelemetryReceiveResponse)
def receive_events(
    batch: TelemetryBatchLoose,
    db: Session = Depends(get_db),
) -> TelemetryReceiveResponse:
    """Accept {events: [...]} with per-event validation and one bulk INSERT."""
    received = len(batch.events)
    valid: list[TelemetryEvent] = []
    rejected = 0

    for raw in batch.events:
        try:
            event = TelemetryEvent.model_validate(raw)
        except ValidationError as exc:
            rejected += 1
            logger.info(
                "telemetry event rejected validation=%s",
                exc.error_count(),
            )
            continue
        valid.append(event)
        logger.info("telemetry event_type=%s", event.event_type)

    stored = bulk_insert_events(db, valid, service=TELEMETRY_SERVICE)
    if stored:
        telemetry_report_cache.clear()
    logger.info(
        "telemetry batch received=%s stored=%s rejected=%s",
        received,
        stored,
        rejected,
    )
    return TelemetryReceiveResponse(
        received=received,
        stored=stored,
        rejected=rejected,
    )


@router.get("/report", response_model=TelemetryReportResponse)
def telemetry_report(
    start_date: date | None = Query(
        default=None,
        description="Inclusive start (YYYY-MM-DD, UTC). Default: end − 6 days.",
    ),
    end_date: date | None = Query(
        default=None,
        description="Inclusive end (YYYY-MM-DD, UTC). Default: today UTC.",
    ),
) -> dict:
    """Serve cached operational metrics (pipeline runs outside the hot path)."""
    start_dt, end_dt, period_from, period_to = default_period(start_date, end_date)
    cache_key = f"telemetry:report:{period_from.isoformat()}:{period_to.isoformat()}"
    cached = telemetry_report_cache.get(cache_key)
    if cached is not None:
        return cached

    report = build_report(
        engine,
        start_dt,
        end_dt,
        period_from=period_from,
        period_to=period_to,
    )
    telemetry_report_cache.set(cache_key, report, TELEMETRY_REPORT_TTL)
    return report
