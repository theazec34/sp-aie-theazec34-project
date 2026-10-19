"""Pydantic API schemas for RFP intake (never return raw ORM blindly)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DepartmentSectionOut(BaseModel):
    department_id: str
    contact_name: str | None = None
    key_aspects: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    approval_status: str = "pendiente"


class RfpMetadataOut(BaseModel):
    client_name: str | None = None
    location: str | None = None
    service_type: str | None = None
    scope: str | None = None
    deadline: str | None = None
    budget_range: str | None = None
    departments_needed: list[str] = Field(default_factory=list)
    flesch_kincaid: float | None = None
    gunning_fog: float | None = None
    word_count: int | None = None
    is_rfp: bool = False
    classifier_confidence: float | None = None
    classifier_notes: str | None = None
    open_questions: list[str] = Field(default_factory=list)


class RfpTicketOut(BaseModel):
    ticket_id: int
    status: str
    original_filename: str
    raw_pdf_path: str
    markdown_path: str | None = None
    discard_reason: str | None = None
    handoff_ready: bool = False
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: RfpMetadataOut | None = None
    department_sections: list[DepartmentSectionOut] = Field(default_factory=list)
    synthesizer_summary: dict[str, Any] | None = None


class RfpUploadAccepted(BaseModel):
    ticket_id: int
    status: str = "analizando"
    message: str = "Ticket creado; el pipeline corre en segundo plano."
