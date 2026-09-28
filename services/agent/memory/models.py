"""Typed models for agent episodic memory (separate from RAG)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    HOURS = "hours"
    SUPPLIER = "supplier"
    INCIDENT_PATTERN = "incident_pattern"
    COMM_PREFERENCE = "comm_preference"
    OTHER_OPERATIONAL = "other_operational"


class DecisionOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    DISCARDED_AMBIGUOUS = "discarded_ambiguous"
    DISCARDED_TOPIC_CHANGE = "discarded_topic_change"
    DISCARDED_POLICY = "discarded_policy"


ConfirmLabel = Literal["approve", "reject", "edit", "ambiguous", "topic_change"]


class MemoryProposal(BaseModel):
    """Structured self-eval output — proposed BEFORE any write."""

    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    fact: str = Field(min_length=1, description="Normalized fact to remember")
    reason: str = Field(min_length=1, description="Why this is memorable")
    location: str | None = None
    category: MemoryCategory = MemoryCategory.OTHER_OPERATIONAL
    language: Literal["es", "en"] = "es"
    source_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SelfEvalResult(BaseModel):
    """Single structured self-evaluation (no second agent)."""

    memorable: bool
    propuesta_memoria: MemoryProposal | None = None
    discard_reason: str | None = None


class MemoryEntry(BaseModel):
    """Persisted approved memory — never written to RAG collections."""

    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    fact: str
    location: str | None = None
    category: MemoryCategory = MemoryCategory.OTHER_OPERATIONAL
    language: Literal["es", "en"] = "es"
    source_message: str = ""
    proposal_id: str | None = None
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    consolidated: bool = False


class AuditRecord(BaseModel):
    """Every proposal + decision is auditable (approved or rejected)."""

    audit_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str
    proposal: MemoryProposal
    outcome: DecisionOutcome
    user_message: str
    confirm_label: ConfirmLabel | None = None
    edited_fact: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PendingProposal(BaseModel):
    """At most one pending proposal per session."""

    session_id: str
    proposal: MemoryProposal
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
