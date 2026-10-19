"""LangGraph state for rfp_intake Part 1."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class RfpIntakeState(TypedDict):
    ticket_id: int
    pdf_path: str
    markdown: str
    markdown_path: str
    classification: dict[str, Any]
    metadata: dict[str, Any]
    departments: list[str]
    worker_results: list[dict[str, Any]]
    synthesizer: dict[str, Any]
    status: str  # analizando | descartado | analisis_completo
    discard_reason: str | None
    error: str | None
    trace: list[dict[str, Any]]
    readability: NotRequired[dict[str, Any]]
