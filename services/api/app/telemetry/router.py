"""Telemetry intake — validate per event, bulk-insert valid rows to telemetry_events."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends
from pydantic import ValidationError
from sqlmodel import Session

from app.database import get_db
from app.telemetry.models import (
    TelemetryBatchLoose,
    TelemetryEvent,
    TelemetryReceiveResponse,
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
