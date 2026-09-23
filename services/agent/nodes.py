"""LangGraph nodes — RAG + live tools (Parts 1–2)."""

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
from agent.tools.contracts import InventoryLookupInput, TicketLookupInput  # noqa: E402
from agent.tools.incidents import lookup_support_ticket  # noqa: E402
from agent.tools.inventory import lookup_inventory_stock  # noqa: E402
from agent.tools.routing import (  # noqa: E402
    classify_intent,
    extract_product_query,
    extract_ticket_id,
)


def _append_trace(state: AgentState, node: str, output: dict[str, Any]) -> list[dict[str, Any]]:
    return list(state.get("trace") or []) + [{"node": node, "output": output}]


def receive_question(state: AgentState) -> dict[str, Any]:
    """Normalize question and classify intent (rag | ticket | inventory)."""
    raw = (state.get("question") or "").strip()
    empty = not bool(raw)
    intent = "rag" if empty else classify_intent(raw)
    out: dict[str, Any] = {
        "question": raw,
        "empty_question": empty,
        "chunks": [],
        "answer": "",
        "error": "empty_question" if empty else None,
        "has_context": False,
        "intent": intent,
        "tool_ok": False,
        "tool_result": None,
        "sources_used": [],
    }
    out["trace"] = _append_trace(state, "receive_question", {
        "empty_question": empty,
        "question_len": len(raw),
        "intent": intent,
    })
    return out


