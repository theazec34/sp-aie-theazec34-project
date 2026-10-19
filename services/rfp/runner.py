"""Background runner: pipeline → PostgreSQL persistence (ticket is source of truth)."""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SERVICES = _REPO / "services"
_API = _SERVICES / "api"
for _p in (_REPO, _SERVICES, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

logger = logging.getLogger("rfp.runner")


def process_ticket(ticket_id: int) -> None:
    """
    Ejecuta el grafo rfp_intake y persiste resultados.

    Si el job falla a mitad, el ticket pasa a `fallido` con mensaje legible
    (nunca descarte silencioso). Fuente de verdad = fila rfp_ticket.
    """
    from sqlmodel import Session

    from app.database import engine
    from app.rfp import repository as repo
    from data.pipelines.rfp_intake.graph import run_rfp_intake

    with Session(engine) as session:
        ticket = repo.get_ticket(session, ticket_id)
        if ticket is None:
            logger.error("ticket %s no encontrado", ticket_id)
            return
        pdf_path = ticket.raw_pdf_path

    try:
        result = run_rfp_intake(ticket_id=ticket_id, pdf_path=pdf_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("fallo pipeline rfp ticket=%s", ticket_id)
        with Session(engine) as session:
            repo.update_ticket_status(
                session,
                ticket_id,
                "fallido",
                error_message=(
                    f"Error en el análisis ({type(exc).__name__}): {exc}. "
                    "Revisa logs del servidor; puedes volver a subir el PDF."
                ),
            )
        # Detalle técnico solo en logs, no en la UI
        logger.debug("traceback ticket=%s\n%s", ticket_id, traceback.format_exc()[-1200:])
        return

    status = result.get("status") or "analizando"
    with Session(engine) as session:
        repo.update_ticket_status(
            session,
            ticket_id,
            status,
            discard_reason=result.get("discard_reason"),
            markdown_path=result.get("markdown_path"),
            error_message=None,
            handoff_ready=status == "analisis_completo",
            synthesizer_payload=result.get("synthesizer") or {},
        )
        meta = result.get("metadata") or {}
        repo.upsert_metadata(session, ticket_id, meta)
        if status == "analisis_completo":
            repo.replace_department_sections(
                session, ticket_id, list(result.get("worker_results") or [])
            )
    logger.info("ticket %s -> %s", ticket_id, status)


def process_generation(ticket_id: int) -> None:
    """
    Parte 2: consume handoff Parte 1 y corre generador↔evaluador.

    Estados: generando_borrador → en_evaluacion → borrador_listo | needs_human_review.
    No re-parsea el PDF.
    """
    from sqlmodel import Session

    from app.database import engine
    from app.rfp import repository as repo
    from data.pipelines.rfp_intake.generation_graph import run_response_generation

    with Session(engine) as session:
        handoff = repo.load_part1_handoff(session, ticket_id)
        if handoff is None:
            logger.error("ticket %s no encontrado (generación)", ticket_id)
            return
        if handoff["status"] not in {
            "analisis_completo",
            "generando_borrador",
            "en_evaluacion",
            "borrador_listo",
            "needs_human_review",
        }:
            repo.update_ticket_status(
                session,
                ticket_id,
                handoff["status"],
                error_message=(
                    "La generación requiere un ticket en analisis_completo "
                    f"(estado actual: {handoff['status']})."
                ),
            )
            return
        if not handoff["sections"]:
            repo.update_ticket_status(
                session,
                ticket_id,
                "fallido",
                error_message="Sin secciones de departamento en el handoff de Parte 1.",
            )
            return
        repo.update_ticket_status(session, ticket_id, "generando_borrador", error_message=None)
        metadata = handoff["metadata"]
        sections = handoff["sections"]

    try:
        # Marca en_evaluacion justo antes del ciclo (las secciones corren en paralelo)
        with Session(engine) as session:
            repo.update_ticket_status(session, ticket_id, "en_evaluacion")
        result = run_response_generation(
            ticket_id=ticket_id,
            metadata=metadata,
            sections=sections,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("fallo generación RFP ticket=%s", ticket_id)
        with Session(engine) as session:
            repo.update_ticket_status(
                session,
                ticket_id,
                "fallido",
                error_message=(
                    f"Error en la generación ({type(exc).__name__}): {exc}. "
                    "Puedes reintentar desde analisis_completo."
                ),
            )
        logger.debug("traceback gen ticket=%s\n%s", ticket_id, traceback.format_exc()[-1200:])
        return

    status = result.get("status") or "needs_human_review"
    with Session(engine) as session:
        repo.apply_section_generation_results(
            session, ticket_id, list(result.get("sections") or [])
        )
        # Amplía synthesizer con handoff Parte 3 sin borrar Parte 1
        ticket = repo.get_ticket(session, ticket_id)
        synth: dict = {}
        if ticket and ticket.synthesizer_payload_json:
            try:
                import json

                synth = json.loads(ticket.synthesizer_payload_json)
            except Exception:  # noqa: BLE001
                synth = {}
        synth["part2"] = result.get("part3_handoff") or {}
        synth["part2_status"] = status
        repo.update_ticket_status(
            session,
            ticket_id,
            status,
            error_message=None,
            handoff_ready=True,
            synthesizer_payload=synth,
        )
    logger.info("ticket %s generación -> %s", ticket_id, status)


def start_approvals(ticket_id: int) -> dict:
    """
    Parte 3: arranca interrupt HITL por departamento (threads independientes).
    Estado ticket → esperando_aprobacion.
    """
    from sqlmodel import Session

    from app.database import engine
    from app.rfp import repository as repo
    from data.pipelines.rfp_intake.approval_graph import start_department_approval
    from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS

    with Session(engine) as session:
        ticket = repo.get_ticket(session, ticket_id)
        if ticket is None:
            raise ValueError(f"ticket {ticket_id} no encontrado")
        sections = repo.load_sections_for_approval(session, ticket_id)
        if not sections:
            raise ValueError("Sin secciones para aprobar")
        repo.update_ticket_status(
            session, ticket_id, "esperando_aprobacion", error_message=None
        )

    pending = []
    traces = []
    for sec in sections:
        if not sec.get("draft_content"):
            continue
        info = DEPARTMENTS.get(sec["department_id"], {})
        out = start_department_approval(
            ticket_id=ticket_id,
            department_id=sec["department_id"],
            draft_content=sec["draft_content"],
            key_aspects=sec.get("key_aspects") or [],
            approver_name=sec.get("contact_name") or info.get("owner"),
        )
        traces.append(out)
        if out.get("status") == "interrupted":
            pending.append(
                {
                    "department_id": sec["department_id"],
                    "thread_id": out.get("thread_id"),
                    "approver": info.get("owner"),
                    "interrupt": out.get("pending_interrupt"),
                }
            )

    with Session(engine) as session:
        repo.set_approval_trace(
            session,
            ticket_id,
            {"pending": pending, "events": traces, "started": True},
        )
    return {"ticket_id": ticket_id, "status": "esperando_aprobacion", "pending": pending}


def apply_approval_decision(
    ticket_id: int,
    department_id: str,
    *,
    action: str,
    comment: str = "",
) -> dict:
    """Resume HITL de un departamento (o CEO) y reevalúa síntesis."""
    from sqlmodel import Session

    from app.database import engine
    from app.rfp import repository as repo
    from data.pipelines.rfp_intake.approval_graph import (
        resume_department_approval,
        run_arbitration_and_maybe_finalize,
        thread_id_for,
    )
    from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS

    if action not in {"approve", "reject", "request_changes"}:
        raise ValueError("action debe ser approve | reject | request_changes")

    with Session(engine) as session:
        ticket = repo.get_ticket(session, ticket_id)
        if ticket is None:
            raise ValueError("ticket no encontrado")
        handoff = repo.load_part1_handoff(session, ticket_id)
        metadata = (handoff or {}).get("metadata") or {}

    if department_id == "ceo":
        with Session(engine) as session:
            repo.save_ceo_approval(
                session, ticket_id, action=action, comment=comment
            )
        result = {"department_id": "ceo", "approval_status": (
            "aprobado" if action == "approve" else "rechazado"
        ), "status": "completed", "trace": []}
    else:
        result = resume_department_approval(
            ticket_id=ticket_id,
            department_id=department_id,
            action=action,  # type: ignore[arg-type]
            comment=comment,
        )
        # Si sigue interrupted (p.ej. tras reject→again), actualizar pending
        if result.get("status") == "completed":
            with Session(engine) as session:
                info = DEPARTMENTS.get(department_id, {})
                repo.update_section_approval(
                    session,
                    ticket_id,
                    department_id,
                    approval_status=result.get("approval_status") or "pendiente",
                    approver=result.get("approver_name") or info.get("owner"),
                    comment=result.get("comment") or comment,
                    iteration=int(result.get("iteration") or 0),
                )

    # Actualizar pending + arbitraje / documento final
    with Session(engine) as session:
        sections = repo.load_sections_for_approval(session, ticket_id)
        ticket = repo.get_ticket(session, ticket_id)
        ceo_approval = None
        if ticket and ticket.ceo_approval_status:
            ceo_approval = {
                "action": (
                    "approve"
                    if ticket.ceo_approval_status == "aprobado"
                    else "reject"
                ),
                "comment": ticket.ceo_comment or "",
                "approved_at": (
                    ticket.ceo_approved_at.isoformat()
                    if ticket.ceo_approved_at
                    else None
                ),
            }
        final_pack = run_arbitration_and_maybe_finalize(
            ticket_id=ticket_id,
            metadata=metadata,
            sections=sections,
            ceo_approval=ceo_approval,
        )

        # Rebuild pending from sections still pendiente + open interrupts
        pending = []
        for sec in sections:
            if sec.get("approval_status") in {"aprobado"}:
                continue
            pending.append(
                {
                    "department_id": sec["department_id"],
                    "thread_id": thread_id_for(ticket_id, sec["department_id"]),
                    "approver": sec.get("contact_name"),
                    "approval_status": sec.get("approval_status"),
                }
            )
        if final_pack.get("needs_ceo") and (
            not ceo_approval or ceo_approval.get("action") != "approve"
        ):
            pending.append(
                {
                    "department_id": "ceo",
                    "thread_id": thread_id_for(ticket_id, "ceo"),
                    "approver": "Mariana Restrepo",
                    "approval_status": ticket.ceo_approval_status if ticket else None,
                }
            )

        # Si reject/request_changes y completed needs_human_review — ok
        # Si result interrupted after resume (again path), re-list interrupt
        if result.get("status") == "interrupted":
            pending = [
                p
                for p in pending
                if p["department_id"] != department_id
            ] + [
                {
                    "department_id": department_id,
                    "thread_id": result.get("thread_id"),
                    "approver": DEPARTMENTS.get(department_id, {}).get("owner"),
                    "interrupt": result.get("pending_interrupt"),
                }
            ]

        repo.set_approval_trace(
            session,
            ticket_id,
            {
                "pending": pending,
                "last_decision": result,
                "arbitration": final_pack.get("arbitration"),
            },
        )

        if final_pack.get("final_document"):
            repo.upsert_final_document(session, ticket_id, final_pack["final_document"])
            repo.update_ticket_status(session, ticket_id, "terminado", error_message=None)
            ticket_status = "terminado"
        else:
            repo.update_ticket_status(
                session, ticket_id, "esperando_aprobacion", error_message=None
            )
            ticket_status = "esperando_aprobacion"

        final_out = None
        if final_pack.get("final_document"):
            fd = final_pack["final_document"]
            final_out = {
                "ticket_id": ticket_id,
                "title": fd.get("title"),
                "content": fd.get("content"),
                "total_estimated_value": fd.get("total_estimated_value"),
                "currency": "EUR",
                "currency_symbol": "€",
                "sections_included": fd.get("sections_included") or [],
                "generated_at": fd.get("generated_at"),
            }

    return {
        "ticket_id": ticket_id,
        "department_id": department_id,
        "approval_status": result.get("approval_status") or "pendiente",
        "ticket_status": ticket_status,
        "pending_interrupt": result.get("pending_interrupt"),
        "final_document": final_out,
        "arbitration": final_pack.get("arbitration"),
    }
