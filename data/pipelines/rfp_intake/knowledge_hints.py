"""Recuperación opcional de la base de conocimiento (RAG) para tono/políticas."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("rfp.knowledge_hints")


def fetch_knowledge_snippets(query: str, *, limit: int = 3) -> list[str]:
    """Best-effort: si Qdrant/RAG no está disponible, devuelve []."""
    q = (query or "").strip()
    if not q:
        return []
    try:
        from data.pipelines.rag import retrieve

        hits = retrieve(q, top_k=limit) or []
        out: list[str] = []
        for h in hits:
            if isinstance(h, dict):
                text = h.get("text") or h.get("page_content") or h.get("content") or ""
            else:
                text = str(h)
            text = text.strip()
            if text:
                out.append(text[:400])
        return out
    except Exception as exc:  # noqa: BLE001
        logger.info("RAG opcional no disponible para RFP: %s", exc)
        return []


def knowledge_query_for_department(department_id: str, metadata: dict[str, Any]) -> str:
    client = metadata.get("client_name") or ""
    service = metadata.get("service_type") or ""
    return f"Brasaland políticas {department_id} {service} {client} pilares marca"
