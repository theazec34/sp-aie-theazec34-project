"""Parte 3: aprobación humana por departamento con interrupt + checkpointer SQLite.

Cada departamento usa thread_id `rfp-{ticket_id}:{department_id}` para no bloquear
a los demás. El CEO usa `rfp-{ticket_id}:ceo` cuando aplica el umbral.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from data.pipelines.rfp_intake.arbitration import apply_arbitration, detect_conflicts
from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS
from data.pipelines.rfp_intake.final_document import synthesize_final_document
from data.pipelines.rfp_intake.guidelines import MAX_APPROVAL_ITERATIONS

ApprovalAction = Literal["approve", "reject", "request_changes"]

_REPO = Path(__file__).resolve().parents[3]
_CHECKPOINT_DIR = _REPO / "data" / "rfp_checkpoints"
_CHECKPOINT_DB = _CHECKPOINT_DIR / "rfp_approval.sqlite"


class DeptApprovalState(TypedDict, total=False):
    ticket_id: int
    department_id: str
    draft_content: str
    key_aspects: list[str]
    approver_name: str
    approval_status: str
    approval_action: str
    comment: str
    iteration: int
    trace: list[dict[str, Any]]
    max_iterations: int


def thread_id_for(ticket_id: int, department_id: str) -> str:
    return f"rfp-{ticket_id}:{department_id}"


def _append_trace(
    state: DeptApprovalState,
    *,
    agent: str,
    input_data: Any,
    output_data: Any,
) -> list[dict[str, Any]]:
    return list(state.get("trace") or []) + [
        {
            "agent": agent,
            "input": input_data,
            "output": output_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]


def _get_saver() -> SqliteSaver:
    _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_CHECKPOINT_DB), check_same_thread=False)
    return SqliteSaver(conn)


def build_department_approval_graph():
    """Grafo por departamento: interrupt HITL → valida → aprueba o itera."""

    def prepare(state: DeptApprovalState) -> dict[str, Any]:
        info = DEPARTMENTS.get(state["department_id"], {})
        return {
            "approver_name": state.get("approver_name") or info.get("owner") or "",
            "approval_status": "pendiente",
            "iteration": int(state.get("iteration") or 0),
            "max_iterations": int(state.get("max_iterations") or MAX_APPROVAL_ITERATIONS),
            "trace": _append_trace(
                state,
                agent="prepare_approval",
                input_data={"department_id": state["department_id"]},
                output_data={"approver": info.get("owner")},
            ),
        }

    def await_human(state: DeptApprovalState) -> dict[str, Any]:
        payload = {
            "type": "department_approval",
            "ticket_id": state["ticket_id"],
            "department_id": state["department_id"],
            "approver": state.get("approver_name"),
            "draft_excerpt": (state.get("draft_content") or "")[:1200],
            "key_aspects": state.get("key_aspects") or [],
            "allowed_actions": ["approve", "reject", "request_changes"],
            "iteration": state.get("iteration") or 0,
        }
        decision = interrupt(payload)
        # decision esperado: {action, comment?}
        action = (decision or {}).get("action") if isinstance(decision, dict) else None
        comment = (decision or {}).get("comment", "") if isinstance(decision, dict) else ""
        if action not in {"approve", "reject", "request_changes"}:
            # Re-interrupt if invalid
            decision = interrupt(
                {
                    **payload,
                    "error": "Acción inválida; use approve | reject | request_changes",
                }
            )
            action = (decision or {}).get("action")
            comment = (decision or {}).get("comment", "")
        return {
            "approval_action": action,
            "comment": comment or "",
            "trace": _append_trace(
                state,
                agent="human_interrupt",
                input_data=payload,
                output_data={"action": action, "comment": comment},
            ),
        }

    def apply_decision(state: DeptApprovalState) -> dict[str, Any]:
        action = state.get("approval_action") or ""
        iteration = int(state.get("iteration") or 0) + 1
        if action == "approve":
            status = "aprobado"
        elif iteration >= int(state.get("max_iterations") or MAX_APPROVAL_ITERATIONS):
            status = "needs_human_review"
        else:
            status = "rechazado" if action == "reject" else "cambios_solicitados"
        return {
            "approval_status": status,
            "iteration": iteration,
            "trace": _append_trace(
                state,
                agent="apply_decision",
                input_data={"action": action},
                output_data={"approval_status": status, "iteration": iteration},
            ),
        }

    def route_after(state: DeptApprovalState) -> str:
        if state.get("approval_status") == "aprobado":
            return "done"
        if state.get("approval_status") == "needs_human_review":
            return "done"
        # reject / request_changes → volver a interrupt (HITL otra vez)
        return "again"

    g = StateGraph(DeptApprovalState)
    g.add_node("prepare", prepare)
    g.add_node("await_human", await_human)
    g.add_node("apply_decision", apply_decision)
    g.add_edge(START, "prepare")
    g.add_edge("prepare", "await_human")
    g.add_edge("await_human", "apply_decision")
    g.add_conditional_edges(
        "apply_decision",
        route_after,
        {"done": END, "again": "await_human"},
    )
    return g.compile(checkpointer=_get_saver())


_DEPT_GRAPH = None


def get_department_graph():
    global _DEPT_GRAPH
    if _DEPT_GRAPH is None:
        _DEPT_GRAPH = build_department_approval_graph()
    return _DEPT_GRAPH


def start_department_approval(
    *,
    ticket_id: int,
    department_id: str,
    draft_content: str,
    key_aspects: list[str] | None = None,
    approver_name: str | None = None,
) -> dict[str, Any]:
    """Arranca HITL para un depto; retorna estado interrupted + payload."""
    graph = get_department_graph()
    tid = thread_id_for(ticket_id, department_id)
    info = DEPARTMENTS.get(department_id, {})
    initial: DeptApprovalState = {
        "ticket_id": ticket_id,
        "department_id": department_id,
        "draft_content": draft_content or "",
        "key_aspects": list(key_aspects or []),
        "approver_name": approver_name or info.get("owner") or "",
        "approval_status": "pendiente",
        "iteration": 0,
        "trace": [],
        "max_iterations": MAX_APPROVAL_ITERATIONS,
    }
    result = graph.invoke(initial, config={"configurable": {"thread_id": tid}})
    return _normalize_invoke_result(ticket_id, department_id, tid, result, graph)


def resume_department_approval(
    *,
    ticket_id: int,
    department_id: str,
    action: ApprovalAction,
    comment: str = "",
) -> dict[str, Any]:
    graph = get_department_graph()
    tid = thread_id_for(ticket_id, department_id)
    result = graph.invoke(
        Command(resume={"action": action, "comment": comment}),
        config={"configurable": {"thread_id": tid}},
    )
    return _normalize_invoke_result(ticket_id, department_id, tid, result, graph)


def _normalize_invoke_result(
    ticket_id: int,
    department_id: str,
    tid: str,
    result: Any,
    graph,
) -> dict[str, Any]:
    # Si hay interrupt pendiente
    state = graph.get_state({"configurable": {"thread_id": tid}})
    tasks = list(getattr(state, "tasks", None) or [])
    interrupts = []
    for t in tasks:
        ints = getattr(t, "interrupts", None) or ()
        for i in ints:
            val = getattr(i, "value", i)
            interrupts.append(val)

    if interrupts:
        return {
            "ticket_id": ticket_id,
            "department_id": department_id,
            "thread_id": tid,
            "status": "interrupted",
            "pending_interrupt": interrupts[0],
            "approval_status": "pendiente",
            "trace": (result or {}).get("trace") if isinstance(result, dict) else [],
        }

    out = result if isinstance(result, dict) else {}
    return {
        "ticket_id": ticket_id,
        "department_id": department_id,
        "thread_id": tid,
        "status": "completed",
        "pending_interrupt": None,
        "approval_status": out.get("approval_status") or "pendiente",
        "approval_action": out.get("approval_action"),
        "comment": out.get("comment") or "",
        "iteration": out.get("iteration") or 0,
        "trace": out.get("trace") or [],
        "approver_name": out.get("approver_name"),
    }


def run_arbitration_and_maybe_finalize(
    *,
    ticket_id: int,
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    ceo_approval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Nodo de arbitraje + síntesis si todo está aprobado."""
    conflicts = detect_conflicts(
        metadata=metadata,
        sections=sections,
        ceo_approved=bool(ceo_approval and ceo_approval.get("action") == "approve"),
    )
    arb = apply_arbitration(conflicts)
    all_approved = all(
        (s.get("approval_status") == "aprobado") for s in sections
    )
    needs_ceo = any(c["trigger_id"] == "ceo-threshold" for c in conflicts)
    ceo_ok = (not needs_ceo) or (
        ceo_approval is not None and ceo_approval.get("action") == "approve"
    )

    final_doc = None
    status = "esperando_aprobacion"
    if all_approved and ceo_ok and not arb["request_changes_targets"]:
        final_doc = synthesize_final_document(
            ticket_id=ticket_id,
            metadata=metadata,
            sections=sections,
            ceo_approval=ceo_approval,
            arbitration_log=arb.get("orders") or [],
        )
        status = "terminado"

    return {
        "ticket_id": ticket_id,
        "status": status,
        "arbitration": arb,
        "needs_ceo": needs_ceo,
        "final_document": final_doc,
        "trace": [
            {
                "agent": "arbitration",
                "input": {"conflicts": len(conflicts)},
                "output": arb,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
