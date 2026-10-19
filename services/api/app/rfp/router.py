"""HTTP surface for RFP intake — routers only trigger/query the pipeline."""

from __future__ import annotations

import logging
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.rfp import repository as repo
from app.rfp.schemas import RfpTicketOut, RfpUploadAccepted
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


def _safe_name(name: str) -> str:
    base = Path(name or "upload.pdf").name
    return re.sub(r"[^\w.\-]+", "_", base)[:120]


def _enqueue(ticket_id: int) -> None:
    """Background job — FastAPI BackgroundTasks + thread pool (ticket SoT)."""
    _SERVICES = Path(__file__).resolve().parents[3]
    if str(_SERVICES) not in sys.path:
        sys.path.insert(0, str(_SERVICES.parent))
        sys.path.insert(0, str(_SERVICES))
    from rfp.runner import process_ticket

    _POOL.submit(process_ticket, ticket_id)


@router.post("/tickets", response_model=RfpUploadAccepted, status_code=202)
async def upload_rfp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    _user: UserInDB = Depends(get_current_user),
) -> RfpUploadAccepted:
    """Accept PDF, persist ticket as `analizando`, return 202; pipeline async."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".md", ".txt"}:
        raise HTTPException(status_code=400, detail="Only PDF (or md fixtures) accepted")

    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = uuid.uuid4().hex[:12]
    safe = _safe_name(file.filename)
    dest = _RAW_DIR / f"rfp_{upload_id}_{safe}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")
    dest.write_bytes(content)

    ticket = repo.create_ticket(
        session,
        raw_pdf_path=str(dest),
        original_filename=file.filename,
    )
    assert ticket.id is not None
    # Fast response: schedule background pipeline (does not run synchronously)
    background_tasks.add_task(_enqueue, ticket.id)
    logger.info("rfp ticket=%s accepted path=%s", ticket.id, dest)
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
        raise HTTPException(status_code=404, detail="Ticket not found")
    return repo.ticket_to_out(session, ticket)
