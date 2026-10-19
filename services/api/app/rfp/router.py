"""Capa HTTP de recepción RFP — solo dispara y consulta el pipeline."""

from __future__ import annotations

import logging
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.rfp import repository as repo
from app.rfp.schemas import RfpGenerateAccepted, RfpTicketOut, RfpUploadAccepted
from app.users.models import UserInDB

logger = logging.getLogger("api.rfp")

router = APIRouter(
    prefix="/rfp",
    tags=["rfp-intake"],
    dependencies=[Depends(get_current_user)],
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_RAW_DIR = _REPO_ROOT / "data" / "raw"
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rfp-intake")

_PART2_ALLOWED = frozenset(
    {
        "analisis_completo",
        "borrador_listo",
        "needs_human_review",
    }
)


def _safe_name(name: str) -> str:
    base = Path(name or "upload.pdf").name
    return re.sub(r"[^\w.\-]+", "_", base)[:120]


def _ensure_rfp_path() -> None:
    _SERVICES = Path(__file__).resolve().parents[3]
    if str(_SERVICES) not in sys.path:
        sys.path.insert(0, str(_SERVICES.parent))
        sys.path.insert(0, str(_SERVICES))


def _enqueue(ticket_id: int) -> None:
    """Encola el pipeline Parte 1 (respuesta HTTP ya enviada)."""
    _ensure_rfp_path()
    from rfp.runner import process_ticket

    _POOL.submit(process_ticket, ticket_id)


def _enqueue_generation(ticket_id: int) -> None:
    """Encola generación Parte 2."""
    _ensure_rfp_path()
    from rfp.runner import process_generation

    _POOL.submit(process_generation, ticket_id)


@router.post("/tickets", response_model=RfpUploadAccepted, status_code=202)
async def upload_rfp(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpUploadAccepted:
    """Acepta PDF, crea ticket `analizando`, responde 202; el pipeline corre async."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Se requiere un nombre de archivo")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".md", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan PDF (o fixtures .md/.txt para pruebas)",
        )

    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = uuid.uuid4().hex[:12]
    safe = _safe_name(file.filename)
    dest = _RAW_DIR / f"rfp_{upload_id}_{safe}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    dest.write_bytes(content)

    ticket = repo.create_ticket(
        session,
        raw_pdf_path=str(dest),
        original_filename=file.filename,
    )
    assert ticket.id is not None
    _enqueue(ticket.id)
    logger.info("rfp ticket=%s aceptado path=%s", ticket.id, dest)
    return RfpUploadAccepted(ticket_id=ticket.id, status="analizando")


@router.get("/tickets", response_model=list[RfpTicketOut])
def list_rfp_tickets(
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> list[RfpTicketOut]:
    tickets = repo.list_tickets(session)
    return [repo.ticket_to_out(session, t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=RfpTicketOut)
def get_rfp_ticket(
    ticket_id: int,
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpTicketOut:
    ticket = repo.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return repo.ticket_to_out(session, ticket)


@router.post(
    "/tickets/{ticket_id}/generate",
    response_model=RfpGenerateAccepted,
    status_code=202,
)
def start_response_generation(
    ticket_id: int,
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpGenerateAccepted:
    """
    Dispara Parte 2: generadores + evaluadores desde el handoff de Parte 1.
    No re-parsea el PDF. Responde 202 y actualiza el ticket en segundo plano.
    """
    ticket = repo.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status in {"generando_borrador", "en_evaluacion"}:
        raise HTTPException(
            status_code=409,
            detail="El ticket ya está generando o evaluando borradores.",
        )
    if ticket.status not in _PART2_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Solo se puede generar desde analisis_completo "
                f"(o reintentar desde borrador_listo / needs_human_review). "
                f"Estado actual: {ticket.status}."
            ),
        )
    if not ticket.handoff_ready and ticket.status == "analisis_completo":
        # Parte 1 debería haber marcado handoff_ready; permitimos si hay secciones
        pass
    handoff = repo.load_part1_handoff(session, ticket_id)
    if not handoff or not handoff.get("sections"):
        raise HTTPException(
            status_code=400,
            detail="No hay secciones de departamento en el handoff de Parte 1.",
        )
    repo.update_ticket_status(session, ticket_id, "generando_borrador", error_message=None)
    _enqueue_generation(ticket_id)
    logger.info("rfp ticket=%s generación encolada", ticket_id)
    return RfpGenerateAccepted(ticket_id=ticket_id, status="generando_borrador")
