"""Knowledge-base query API — Phase 3.

POST /knowledge/query → { "answer": "..." } only (no raw Qdrant hits).
POST /knowledge/reindex → starts background job (no HTTP 504 on long embeds).
GET  /knowledge/reindex/status → poll job.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
for _p in (_REPO_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.deps import get_current_user  # noqa: E402
from app.rate_limit import (  # noqa: E402
    client_key,
    enforce_rate_limit,
    knowledge_query_limiter,
)
from app.users.models import UserInDB  # noqa: E402
from data.pipelines.rag import query as rag_query  # noqa: E402
from data.process.rag import setup as rag_setup  # noqa: E402
from knowledge.reindex_job import get_status, start_reindex  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class KnowledgeQueryResponse(BaseModel):
    answer: str


class ReindexResponse(BaseModel):
    status: str
    collection: str = "brasaland_knowledge"
    chunks_indexed: int = 0
    message: str = ""
    error: str | None = None


def _collection_is_empty() -> bool:
    """True if Qdrant has no points (first boot / volume wiped)."""
    try:
        from data.process.rag import collection_name, get_qdrant_client

        client = get_qdrant_client()
        name = collection_name()
        names = {c.name for c in client.get_collections().collections}
        if name not in names:
            return True
        info = client.get_collection(name)
        points = getattr(info, "points_count", 0) or 0
        return int(points) == 0
    except Exception:  # noqa: BLE001
        return True


@router.post("/query", response_model=KnowledgeQueryResponse)
def knowledge_query(
    body: KnowledgeQueryRequest,
    request: Request,
    user: UserInDB = Depends(get_current_user),
) -> KnowledgeQueryResponse:
    """Answer a natural-language question from the Brasaland knowledge base."""
    uid = getattr(user, "id", None) or getattr(user, "email", None)
    enforce_rate_limit(
        knowledge_query_limiter,
        client_key(request, uid),
        detail=(
            "Límite de consultas a BrasAI alcanzado. "
            "Espera un minuto antes de reintentar."
        ),
    )
    try:
        job = get_status()
        if job.get("status") == "running":
            raise HTTPException(
                status_code=503,
                detail=(
                    "BrasAI está reindexando manuales ahora mismo. "
                    "Espera unos segundos y vuelve a preguntar."
                ),
            )
        if _collection_is_empty():
            logger.info("BrasAI: colección vacía — indexando corpus…")
            rag_setup()
        answer = rag_query(body.question.strip())
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — never leak stack traces to clients
        logger.exception("knowledge query failed")
        raise HTTPException(
            status_code=503,
            detail=(
                f"BrasAI no disponible: {exc}. "
                "Prueba POST /knowledge/reindex o revisa GENERATION_* / Qdrant."
            ),
        ) from exc
    return KnowledgeQueryResponse(answer=answer)


@router.post("/reindex", response_model=ReindexResponse)
def knowledge_reindex(
    _user: UserInDB = Depends(get_current_user),
) -> ReindexResponse:
    """Start background reindex — returns immediately (poll /reindex/status)."""
    job = start_reindex(recreate=True)
    status = str(job.get("status") or "started")
    if status == "running":
        return ReindexResponse(
            status="running",
            message=(
                "Reindexación en curso en segundo plano. "
                "No hace falta volver a pulsar; consulta el estado o espera ~1–3 min."
            ),
        )
    return ReindexResponse(
        status=status,
        message="Reindexación iniciada en segundo plano.",
    )


@router.get("/reindex/status", response_model=ReindexResponse)
def knowledge_reindex_status(
    _user: UserInDB = Depends(get_current_user),
) -> ReindexResponse:
    """Poll background reindex job."""
    job = get_status()
    status = str(job.get("status") or "idle")
    result = job.get("result") or {}
    if status == "done":
        return ReindexResponse(
            status="done",
            collection=str(result.get("collection") or "brasaland_knowledge"),
            chunks_indexed=int(result.get("chunks_indexed") or 0),
            message="Manuales indexados. Ya puedes preguntar a BrasAI.",
        )
    if status == "error":
        return ReindexResponse(
            status="error",
            error=str(job.get("error") or "reindex_failed"),
            message="Falló la reindexación. Revisa logs del backend o prueba por CLI.",
        )
    if status == "running":
        return ReindexResponse(
            status="running",
            message="Indexando… (embeddings + Qdrant). Puede tardar 1–3 min.",
        )
    return ReindexResponse(
        status="idle",
        message="No hay reindexación en curso.",
    )
