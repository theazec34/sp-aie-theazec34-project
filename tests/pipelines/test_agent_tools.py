"""Part 2 evals — RAG vs external tools routing + tool fallback."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SERVICES = _REPO / "services"
_API = _SERVICES / "api"
for _p in (_REPO, _SERVICES, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from agent.graph import get_compiled_graph, run_agent  # noqa: E402
from agent.tools.contracts import TicketLookupOutput  # noqa: E402
from agent.tools.routing import classify_intent  # noqa: E402
from agent.tracing import load_trace  # noqa: E402


@pytest.fixture()
def fresh_graph():
    get_compiled_graph.cache_clear()
    yield
    get_compiled_graph.cache_clear()


def test_classify_intent_ticket_vs_rag():
    assert classify_intent("¿Estado del ticket 12?") == "ticket"
    assert classify_intent("¿Cuántos puntos para el nivel Oro?") == "rag"
    assert classify_intent("¿Qué stock de lomo tenemos?") == "inventory"


def test_eval_ticket_question_uses_tool_not_rag(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval A — ticket question must hit lookup_ticket, never retrieve_knowledge."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    # Seed a real incident via TinyDB repository (not simulated tool output).
    from app.incidents.models import (
        IncidentBranch,
        IncidentCategory,
        IncidentCreate,
        IncidentOrigin,
    )
    from app.incidents.repository import IncidentRepository

    repo = IncidentRepository()
    try:
        created = repo.create(
            IncidentCreate(
                title="Horno no enciende",
                description="Local Medellín — horno principal sin flama",
                category=IncidentCategory.EQUIPMENT_FAILURE,
                origin=IncidentOrigin.BRANCH,
                branch=IncidentBranch.MEDELLIN_CENTRO,
            )
        )
        ticket_id = created.id
    finally:
        repo.close()

    retrieve_calls = {"n": 0}

    def _no_retrieve(_q, **_k):
        retrieve_calls["n"] += 1
        raise AssertionError("RAG retrieve must not run for ticket questions")

    monkeypatch.setattr("agent.nodes.retrieve", _no_retrieve)

    result = run_agent(f"¿Cuál es el estado de la incidencia {ticket_id}?")
    nodes = result["nodes"]
    assert "lookup_ticket" in nodes
    assert "answer_from_ticket" in nodes
    assert "retrieve_knowledge" not in nodes
    assert "generate_response" not in nodes
    assert retrieve_calls["n"] == 0
    assert "ticket_tool" in result["sources_used"]
    assert result["intent"] == "ticket"
    assert str(ticket_id) in result["answer"]
    assert "open" in result["answer"].lower() or "estado" in result["answer"].lower()

    saved = load_trace(result["run_id"])
    assert saved is not None
    assert "lookup_ticket" in saved["nodes"]


def test_eval_policy_question_uses_rag_not_tool(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval B — policy/loyalty question must use RAG path, not ticket tool."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    tool_calls = {"n": 0}

    def _no_ticket(payload, **_k):
        tool_calls["n"] += 1
        raise AssertionError("ticket tool must not run for RAG questions")

    monkeypatch.setattr("agent.nodes.lookup_support_ticket", _no_ticket)

    fake_chunks = [
        {
            "text": "Oro (50+ puntos): 15% de descuento permanente.",
            "source_document": "loyalty-program",
            "section": "Niveles",
            "company": "brasaland",
            "language": "es",
            "chunk_index": 1,
        }
    ]
    monkeypatch.setattr("agent.nodes.retrieve", lambda _q, **_k: fake_chunks)
    monkeypatch.setattr(
        "agent.nodes.generate_answer",
        lambda q, ctx: "Nivel Oro: 50+ puntos según Brasa Points.",
    )

    result = run_agent("¿Cuántos puntos necesito para el nivel Oro?")
    nodes = result["nodes"]
    assert "retrieve_knowledge" in nodes
    assert "generate_response" in nodes
    assert "lookup_ticket" not in nodes
    assert "lookup_inventory" not in nodes
    assert tool_calls["n"] == 0
    assert "rag" in result["sources_used"]
    assert result["intent"] == "rag"

    saved = load_trace(result["run_id"])
    assert saved is not None
    assert saved["nodes"] == nodes


def test_eval_ticket_tool_fallback_on_failure(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval C (optional) — tool failure/timeout → tool_fallback, no invented status."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fail(_payload, **_k):
        return TicketLookupOutput(
            ok=False,
            timed_out=True,
            error="Timeout (4.0s) al consultar el gestor de incidencias",
        )

    monkeypatch.setattr("agent.nodes.lookup_support_ticket", _fail)

    result = run_agent("¿Estado del ticket 99999?")
    nodes = result["nodes"]
    assert "lookup_ticket" in nodes
    assert "tool_fallback" in nodes
    assert "answer_from_ticket" not in nodes
    assert "no pude confirmar" in result["answer"].lower()
    # Must not invent a ticket status
    assert "resolved" not in result["answer"].lower()
    assert "in_progress" not in result["answer"].lower()
