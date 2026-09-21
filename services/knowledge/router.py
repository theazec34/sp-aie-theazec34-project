"""Knowledge-base query API — Phase 3.

POST /knowledge/query → { "answer": "..." } only (no raw Qdrant hits).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
for _p in (_REPO_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.deps import get_current_user  # noqa: E402
from app.users.models import UserInDB  # noqa: E402
from data.pipelines.rag import query as rag_query  # noqa: E402
from data.process.rag import setup as rag_setup  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class KnowledgeQueryResponse(BaseModel):
    answer: str


class ReindexResponse(BaseModel):
    status: str
    collection: str
    chunks_indexed: int


@router.post("/query", response_model=KnowledgeQueryResponse)
def knowledge_query(
    body: KnowledgeQueryRequest,
    _user: UserInDB = Depends(get_current_user),
) -> KnowledgeQueryResponse:
    """Answer a natural-language question from the Brasaland knowledge base."""
    try:
        answer = rag_query(body.question.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("knowledge query failed")
        raise HTTPException(
            status_code=503,
            detail=f"Knowledge service unavailable: {exc}",
        ) from exc
    return KnowledgeQueryResponse(answer=answer)


@router.post("/reindex", response_model=ReindexResponse)
def knowledge_reindex(
    _user: UserInDB = Depends(get_current_user),
) -> ReindexResponse:
    """Re-run setup() (idempotent upsert) — ops helper, not required by UI."""
    try:
        result = rag_setup()
    except Exception as exc:  # noqa: BLE001
        logger.exception("knowledge reindex failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ReindexResponse(
        status="ok",
        collection=str(result["collection"]),
        chunks_indexed=int(result["chunks_indexed"]),
    )
