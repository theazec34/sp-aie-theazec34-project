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
