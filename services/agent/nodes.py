"""LangGraph nodes — RAG + MCP tools + memory + security harness.

Operational data via MCP. Memory via AgentMemory. Guardrails wrap input/output
and isolate untrusted RAG/tool text.
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

from agent.guardrails import (  # noqa: E402
    guard_answer,
    guard_user_input,
    prepare_rag_context,
    prepare_tool_result,
)
from agent.memory.interface import get_agent_memory  # noqa: E402
from agent.memory.pending import get_pending  # noqa: E402
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


def _session_id(state: AgentState) -> str:
    return str(state.get("session_id") or state.get("run_id") or "default")


def _finalize_answer(
    state: AgentState,
    answer: str,
    *,
    require_redirect: bool = False,
) -> str:
    check = guard_answer(
        answer,
        session_id=_session_id(state),
        require_redirect=require_redirect,
        question=state.get("question"),
    )
    return check.sanitized_answer


def receive_question(state: AgentState) -> dict[str, Any]:
    """Normalize question; apply input guardrails; route memory confirm if pending."""
    raw = (state.get("question") or "").strip()
    empty = not bool(raw)
    session = _session_id(state)
    pending = None if empty else get_pending(session)

    guard_action = None
    guard_reason = None
    guard_failure = None
    answer = ""
    intent: str

    if pending is not None and not empty:
        intent = "memory_confirm"
    elif empty:
        intent = "rag"
    else:
        decision = guard_user_input(raw, session_id=session)
        guard_action = decision.action
        guard_reason = decision.reason_code
        guard_failure = (
            decision.failure_type.value if decision.failure_type else None
        )
        if decision.action == "block":
            intent = "guard_block"
            answer = decision.message
        elif decision.action == "redirect":
            intent = "casual"
            answer = decision.message
        else:
            intent = classify_intent(raw)

    out: dict[str, Any] = {
        "question": raw,
        "empty_question": empty,
        "chunks": [],
        "answer": answer,
        "error": "empty_question" if empty else (
            guard_reason if intent in {"guard_block", "casual"} else None
        ),
        "has_context": False,
        "intent": intent,
        "tool_ok": False,
        "tool_result": None,
        "sources_used": (["guardrails"] if intent in {"guard_block", "casual"} else []),
        "memory_hits": [],
        "memory_proposal": None,
        "memory_decision": None,
        "pending_resolved": False,
        "session_id": session,
        "guard_action": guard_action,
        "guard_reason": guard_reason,
        "guard_failure_type": guard_failure,
    }
    out["trace"] = _append_trace(state, "receive_question", {
        "empty_question": empty,
        "question_len": len(raw),
        "intent": intent,
        "pending_proposal": pending is not None,
        "guard_action": guard_action,
        "guard_reason": guard_reason,
        "guard_failure_type": guard_failure,
    })
    return out


def emit_guard_response(state: AgentState) -> dict[str, Any]:
    """Terminal node for blocked / casual-redirect answers (already set)."""
    answer = _finalize_answer(
        state,
        state.get("answer") or "",
        require_redirect=state.get("intent") == "casual",
    )
    out: dict[str, Any] = {
        "answer": answer,
        "error": state.get("guard_reason") or state.get("error"),
        "sources_used": list(state.get("sources_used") or [])
        if "guardrails" in (state.get("sources_used") or [])
        else list(state.get("sources_used") or []) + ["guardrails"],
    }
    out["trace"] = _append_trace(state, "emit_guard_response", {
        "guard_action": state.get("guard_action"),
        "guard_reason": state.get("guard_reason"),
        "guard_failure_type": state.get("guard_failure_type"),
        "answer_len": len(answer),
    })
    return out


def resolve_memory_confirm(state: AgentState) -> dict[str, Any]:
    """Classify approve/reject/edit/ambiguous; write only on explicit decision."""
    mem = get_agent_memory()
    session = _session_id(state)
    question = state.get("question") or ""
    user_id = state.get("user_id")

    ack, outcome, confirm = mem.handle_confirmation(
        session, question, user_id=user_id
    )

    # topic_change: pending discarded; re-run input guards then continue
    if outcome and outcome.value == "discarded_topic_change":
        decision = guard_user_input(question, session_id=session)
        if decision.action == "block":
            intent = "guard_block"
            answer = _finalize_answer(state, decision.message)
        elif decision.action == "redirect":
            intent = "casual"
            answer = _finalize_answer(
                state, decision.message, require_redirect=True
            )
        else:
            intent = classify_intent(question)
            answer = ""
        out: dict[str, Any] = {
            "intent": intent,
            "pending_resolved": True,
            "memory_decision": outcome.value,
            "answer": answer,
            "error": decision.reason_code if decision.action != "allow" else None,
            "guard_action": decision.action,
            "guard_reason": decision.reason_code,
            "guard_failure_type": (
                decision.failure_type.value if decision.failure_type else None
            ),
        }
        out["trace"] = _append_trace(state, "resolve_memory_confirm", {
            "outcome": outcome.value,
            "confirm_label": confirm.label if confirm else None,
            "continue_intent": intent,
            "guard_action": decision.action,
        })
        return out

    out = {
        "answer": ack,
        "pending_resolved": True,
        "memory_decision": outcome.value if outcome else None,
        "error": None,
        "intent": "memory_confirm",
        "sources_used": list(state.get("sources_used") or []) + (
            ["memory"] if "memory" not in (state.get("sources_used") or []) else []
        ),
    }
    out["trace"] = _append_trace(state, "resolve_memory_confirm", {
        "outcome": outcome.value if outcome else None,
        "confirm_label": confirm.label if confirm else None,
        "wrote": outcome.value in {"approved", "edited"} if outcome else False,
    })
    return out


def retrieve_knowledge(state: AgentState) -> dict[str, Any]:
    """RAG retrieve — isolate untrusted chunks; also loads agent memory hits."""
    question = state.get("question") or ""
    session = _session_id(state)
    raw_hits = retrieve(question)
    raw_chunks = [{k: v for k, v in h.items() if k != "score"} for h in raw_hits]
    chunks = prepare_rag_context(raw_chunks, session_id=session)
    has_context = len(chunks) > 0

    mem = get_agent_memory()
    memory_hits = [e.model_dump(mode="json") for e in mem.read_relevant(question)]
    if memory_hits:
        has_context = True

    sources = list(state.get("sources_used") or [])
    if chunks and "rag" not in sources:
        sources = sources + ["rag"]
    if memory_hits and "memory" not in sources:
        sources = sources + ["memory"]

    out: dict[str, Any] = {
        "chunks": chunks,
        "has_context": has_context,
        "error": None if has_context else "insufficient_context",
        "sources_used": sources,
        "memory_hits": memory_hits,
    }
    out["trace"] = _append_trace(state, "retrieve_knowledge", {
        "n_chunks": len(chunks),
        "n_memory": len(memory_hits),
        "isolated": True,
        "sources": sorted({
            str(c.get("source_document", "")) for c in chunks if c.get("source_document")
        }),
        "has_context": has_context,
    })
    return out


def generate_response(state: AgentState) -> dict[str, Any]:
    """RAG generation + memory context; output guard; optional memory proposal."""
    question = state.get("question") or ""
    chunks = list(state.get("chunks") or [])
    mem = get_agent_memory()
    memory_entries = mem.read_relevant(question)
    memory_ctx = mem.format_context(memory_entries)

    if chunks:
        answer = generate_answer(question, chunks)
    elif memory_ctx:
        answer = (
            "Según lo que acordamos recordar en conversaciones anteriores:\n"
            + "\n".join(f"- {e.fact}" for e in memory_entries)
        )
    else:
        answer = refusal_message()

    if memory_ctx and chunks:
        answer = answer + "\n\n" + memory_ctx

    answer, proposal_dump = _maybe_attach_proposal(state, question, answer)
    answer = _finalize_answer(state, answer)

    out: dict[str, Any] = {
        "answer": answer,
        "error": None,
        "memory_proposal": proposal_dump,
    }
    out["trace"] = _append_trace(state, "generate_response", {
        "answer_len": len(answer or ""),
        "used_chunks": len(chunks),
        "used_memory": len(memory_entries),
        "proposed_memory": proposal_dump is not None,
        "source": "rag+memory" if memory_entries else "rag",
        "output_guarded": True,
    })
    return out


def _maybe_attach_proposal(
    state: AgentState, question: str, answer: str
) -> tuple[str, dict[str, Any] | None]:
    """Self-eval; propose in-conversation; never write here. Max one pending."""
    session = _session_id(state)
    if get_pending(session) is not None:
        return answer, None
    mem = get_agent_memory()
    proposal = mem.self_evaluate(question, answer)
    if proposal is None:
        return answer, None
    suffix = mem.propose(session, proposal)
    if suffix is None:
        return answer, None
    return answer + suffix, proposal.model_dump(mode="json")


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
    tool_result = prepare_tool_result(
        {
            "ok": ok,
            "source": "mcp:manage_incidents",
            "tickets": tickets,
            "error": None if ok else (payload.get("error") or payload.get("error_code")),
            "timed_out": timed_out,
            "mcp": payload,
        },
        session_id=_session_id(state),
    )
    sources = list(state.get("sources_used") or [])
    if "ticket_tool" not in sources:
        sources = sources + ["ticket_tool"]
    if "mcp" not in sources:
        sources = sources + ["mcp"]
    out: dict[str, Any] = {
        "tool_ok": ok,
        "tool_result": tool_result,
        "sources_used": sources,
        "error": None if ok else (tool_result.get("error") or "ticket_not_found"),
    }
    out["trace"] = _append_trace(state, "lookup_ticket", {
        "ticket_id": ticket_id,
        "ok": ok,
        "timed_out": timed_out,
        "n_tickets": len(tickets),
        "error": tool_result.get("error"),
        "via": "mcp",
        "isolated": True,
    })
    return out


def answer_from_ticket(state: AgentState) -> dict[str, Any]:
    """Format ticket tool payload; optional memory proposal; output guard."""
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
    question = state.get("question") or ""
    answer, proposal_dump = _maybe_attach_proposal(state, question, answer)
    answer = _finalize_answer(state, answer)
    out: dict[str, Any] = {
        "answer": answer,
        "error": None,
        "memory_proposal": proposal_dump,
    }
    out["trace"] = _append_trace(state, "answer_from_ticket", {
        "n_tickets": len(tickets),
        "source": "mcp:manage_incidents",
        "proposed_memory": proposal_dump is not None,
        "output_guarded": True,
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
    tool_result = prepare_tool_result(
        {
            "ok": ok,
            "source": "mcp:query_inventory",
            "products": products,
            "error": None if ok else (payload.get("error") or payload.get("error_code")),
            "timed_out": timed_out,
            "mcp": payload,
        },
        session_id=_session_id(state),
    )
    sources = list(state.get("sources_used") or [])
    if "inventory_tool" not in sources:
        sources = sources + ["inventory_tool"]
    if "mcp" not in sources:
        sources = sources + ["mcp"]
    out: dict[str, Any] = {
        "tool_ok": ok,
        "tool_result": tool_result,
        "sources_used": sources,
        "error": None if ok else (tool_result.get("error") or "product_not_found"),
    }
    out["trace"] = _append_trace(state, "lookup_inventory", {
        "name_query": name_query,
        "ok": ok,
        "timed_out": timed_out,
        "n_products": len(products),
        "error": tool_result.get("error"),
        "via": "mcp",
        "isolated": True,
    })
    return out


def answer_from_inventory(state: AgentState) -> dict[str, Any]:
    """Format inventory payload; optional memory proposal; output guard."""
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
    question = state.get("question") or ""
    answer, proposal_dump = _maybe_attach_proposal(state, question, answer)
    answer = _finalize_answer(state, answer)
    out: dict[str, Any] = {
        "answer": answer,
        "error": None,
        "memory_proposal": proposal_dump,
    }
    out["trace"] = _append_trace(state, "answer_from_inventory", {
        "n_products": len(products),
        "source": "mcp:query_inventory",
        "proposed_memory": proposal_dump is not None,
        "output_guarded": True,
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
