"""LangGraph: convert → classify → orchestrate → workers → synthesize."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from data.pipelines.rfp_intake.classifier import classify_rfp
from data.pipelines.rfp_intake.convert import compute_readability, pdf_to_markdown
from data.pipelines.rfp_intake.state import RfpIntakeState
from data.pipelines.rfp_intake.synthesizer import merge_worker_conflicts, synthesize
from data.pipelines.rfp_intake.workers import run_worker

RouteAfterClassify = Literal["discard", "orchestrate"]


def _trace(state: RfpIntakeState, node: str, output: dict[str, Any]) -> list[dict[str, Any]]:
    return list(state.get("trace") or []) + [{"node": node, "output": output}]


def node_convert(state: RfpIntakeState) -> dict[str, Any]:
    pdf = state["pdf_path"]
    md = pdf_to_markdown(pdf)
    out_dir = Path(pdf).resolve().parent
    md_path = out_dir / (Path(pdf).stem + ".md")
    md_path.write_text(md, encoding="utf-8")
    readability = compute_readability(md)
    return {
        "markdown": md,
        "markdown_path": str(md_path),
        "readability": readability,
        "status": "analizando",
        "trace": _trace(state, "convert", {"chars": len(md), **readability}),
    }


def node_classify(state: RfpIntakeState) -> dict[str, Any]:
    classification = classify_rfp(state.get("markdown") or "")
    readability = state.get("readability") or {}
    # Normaliza claves al esquema de persistencia (repository / UI)
    metadata = {
        **classification,
        "classifier_confidence": classification.get("confidence"),
        "classifier_notes": classification.get("notes"),
        "flesch_kincaid": readability.get("flesch_kincaid"),
        "gunning_fog": readability.get("gunning_fog"),
        "word_count": readability.get("word_count"),
    }
    if not classification.get("is_rfp"):
        return {
            "classification": classification,
            "metadata": metadata,
            "departments": [],
            "status": "descartado",
            "discard_reason": classification.get("notes") or "No es RFP",
            "trace": _trace(state, "classify", {"is_rfp": False, **classification}),
        }
    return {
        "classification": classification,
        "metadata": metadata,
        "departments": list(classification.get("departments_needed") or []),
        "status": "analizando",
        "discard_reason": None,
        "trace": _trace(state, "classify", {"is_rfp": True, **classification}),
    }


def route_after_classify(state: RfpIntakeState) -> RouteAfterClassify:
    if state.get("status") == "descartado" or not (state.get("classification") or {}).get(
        "is_rfp"
    ):
        return "discard"
    return "orchestrate"


def node_orchestrate(state: RfpIntakeState) -> dict[str, Any]:
    """Orquestador: workstreams por departamento (ids del BRIEFING)."""
    from data.pipelines.rfp_intake.departments_ref import normalize_departments

    departments = normalize_departments(list(state.get("departments") or []))
    return {
        "departments": departments,
        "trace": _trace(state, "orchestrate", {"departments": departments}),
    }


def node_workers(state: RfpIntakeState) -> dict[str, Any]:
    """Fan-out workers sequentially (same semantics as parallel workstreams)."""
    md = state.get("markdown") or ""
    meta = state.get("metadata") or {}
    results = [run_worker(d, md, meta) for d in state.get("departments") or []]
    conflicts = merge_worker_conflicts(results)
    if conflicts:
        meta = dict(meta)
        meta["open_questions"] = list(meta.get("open_questions") or []) + conflicts
    return {
        "worker_results": results,
        "metadata": meta,
        "trace": _trace(
            state,
            "workers",
            {"n": len(results), "departments": [r["department_id"] for r in results]},
        ),
    }


def node_synthesize(state: RfpIntakeState) -> dict[str, Any]:
    synth = synthesize(state.get("metadata") or {}, state.get("worker_results") or [])
    return {
        "synthesizer": synth,
        "status": "analisis_completo",
        "trace": _trace(state, "synthesize", {"departments": len(synth.get("departments") or [])}),
    }


def node_discard(state: RfpIntakeState) -> dict[str, Any]:
    return {
        "status": "descartado",
        "synthesizer": {},
        "worker_results": [],
        "trace": _trace(
            state,
            "discard",
            {"reason": state.get("discard_reason") or "classifier_reject"},
        ),
    }


def build_rfp_intake_graph():
    g = StateGraph(RfpIntakeState)
    g.add_node("convert", node_convert)
    g.add_node("classify", node_classify)
    g.add_node("orchestrate", node_orchestrate)
    g.add_node("workers", node_workers)
    g.add_node("synthesize", node_synthesize)
    g.add_node("discard", node_discard)

    g.add_edge(START, "convert")
    g.add_edge("convert", "classify")
    g.add_conditional_edges(
        "classify",
        route_after_classify,
        {"discard": "discard", "orchestrate": "orchestrate"},
    )
    g.add_edge("orchestrate", "workers")
    g.add_edge("workers", "synthesize")
    g.add_edge("synthesize", END)
    g.add_edge("discard", END)
    return g.compile()


def run_rfp_intake(*, ticket_id: int, pdf_path: str) -> dict[str, Any]:
    """Invoke the dedicated graph (no CX agent)."""
    graph = build_rfp_intake_graph()
    initial: RfpIntakeState = {
        "ticket_id": ticket_id,
        "pdf_path": pdf_path,
        "markdown": "",
        "markdown_path": "",
        "classification": {},
        "metadata": {},
        "departments": [],
        "worker_results": [],
        "synthesizer": {},
        "status": "analizando",
        "discard_reason": None,
        "error": None,
        "trace": [],
    }
    final = graph.invoke(initial)
    return dict(final)
