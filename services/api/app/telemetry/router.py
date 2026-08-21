"""Telemetry intake stub — validates envelope, logs, no DB write (Phase 3)."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter

from app.telemetry.models import TelemetryBatch, TelemetryReceiveResponse

logger = logging.getLogger("api.telemetry")

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Documented sink URL (frontends use NEXT_PUBLIC_TELEMETRY_ENDPOINT).
TELEMETRY_ENDPOINT = os.getenv(
    "TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events"
).rstrip("/")


@router.get("/config")
def telemetry_config() -> dict[str, str]:
    """Expose configured sink for ops/debug (no secrets)."""
    return {"TELEMETRY_ENDPOINT": TELEMETRY_ENDPOINT}


@router.post("/events", response_model=TelemetryReceiveResponse)
def receive_events(batch: TelemetryBatch) -> TelemetryReceiveResponse:
    types = [event.event_type for event in batch.events]
    logger.info(
        "telemetry stub received=%s types=%s",
        len(batch.events),
        ",".join(types),
    )
    for event_type in types:
        logger.info("telemetry event_type=%s", event_type)
    return TelemetryReceiveResponse(received=len(batch.events))