def retrieve_knowledge(state: AgentState) -> dict[str, Any]:
    """RAG retrieve — never calls monolithic query()."""
    question = state.get("question") or ""
    raw_hits = retrieve(question)
    chunks = [{k: v for k, v in h.items() if k != "score"} for h in raw_hits]
    has_context = len(chunks) > 0
    sources = list(state.get("sources_used") or [])
    if has_context and "rag" not in sources:
        sources = sources + ["rag"]
    out: dict[str, Any] = {
        "chunks": chunks,
        "has_context": has_context,
        "error": None if has_context else "insufficient_context",
        "sources_used": sources,
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
    """RAG generation from retrieved chunks only."""
    question = state.get("question") or ""
    chunks = list(state.get("chunks") or [])
    answer = generate_answer(question, chunks)
    out: dict[str, Any] = {"answer": answer, "error": None}
    out["trace"] = _append_trace(state, "generate_response", {
        "answer_len": len(answer or ""),
        "used_chunks": len(chunks),
        "source": "rag",
    })
    return out


def lookup_ticket(state: AgentState) -> dict[str, Any]:
    """Node — call the support-ticket tool (real IncidentRepository)."""
    question = state.get("question") or ""
    ticket_id = extract_ticket_id(question)
    result = lookup_support_ticket(TicketLookupInput(ticket_id=ticket_id))
    payload = result.model_dump(mode="json")
    sources = list(state.get("sources_used") or [])
    if "ticket_tool" not in sources:
        sources = sources + ["ticket_tool"]
    out: dict[str, Any] = {
        "tool_ok": result.ok and bool(result.tickets),
        "tool_result": payload,
        "sources_used": sources,
        "error": None if (result.ok and result.tickets) else (
            result.error or "ticket_not_found"
        ),
    }
    out["trace"] = _append_trace(state, "lookup_ticket", {
        "ticket_id": ticket_id,
        "ok": result.ok,
        "timed_out": result.timed_out,
        "n_tickets": len(result.tickets),
        "error": result.error,
    })
    return out


def answer_from_ticket(state: AgentState) -> dict[str, Any]:
    """Format ticket tool payload into a salesperson-style answer (no invent)."""
    payload = state.get("tool_result") or {}
    tickets = payload.get("tickets") or []
    lines: list[str] = []
    for t in tickets:
        lines.append(
            f"Incidencia #{t.get('id')}: «{t.get('title')}» — "
            f"estado **{t.get('status')}**, categoría {t.get('category')}, "
            f"origen {t.get('origin')}, sede {t.get('branch')}. "
            f"Actualizada: {t.get('updated_at')}."
        )
    answer = " ".join(lines) if lines else (
        "No encontré incidencias que coincidan con tu consulta."
    )
    out: dict[str, Any] = {"answer": answer, "error": None}
    out["trace"] = _append_trace(state, "answer_from_ticket", {
        "n_tickets": len(tickets),
        "source": "ticket_tool",
    })
    return out


def lookup_inventory(state: AgentState) -> dict[str, Any]:
    """Node — call the inventory stock tool (real SQLModel inventory)."""
    question = state.get("question") or ""
    name_query = extract_product_query(question)
    result = lookup_inventory_stock(
        InventoryLookupInput(name_query=name_query, limit=10)
    )
    payload = result.model_dump(mode="json")
    sources = list(state.get("sources_used") or [])
    if "inventory_tool" not in sources:
        sources = sources + ["inventory_tool"]
    out: dict[str, Any] = {
        "tool_ok": result.ok and bool(result.products),
        "tool_result": payload,
        "sources_used": sources,
        "error": None if (result.ok and result.products) else (
            result.error or "product_not_found"
        ),
    }
    out["trace"] = _append_trace(state, "lookup_inventory", {
        "name_query": name_query,
        "ok": result.ok,
        "timed_out": result.timed_out,
        "n_products": len(result.products),
        "error": result.error,
    })
    return out


def answer_from_inventory(state: AgentState) -> dict[str, Any]:
    """Format inventory tool payload (stock figures from the live service)."""
    payload = state.get("tool_result") or {}
    products = payload.get("products") or []
    lines: list[str] = []
    for p in products:
        lines.append(
            f"{p.get('name')} (SKU {p.get('sku')}): "
            f"{p.get('current_stock')} {p.get('unit')} — "
            f"categoría {p.get('category')}, país {p.get('country')}."
        )
    answer = (
        "Stock actual según inventario: " + " ".join(lines)
        if lines
        else "No encontré productos de inventario para esa consulta."
    )
    out: dict[str, Any] = {"answer": answer, "error": None}
    out["trace"] = _append_trace(state, "answer_from_inventory", {
        "n_products": len(products),
        "source": "inventory_tool",
    })
    return out


def tool_fallback(state: AgentState) -> dict[str, Any]:
    """Honest fallback when a live tool times out / fails / misses."""
    intent = state.get("intent") or "ticket"
    err = state.get("error") or "tool_unavailable"
    payload = state.get("tool_result") or {}
    timed_out = bool(payload.get("timed_out"))
    if timed_out:
        answer = (
            "No pude confirmar ese dato operativo ahora mismo: el servicio "
            "no respondió a tiempo. Reinténtalo en unos segundos o consulta "
            "el panel de operaciones."
        )
        reason = "tool_timeout"
    elif intent == "ticket":
        answer = (
            "No pude confirmar el estado de esa incidencia en el gestor de "
            "soporte ahora mismo. No invento estados: verifica el id o "
            "revisa el panel de incidencias."
        )
        reason = err
    else:
        answer = (
            "No pude confirmar el stock en el inventario ahora mismo. "
            "No invento existencias: prueba otro nombre/SKU o revisa el "
            "backoffice de inventario."
        )
        reason = err
    out: dict[str, Any] = {
        "answer": answer,
        "error": reason,
    }
    out["trace"] = _append_trace(state, "tool_fallback", {
        "intent": intent,
        "reason": reason,
        "timed_out": timed_out,
    })
    return out


def refuse_honestly(state: AgentState) -> dict[str, Any]:
    """Honest refusal for empty questions or RAG with no context."""
    reason = state.get("error") or (
        "empty_question" if state.get("empty_question") else "insufficient_context"
    )
    if reason == "empty_question":
        answer = (
            "No recibí una pregunta válida. Puedes preguntar por manuales "
            "(lealtad, alérgenos…), por una incidencia (#id) o por stock."
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
