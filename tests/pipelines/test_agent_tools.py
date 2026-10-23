"""Part 2/3 evals — RAG vs MCP tools routing + tool fallback."""

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
from agent.tools.routing import classify_intent  # noqa: E402
from agent.tracing import load_trace  # noqa: E402


@pytest.fixture()
def fresh_graph(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_INPROCESS", "1")
    monkeypatch.setenv("MCP_AUTH_MODE", "dev")
    monkeypatch.setenv("MCP_DATA_MODE", "direct")
    get_compiled_graph.cache_clear()
    yield
    get_compiled_graph.cache_clear()


def test_classify_intent_ticket_vs_rag():
    assert classify_intent("¿Estado del ticket 12?") == "ticket"
    assert classify_intent("¿Cuántos puntos para el nivel Oro?") == "rag"
    assert classify_intent("¿Qué stock de lomo tenemos?") == "inventory"
    assert classify_intent("¿Cuál es el mayor proveedor en €?") == "supplier"
    assert classify_intent("¿Cuáles fueron las últimas salidas?") == "inventory"
    assert (
        classify_intent("¿Qué proveedor nos ha enviado más kg?") == "inventory"
    )
    assert classify_intent("¿Qué reservas tengo hoy?") == "front_ops"
    assert classify_intent("¿Cuántas candidaturas hay?") == "front_ops"


def test_eval_ticket_question_uses_mcp_not_rag(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval A — ticket question hits MCP manage_incidents, never RAG retrieve."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

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

    # Guard: direct deprecated tool must never be used.
    from agent.tools import incidents as deprecated_incidents

    def _boom(*_a, **_k):
        raise AssertionError("direct IncidentRepository path must not run")

    monkeypatch.setattr(deprecated_incidents, "lookup_support_ticket", _boom)

    result = run_agent(f"¿Cuál es el estado de la incidencia {ticket_id}?")
    nodes = result["nodes"]
    assert "lookup_ticket" in nodes
    assert "answer_from_ticket" in nodes
    assert "retrieve_knowledge" not in nodes
    assert "generate_response" not in nodes
    assert retrieve_calls["n"] == 0
    assert "ticket_tool" in result["sources_used"]
    assert "mcp" in result["sources_used"]
    assert result["intent"] == "ticket"
    assert str(ticket_id) in result["answer"]
    assert "open" in result["answer"].lower() or "estado" in result["answer"].lower()

    saved = load_trace(result["run_id"])
    assert saved is not None
    assert "lookup_ticket" in saved["nodes"]


def test_eval_policy_question_uses_rag_not_tool(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval B — policy/loyalty question must use RAG path, not MCP ticket tool."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    tool_calls = {"n": 0}

    def _no_mcp(**_k):
        tool_calls["n"] += 1
        raise AssertionError("MCP ticket tool must not run for RAG questions")

    monkeypatch.setattr("agent.nodes.manage_incidents_via_mcp", _no_mcp)

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
    """Eval C — MCP failure/timeout → tool_fallback, no invented status."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fail(**_k):
        return {
            "ok": False,
            "timed_out": True,
            "error": "Timeout (4.0s) al llamar MCP tool manage_incidents",
            "error_code": "MCP_TIMEOUT",
        }

    monkeypatch.setattr("agent.nodes.manage_incidents_via_mcp", _fail)

    result = run_agent("¿Estado del ticket 99999?")
    nodes = result["nodes"]
    assert "lookup_ticket" in nodes
    assert "tool_fallback" in nodes
    assert "answer_from_ticket" not in nodes
    assert "no pude confirmar" in result["answer"].lower()
    assert "resolved" not in result["answer"].lower()
    assert "in_progress" not in result["answer"].lower()


def test_deprecated_direct_incident_tool_raises():
    from agent.tools.contracts import TicketLookupInput
    from agent.tools.incidents import lookup_support_ticket

    with pytest.raises(RuntimeError, match="DEPRECATED"):
        lookup_support_ticket(TicketLookupInput(ticket_id=1))


def test_eval_supplier_question_uses_mcp(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fake_suppliers(**_k):
        return {
            "ok": True,
            "action": "top_rate",
            "currency": "EUR",
            "suppliers": [
                {
                    "name": "Carnes del Sur",
                    "rate_per_unit": 42.5,
                    "currency": "EUR",
                    "status": "active",
                    "categories": ["carne"],
                    "country": "España",
                }
            ],
            "count": 1,
        }

    monkeypatch.setattr("agent.nodes.query_suppliers_via_mcp", _fake_suppliers)
    monkeypatch.setattr(
        "agent.nodes.retrieve",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no RAG")),
    )

    result = run_agent("¿Cuál es el mayor proveedor en €?")
    assert result["intent"] == "supplier"
    assert "lookup_supplier" in result["nodes"]
    assert "answer_from_supplier" in result["nodes"]
    assert "retrieve_knowledge" not in result["nodes"]
    assert "Carnes del Sur" in result["answer"]
    assert "mcp" in result["sources_used"]


def test_eval_inventory_summary_uses_ops_tool(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fake_ops(**kwargs):
        assert kwargs.get("view") == "summary"
        return {
            "ok": True,
            "view": "summary",
            "summary": {
                "currency": "EUR",
                "products_count": 2,
                "inbound_count": 1,
                "outbound_count": 1,
                "inbound_qty_total": 10.0,
                "outbound_qty_total": 3.0,
                "top_suppliers_by_inbound_qty": [
                    {
                        "supplier_name": "Carnes del Sur",
                        "total_qty": 10.0,
                        "rate_per_unit_eur": 5.0,
                        "estimated_value_eur": 50.0,
                    }
                ],
                "top_stock": [],
                "highest_tariff_supplier": {
                    "name": "Carnes del Sur",
                    "rate_per_unit": 5.0,
                    "currency": "EUR",
                    "categories": ["carne"],
                },
            },
        }

    monkeypatch.setattr("agent.nodes.query_inventory_ops_via_mcp", _fake_ops)
    result = run_agent("¿Qué proveedor nos ha enviado más kg?")

    assert result["intent"] == "inventory"
    assert "lookup_inventory" in result["nodes"]
    assert "answer_from_inventory" in result["nodes"]
    assert "Carnes del Sur" in result["answer"]
    assert "10" in result["answer"]


def test_eval_front_ops_reservations(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fake_front(**kwargs):
        assert kwargs.get("action") == "reservations"
        return {
            "ok": True,
            "action": "reservations",
            "branch": "miami_doral",
            "day": "today",
            "reservations": [
                {
                    "full_name": "Cliente Demo Miami Doral",
                    "date": "2026-10-23",
                    "time": "20:00:00",
                    "guests": 4,
                    "status": "received",
                }
            ],
            "count": 1,
        }

    monkeypatch.setattr("agent.nodes.query_front_ops_via_mcp", _fake_front)
    result = run_agent(
        "¿Qué reservas tengo hoy?",
        location_id="miami_doral",
    )
    assert result["intent"] == "front_ops"
    assert "lookup_front_ops" in result["nodes"]
    assert "Cliente Demo Miami Doral" in result["answer"]


def test_supplier_empty_directory_still_answers(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """MCP ok + 0 suppliers must not hit tool_fallback."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    def _fake_empty(**_k):
        return {
            "ok": True,
            "action": "top_rate",
            "currency": "EUR",
            "suppliers": [],
            "count": 0,
        }

    monkeypatch.setattr("agent.nodes.query_suppliers_via_mcp", _fake_empty)
    result = run_agent("¿Cuál es el proveedor con la tarifa más alta en €?")
    assert result["intent"] == "supplier"
    assert "answer_from_supplier" in result["nodes"]
    assert "tool_fallback" not in result["nodes"]
