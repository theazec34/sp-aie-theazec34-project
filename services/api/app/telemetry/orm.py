"""SQLModel table for append-only telemetry_events (Supabase / SQLite).

Eight columns. No update/delete helpers — facts are immutable.
Postgres indexes (incl. GIN on tags) live in sql/telemetry_events.sql.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Index, Text
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class TelemetryEventRow(SQLModel, table=True):
    """Row mapping for telemetry_events (8 columns)."""

    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("ix_telemetry_events_timestamp", "timestamp"),
        Index("ix_telemetry_events_event_type", "event_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(sa_column=Column("event_id", Text, nullable=False, unique=True))
    event_type: str = Field(index=False)
    timestamp: datetime = Field(
        sa_column=Column("timestamp", DateTime(timezone=True), nullable=False),
    )
    service: str = Field(sa_column=Column("service", Text, nullable=False))
    session_id: Optional[str] = Field(
        default=None,
        sa_column=Column("session_id", Text, nullable=True),
    )
    user_id: Optional[str] = Field(
        default=None,
        sa_column=Column("user_id", Text, nullable=True),
    )
    tags: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("tags", JSON, nullable=False),
    )
