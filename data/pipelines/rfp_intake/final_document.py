"""Síntesis del documento final tras sign-off de todos los departamentos (+ CEO si aplica)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS
from data.pipelines.rfp_intake.guidelines import BRAND_PILLARS


def synthesize_final_document(
    *,
    ticket_id: int,
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    ceo_approval: dict[str, Any] | None = None,
    arbitration_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    client = metadata.get("client_name") or "Cliente"
    location = metadata.get("location") or "—"
    service = metadata.get("service_type") or "—"
    budget = metadata.get("budget_range") or "por confirmar en €"
    deadline = metadata.get("deadline") or "—"
    pillars = ", ".join(BRAND_PILLARS)
    now = datetime.now(timezone.utc).isoformat()

    parts: list[str] = [
        "# Propuesta económica Brasaland — documento final",
        f"Ticket: {ticket_id}",
        f"Cliente: {client}",
        f"Ubicación: {location}",
        f"Servicio: {service}",
        f"Presupuesto de referencia: {budget} (euros €)",
        f"Fecha límite RFP: {deadline}",
        f"Generado: {now}",
        f"Pilares de marca: {pillars}",
        "Validez de la oferta: 30 días desde la emisión de este documento.",
        "",
    ]

    total_hint = budget
    for sec in sections:
        dept = sec.get("department_id") or ""
        info = DEPARTMENTS.get(dept, {})
        parts.append(f"## {info.get('name', dept)}")
        parts.append(f"Responsable / aprobador: {sec.get('approver') or info.get('owner')}")
        parts.append(f"Estado de aprobación: {sec.get('approval_status') or 'aprobado'}")
        parts.append("")
        parts.append(sec.get("draft_content") or "(sin contenido)")
        parts.append("")

    if ceo_approval:
        parts.append("## Aprobación CEO")
        parts.append(
            f"Mariana Restrepo: {ceo_approval.get('action', 'approve')} "
            f"({ceo_approval.get('approved_at') or now})"
        )
        if ceo_approval.get("comment"):
            parts.append(f"Comentario: {ceo_approval['comment']}")
        parts.append("")

    if arbitration_log:
        parts.append("## Registro de arbitraje")
        for row in arbitration_log:
            parts.append(
                f"- {row.get('trigger_id')}: árbitro {row.get('arbiter')} → {row.get('action')}"
            )
        parts.append("")

    parts.append("---")
    parts.append(
        "Documento consolidado automáticamente tras el sign-off de todos los departamentos "
        "activos. Montaje/entrega nunca inferior a 10 días hábiles."
    )

    body = "\n".join(parts)
    return {
        "ticket_id": ticket_id,
        "title": f"Propuesta Brasaland — {client}",
        "content": body,
        "total_estimated_value": total_hint,
        "currency": "EUR",
        "currency_symbol": "€",
        "sections_included": [s.get("department_id") for s in sections],
        "generated_at": now,
        "ceo_required": bool(ceo_approval is not None or _needs_ceo(metadata)),
        "ceo_approved": bool(ceo_approval and ceo_approval.get("action") == "approve"),
    }


def _needs_ceo(metadata: dict[str, Any]) -> bool:
    from data.pipelines.rfp_intake.arbitration import _annual_over_threshold

    return _annual_over_threshold(str(metadata.get("budget_range") or ""), [])
