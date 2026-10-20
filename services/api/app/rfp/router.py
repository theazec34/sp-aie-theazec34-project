"""Capa HTTP de recepción RFP — solo dispara y consulta el pipeline."""

from __future__ import annotations

import logging
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.rfp import repository as repo
from app.rfp.schemas import (
    FinalDocumentOut,
    RfpApprovalDecisionIn,
    RfpApprovalDecisionOut,
    RfpApprovalStartAccepted,
    RfpGenerateAccepted,
    RfpTicketOut,
    RfpUploadAccepted,
    SalesDropAlertIn,
    SalesDropAlertOut,
)
from app.rfp.sse_hub import (
    publish_rfp_ticket_created,
    publish_sales_drop_alert,
    stream_events,
)
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
    # Notificación en tiempo real (SSE) — estado inicial analizando
    publish_rfp_ticket_created(
        ticket_id=ticket.id,
        status="analizando",
        original_filename=file.filename or "",
        created_at=ticket.created_at.isoformat() if ticket.created_at else None,
    )
    _enqueue(ticket.id)
    logger.info("rfp ticket=%s aceptado path=%s", ticket.id, dest)
    return RfpUploadAccepted(ticket_id=ticket.id, status="analizando")


@router.get("/events/stream")
async def rfp_events_stream(
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    _user: UserInDB = Depends(get_current_user),
) -> StreamingResponse:
    """
    SSE autenticado (mismo JWT que el backoffice).

    Usar fetch + ReadableStream en el cliente (EventSource no envía Authorization).
    """
    parsed_last: int | None = None
    if last_event_id:
        try:
            parsed_last = int(last_event_id)
        except ValueError:
            parsed_last = None

    async def event_generator():
        async for chunk in stream_events(last_event_id=parsed_last):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/events/sales-drop-alert", response_model=SalesDropAlertOut)
def emit_sales_drop_alert(
    body: SalesDropAlertIn,
    _user: UserInDB = Depends(get_current_user),
) -> SalesDropAlertOut:
    """
    Caso opcional: umbral de negocio (caída de ventas >15%).

    Emite `sales_drop_alert` por el mismo canal SSE (Mariana Restrepo / Felipe Guerrero).
    """
    if body.drop_pct < 15.0:
        raise HTTPException(
            status_code=400,
            detail="La alerta solo aplica con caída ≥ 15% vs semana anterior",
        )
    ev = publish_sales_drop_alert(
        country=body.country,
        drop_pct=body.drop_pct,
        week_label=body.week_label,
    )
    return SalesDropAlertOut(
        event_id=ev.id,
        country=body.country,
        drop_pct=body.drop_pct,
        week_label=body.week_label,
    )


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


_PART3_ALLOWED = frozenset({"borrador_listo", "needs_human_review", "esperando_aprobacion"})


@router.post(
    "/tickets/{ticket_id}/approvals/start",
    response_model=RfpApprovalStartAccepted,
    status_code=202,
)
def start_approvals_endpoint(
    ticket_id: int,
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpApprovalStartAccepted:
    """Inicia Parte 3: interrupts HITL por departamento (paralelos)."""
    ticket = repo.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status not in _PART3_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=(
                "La aprobación requiere borrador_listo o needs_human_review "
                f"(estado actual: {ticket.status})."
            ),
        )
    sections = repo.load_sections_for_approval(session, ticket_id)
    if not any(s.get("draft_content") for s in sections):
        raise HTTPException(
            status_code=400,
            detail="No hay borradores de sección para aprobar (ejecuta Parte 2 primero).",
        )
    _ensure_rfp_path()
    from rfp.runner import start_approvals

    try:
        out = start_approvals(ticket_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("fallo start approvals ticket=%s", ticket_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RfpApprovalStartAccepted(
        ticket_id=ticket_id,
        status="esperando_aprobacion",
        pending=list(out.get("pending") or []),
    )


@router.post(
    "/tickets/{ticket_id}/approvals/{department_id}",
    response_model=RfpApprovalDecisionOut,
)
def decide_approval(
    ticket_id: int,
    department_id: str,
    body: RfpApprovalDecisionIn,
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpApprovalDecisionOut:
    """Resume HITL: approve | reject | request_changes (departamento o ceo)."""
    ticket = repo.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status not in {"esperando_aprobacion", "needs_human_review"}:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket no está en aprobación (estado: {ticket.status}).",
        )
    _ensure_rfp_path()
    from rfp.runner import apply_approval_decision

    try:
        out = apply_approval_decision(
            ticket_id,
            department_id,
            action=body.action,
            comment=body.comment or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("fallo approval ticket=%s dept=%s", ticket_id, department_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    final = None
    if out.get("final_document"):
        fd = out["final_document"]
        final = FinalDocumentOut(
            ticket_id=ticket_id,
            title=fd.get("title") or "",
            content=fd.get("content") or "",
            total_estimated_value=fd.get("total_estimated_value"),
            currency="EUR",
            currency_symbol="€",
            sections_included=list(fd.get("sections_included") or []),
        )
    return RfpApprovalDecisionOut(
        ticket_id=ticket_id,
        department_id=department_id,
        approval_status=out.get("approval_status") or "pendiente",
        ticket_status=out.get("ticket_status") or "esperando_aprobacion",
        pending_interrupt=out.get("pending_interrupt"),
        final_document=final,
    )


@router.get(
    "/tickets/{ticket_id}/final-document",
    response_model=FinalDocumentOut,
)
def get_final_document(
    ticket_id: int,
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> FinalDocumentOut:
    ticket = repo.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    detail = repo.ticket_to_out(session, ticket)
    if not detail.final_document:
        raise HTTPException(status_code=404, detail="Documento final aún no disponible")
    return detail.final_document
