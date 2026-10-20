"""Esquemas Pydantic API RFP (nunca devolver ORM crudo)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationAxisOut(BaseModel):
    pass_: bool = Field(alias="pass", default=False)
    score: float | None = None
    details: str | None = None
    missing_aspects: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class EvaluationResultOut(BaseModel):
    section_id: str | None = None
    department_id: str
    readability: dict[str, Any] = Field(default_factory=dict)
    relevance: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] = Field(default_factory=dict)
    overall_pass: bool = False
    feedback_for_generator: str = ""


class DepartmentSectionOut(BaseModel):
    department_id: str
    contact_name: str | None = None
    key_aspects: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    draft_content: str | None = None
    evaluation_results: EvaluationResultOut | dict[str, Any] | None = None
    generation_iteration: int = 0
    needs_human_review: bool = False
    section_status: str = "pendiente"
    approval_status: str = "pendiente"
    approver: str | None = None
    approved_at: datetime | None = None
    approval_comment: str | None = None
    approval_iteration: int = 0


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


class FinalDocumentOut(BaseModel):
    ticket_id: int
    title: str
    content: str
    total_estimated_value: str | None = None
    currency: str = "EUR"
    currency_symbol: str = "€"
    sections_included: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None


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
    ceo_approval_status: str | None = None
    ceo_approver: str | None = None
    ceo_comment: str | None = None
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)
    final_document: FinalDocumentOut | None = None


class RfpUploadAccepted(BaseModel):
    ticket_id: int
    status: str = "analizando"
    message: str = "Ticket creado; el análisis corre en segundo plano."


class RfpGenerateAccepted(BaseModel):
    ticket_id: int
    status: str = "generando_borrador"
    message: str = (
        "Generación de borradores encolada; el ticket pasará por "
        "generando_borrador → en_evaluacion → borrador_listo o needs_human_review."
    )


class RfpApprovalStartAccepted(BaseModel):
    ticket_id: int
    status: str = "esperando_aprobacion"
    message: str = (
        "Aprobación humana iniciada; cada departamento puede aprobar en paralelo "
        "sin bloquear a los demás."
    )
    pending: list[dict[str, Any]] = Field(default_factory=list)


class RfpApprovalDecisionIn(BaseModel):
    action: str  # approve | reject | request_changes
    comment: str = ""


class RfpApprovalDecisionOut(BaseModel):
    ticket_id: int
    department_id: str
    approval_status: str
    ticket_status: str
    pending_interrupt: dict[str, Any] | None = None
    final_document: FinalDocumentOut | None = None


class SalesDropAlertIn(BaseModel):
    """Alerta opcional BRIEFING: caída de ventas >15% vs semana anterior."""

    country: str
    drop_pct: float = Field(..., description="Porcentaje de caída (p.ej. 18.5)")
    week_label: str


class SalesDropAlertOut(BaseModel):
    event: str = "sales_drop_alert"
    event_id: int
    country: str
    drop_pct: float
    threshold_pct: float = 15.0
    week_label: str
