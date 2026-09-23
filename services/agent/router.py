"""Agent HTTP surface — POST /agent/query invokes the compiled LangGraph only."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# services/agent/router.py → repo root + services/ + services/api
_REPO = Path(__file__).resolve().parents[2]
_SERVICES = Path(__file__).resolve().parents[1]
_API = _SERVICES / "api"
for _p in (_REPO, _SERVICES, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.deps import get_current_user  # noqa: E402
from app.users.models import UserInDB  # noqa: E402
from agent.graph import run_agent  # noqa: E402
from agent.tracing import load_trace  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentQueryRequest(BaseModel):
    question: str = Field(..., max_length=2000)


class AgentQueryResponse(BaseModel):
    answer: str
    run_id: str
    nodes: list[str]
    checkpointed: bool = False
    error: str | None = None
    intent: str | None = None
    sources_used: list[str] = []


class AgentTraceResponse(BaseModel):
    run_id: str
    nodes: list[str]
    trace: list[dict]
    answer: str | None = None
    error: str | None = None
    checkpointed: bool | None = None


@router.post("/query", response_model=AgentQueryResponse)
def agent_query(
    body: AgentQueryRequest,
    _user: UserInDB = Depends(get_current_user),
) -> AgentQueryResponse:
    """Invoke the compiled LangGraph agent — no business logic in the endpoint."""
    try:
        result = run_agent(body.question or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — never leak stack traces to clients
        logger.exception("agent graph failed")
        raise HTTPException(
            status_code=503,
            detail="El agente no pudo completar la consulta. Inténtalo de nuevo.",
        ) from exc

    return AgentQueryResponse(
        answer=str(result.get("answer") or ""),
        run_id=str(result.get("run_id") or ""),
        nodes=list(result.get("nodes") or []),
        checkpointed=bool(result.get("checkpointed")),
        error=result.get("error"),
        intent=result.get("intent"),
        sources_used=list(result.get("sources_used") or []),
    )


@router.get("/traces/{run_id}", response_model=AgentTraceResponse)
def agent_trace(
    run_id: str,
    _user: UserInDB = Depends(get_current_user),
) -> AgentTraceResponse:
    """Fetch a persisted run trace (consultable after execution)."""
    record = load_trace(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return AgentTraceResponse(
        run_id=str(record.get("run_id") or run_id),
        nodes=list(record.get("nodes") or []),
        trace=list(record.get("trace") or []),
        answer=record.get("answer"),
        error=record.get("error"),
        checkpointed=record.get("checkpointed"),
    )
