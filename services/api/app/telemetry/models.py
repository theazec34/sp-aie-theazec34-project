"""Pydantic models for telemetry intake (envelope unchanged from capture hito)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """Standard event envelope from Phase 1 telemetry plan."""

    eventId: str = Field(min_length=1)
    timestamp: str = Field(min_length=1, description="ISO 8601 capture time")
    sessionId: str | None = None
    userId: str | None = None
    event_type: str = Field(min_length=1)
    schemaVersion: str = Field(min_length=1)
    requestId: str = Field(min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class TelemetryBatchLoose(BaseModel):
    """Loose envelope so one bad event does not 422 the whole batch."""

    events: list[dict[str, Any]] = Field(min_length=1)


class TelemetryReceiveResponse(BaseModel):
    received: int
    stored: int
    rejected: int
