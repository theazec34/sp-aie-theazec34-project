"""LangGraph nodes — single responsibility each; reuse RAG pipeline helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from data.pipelines.rag import (  # noqa: E402
    generate_answer,
    refusal_message,
    retrieve,
)

from agent.state import AgentState  # noqa: E402


def _append_trace(state: AgentState, node: str, output: dict[str, Any]) -> list[dict[str, Any]]:
    entry = {"node": node, "output": output}
    return list(state.get("trace") or []) + [entry]


def receive_question(state: AgentState) -> dict[str, Any]:
    """Node 1 — normalize and validate the inbound question."""
    raw = (state.get("question") or "").strip()
    empty = not bool(raw)
    out = {
        "question": raw,
        "empty_question": empty,
        "chunks": [],
        "answer": "",
        "error": "empty_question" if empty else None,
        "has_context": False,
    }
    out["trace"] = _append_trace(state, "receive_question", {
        "empty_question": empty,
        "question_len": len(raw),
    })
    return out


def retrieve_knowledge(state: AgentState) -> dict[str, Any]:
    """Node 2 — call existing ``retrieve()`` (never ``query()``)."""
    question = state.get("question") or ""
    # Strip scores before generation; keep for internal quality checks
    raw_hits = retrieve(question)
    chunks = [{k: v for k, v in h.items() if k != "score"} for h in raw_hits]
    has_context = len(chunks) > 0
    out: dict[str, Any] = {
        "chunks": chunks,
        "has_context": has_context,
        "error": None if has_context else "insufficient_context",
    }
    out["trace"] = _append_trace(state, "retrieve_knowledge", {
        "n_chunks": len(chunks),
        "sources": sorted({
            str(c.get("source_document", "")) for c in chunks if c.get("source_document")
        }),
        "has_context": has_context,
    })
    return out


def generate_response(state: AgentState) -> dict[str, Any]:
    """Node 3 — call existing ``generate_answer(question, context)`` only."""
    question = state.get("question") or ""
    chunks = list(state.get("chunks") or [])
    answer = generate_answer(question, chunks)
    out: dict[str, Any] = {
        "answer": answer,
        "error": None,
    }
    out["trace"] = _append_trace(state, "generate_response", {
        "answer_len": len(answer or ""),
        "used_chunks": len(chunks),
    })
    return out


def refuse_honestly(state: AgentState) -> dict[str, Any]:
    """Honest refusal when question is empty or retrieval has no context."""
    reason = state.get("error") or (
        "empty_question" if state.get("empty_question") else "insufficient_context"
    )
    if reason == "empty_question":
        answer = (
            "No recibí una pregunta válida. Escribe una consulta sobre los "
            "manuales de Brasaland (lealtad, desperdicio, alérgenos o pedidos)."
        )
    else:
        answer = refusal_message()
    out: dict[str, Any] = {
        "answer": answer,
        "error": reason,
        "chunks": list(state.get("chunks") or []),
    }
    out["trace"] = _append_trace(state, "refuse_honestly", {
        "reason": reason,
        "answer_len": len(answer),
    })
    return out
