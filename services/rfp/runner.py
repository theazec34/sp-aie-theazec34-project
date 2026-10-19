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
