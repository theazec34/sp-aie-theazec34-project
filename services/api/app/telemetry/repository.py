"""Bulk persistence for telemetry_events (single INSERT per batch)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session

from app.telemetry.allowlist import filter_tags
from app.telemetry.models import TelemetryEvent
from app.telemetry.orm import TelemetryEventRow

DEFAULT_SERVICE = "backoffice"


def _parse_timestamp(raw: str) -> datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def event_to_row_mapping(
    event: TelemetryEvent,
    *,
    service: str = DEFAULT_SERVICE,
) -> dict[str, Any]:
    """Map validated TelemetryEvent → table columns (does not include id)."""
    return {
        "event_id": event.eventId,
        "event_type": event.event_type,
        "timestamp": _parse_timestamp(event.timestamp),
        "service": service,
        "session_id": event.sessionId,
        "user_id": event.userId,
        "tags": filter_tags(
            event.event_type,
            event.properties,
            schema_version=event.schemaVersion,
            request_id=event.requestId,
        ),
    }


def bulk_insert_events(
    session: Session,
    events: list[TelemetryEvent],
    *,
    service: str = DEFAULT_SERVICE,
) -> int:
    """Insert all valid events in one statement / one transaction.

    Duplicate `event_id` is ignored (idempotent retries from the FE).
    Returns the number of rows newly inserted. No-op when events is empty.
    """
    if not events:
        return 0
    rows = [event_to_row_mapping(event, service=service) for event in events]
    dialect = session.get_bind().dialect.name
    insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert
    stmt = (
        insert_fn(TelemetryEventRow)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["event_id"])
    )
    result = session.execute(stmt)
    session.commit()
    # rowcount is the number of rows actually inserted (excludes conflicts).
    if result.rowcount is not None and result.rowcount >= 0:
        return int(result.rowcount)
    return len(rows)
