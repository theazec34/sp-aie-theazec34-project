"""SQLModel tables for RFP intake tickets (PostgreSQL / SQLite via database.py).

TinyDB is NOT used — tickets, metadata and key_aspects live here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RfpTicket(SQLModel, table=True):
    __tablename__ = "rfp_ticket"

    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="analizando", index=True)
    # Parte 1: analizando | descartado | analisis_completo | fallido
    # Parte 2: generando_borrador | en_evaluacion | borrador_listo | needs_human_review
    # Parte 3: esperando_aprobacion | terminado
    raw_pdf_path: str
    original_filename: str = ""
    markdown_path: str | None = None
    discard_reason: str | None = None
    # Part 2 handoff contract
    handoff_ready: bool = Field(default=False)
    synthesizer_payload_json: str | None = Field(default=None, sa_column=Column(Text))
    error_message: str | None = None
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class RfpMetadata(SQLModel, table=True):
    __tablename__ = "rfp_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="rfp_ticket.id", index=True, unique=True)
    client_name: str | None = None
    location: str | None = None
    service_type: str | None = None
    scope: str | None = None
    deadline: str | None = None
    budget_range: str | None = None
    departments_needed_json: str = Field(default="[]", sa_column=Column(Text))
    flesch_kincaid: float | None = None
    gunning_fog: float | None = None
    word_count: int | None = None
    is_rfp: bool = False
    classifier_confidence: float | None = None
    classifier_notes: str | None = None
    open_questions_json: str = Field(default="[]", sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class DepartmentSection(SQLModel, table=True):
    __tablename__ = "rfp_department_section"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="rfp_ticket.id", index=True)
    department_id: str = Field(index=True)
    # marketing | operaciones | procurement | training
    key_aspects_json: str = Field(default="[]", sa_column=Column(Text))
    open_questions_json: str = Field(default="[]", sa_column=Column(Text))
    contact_name: str | None = None
    # Parte 2: borrador + EvaluationResult estructurado
    draft_content: str | None = Field(default=None, sa_column=Column(Text))
    evaluation_results_json: str | None = Field(default=None, sa_column=Column(Text))
    generation_iteration: int = Field(default=0)
    needs_human_review: bool = Field(default=False)
    section_status: str = Field(default="pendiente")
    # pendiente | generando | en_evaluacion | aprobado_auto | needs_human_review
    # Parte 3 placeholders
    approval_status: str = Field(default="pendiente")
    approver: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
