"""LangGraph nodes — RAG + MCP tools (Parts 1–3).

Operational data (incidents / inventory) is loaded exclusively through the
Brasaland MCP Server client (`langchain-mcp-adapters`). Direct
IncidentRepository / inventory ORM calls from the agent are removed.
"""

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
from agent.tools.mcp_client import (  # noqa: E402
    manage_incidents_via_mcp,
    query_inventory_via_mcp,
)
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
    """Node — Incidents Manager via MCP client (no direct repository calls)."""
    question = state.get("question") or ""
    ticket_id = extract_ticket_id(question)
    if ticket_id is not None:
        payload = manage_incidents_via_mcp(action="get", incident_id=ticket_id)
        tickets = []
        if payload.get("ok") and payload.get("incident"):
            tickets = [payload["incident"]]
    else:
        payload = manage_incidents_via_mcp(action="list", limit=5)
        tickets = list(payload.get("incidents") or []) if payload.get("ok") else []

    timed_out = bool(payload.get("timed_out"))
    ok = bool(payload.get("ok")) and bool(tickets)
    tool_result = {
        "ok": ok,
        "source": "mcp:manage_incidents",
        "tickets": tickets,
        "error": None if ok else (payload.get("error") or payload.get("error_code")),
        "timed_out": timed_out,
        "mcp": payload,
    }
    sources = list(state.get("sources_used") or [])
    if "ticket_tool" not in sources:
        sources = sources + ["ticket_tool"]
    if "mcp" not in sources:
        sources = sources + ["mcp"]
    out: dict[str, Any] = {
        "tool_ok": ok,
        "tool_result": tool_result,
        "sources_used": sources,
        "error": None if ok else (tool_result["error"] or "ticket_not_found"),
    }
    out["trace"] = _append_trace(state, "lookup_ticket", {
        "ticket_id": ticket_id,
        "ok": ok,
        "timed_out": timed_out,
        "n_tickets": len(tickets),
        "error": tool_result["error"],
        "via": "mcp",
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
        "source": "mcp:manage_incidents",
    })
    return out


def lookup_inventory(state: AgentState) -> dict[str, Any]:
    """Node — inventory stock via MCP client (read-only tool)."""
    question = state.get("question") or ""
    name_query = extract_product_query(question)
    payload = query_inventory_via_mcp(name_query=name_query, limit=10)
    products = list(payload.get("products") or []) if payload.get("ok") else []
    timed_out = bool(payload.get("timed_out"))
    ok = bool(payload.get("ok")) and bool(products)
    tool_result = {
        "ok": ok,
        "source": "mcp:query_inventory",
        "products": products,
        "error": None if ok else (payload.get("error") or payload.get("error_code")),
        "timed_out": timed_out,
        "mcp": payload,
    }
    sources = list(state.get("sources_used") or [])
    if "inventory_tool" not in sources:
        sources = sources + ["inventory_tool"]
    if "mcp" not in sources:
        sources = sources + ["mcp"]
    out: dict[str, Any] = {
        "tool_ok": ok,
        "tool_result": tool_result,
        "sources_used": sources,
        "error": None if ok else (tool_result["error"] or "product_not_found"),
    }
    out["trace"] = _append_trace(state, "lookup_inventory", {
        "name_query": name_query,
        "ok": ok,
        "timed_out": timed_out,
        "n_products": len(products),
        "error": tool_result["error"],
        "via": "mcp",
    })
    return out


def answer_from_inventory(state: AgentState) -> dict[str, Any]:
    """Format inventory tool payload (stock figures from MCP / live service)."""
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
        "source": "mcp:query_inventory",
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
