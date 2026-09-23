"""LangGraph agent evals — assert against persisted traces (Part 1).

Run:

    uv run pytest tests/pipelines/test_agent_graph.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SERVICES = _REPO / "services"
for _p in (_REPO, _SERVICES):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from agent.graph import build_agent_graph, get_compiled_graph, run_agent  # noqa: E402
from agent.tracing import load_trace  # noqa: E402


@pytest.fixture()
def fresh_graph(monkeypatch: pytest.MonkeyPatch):
    """Clear cached compiled graph between tests that mutate retrieve."""
    get_compiled_graph.cache_clear()
    yield
    get_compiled_graph.cache_clear()


def test_graph_compiles_with_checkpointing():
    graph = build_agent_graph()
    assert graph is not None
    # Structural compile succeeded — graph has nodes
    # (LangGraph exposes nodes via get_graph)
    g = graph.get_graph()
    node_ids = set(g.nodes.keys())
    assert "receive_question" in node_ids
    assert "retrieve_knowledge" in node_ids
    assert "generate_response" in node_ids
    assert "refuse_honestly" in node_ids


def test_eval_empty_question_routes_to_refuse_without_retrieve(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval 1 — empty input never calls retrieve; refuse node is in the trace."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    called = {"retrieve": 0}

    def _boom(_q, **_kw):
        called["retrieve"] += 1
        raise AssertionError("retrieve must not run for empty questions")

    monkeypatch.setattr("agent.nodes.retrieve", _boom)

    result = run_agent("   ")
    nodes = result["nodes"]
    assert nodes[0] == "receive_question"
    assert "retrieve_knowledge" not in nodes
    assert "refuse_honestly" in nodes
    assert "generate_response" not in nodes
    assert result["error"] == "empty_question"

    # Trace consultable after the run
    saved = load_trace(result["run_id"])
    assert saved is not None
    assert saved["nodes"] == nodes
    assert result["checkpointed"] is True


def test_eval_retrieve_before_generate_and_kb_anchor(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval 2 — loyalty question: retrieve runs before generate; answer anchored."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    fake_chunks = [
        {
            "text": "Oro (50+ puntos): 15% de descuento permanente.",
            "source_document": "loyalty-program",
            "section": "Niveles del programa",
            "company": "brasaland",
            "language": "es",
            "chunk_index": 1,
            "score": 0.7,
        }
    ]

    def _fake_retrieve(q, **_kw):
        return list(fake_chunks)

    def _fake_generate(question, context):
        assert context, "generate must receive retrieved context"
        assert context[0]["source_document"] == "loyalty-program"
        return (
            "Según el programa Brasa Points, el nivel Oro requiere 50+ puntos "
            "con 15% de descuento permanente."
        )

    monkeypatch.setattr("agent.nodes.retrieve", _fake_retrieve)
    monkeypatch.setattr("agent.nodes.generate_answer", _fake_generate)

    result = run_agent("¿Cuántos puntos necesito para el nivel Oro?")
    nodes = result["nodes"]
    assert nodes.index("retrieve_knowledge") < nodes.index("generate_response")
    assert "refuse_honestly" not in nodes
    assert "50+" in result["answer"] or "Oro" in result["answer"]
    assert result["n_chunks"] == 1

    saved = load_trace(result["run_id"])
    assert saved is not None
    retrieve_out = next(t for t in saved["trace"] if t["node"] == "retrieve_knowledge")
    assert "loyalty-program" in retrieve_out["output"]["sources"]


def test_eval_no_context_refuses_instead_of_hallucinating(
    fresh_graph, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Eval 3 — retrieve returns [] → refuse node; generate never called."""
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))

    monkeypatch.setattr("agent.nodes.retrieve", lambda _q, **_k: [])

    gen_called = {"n": 0}

    def _gen(*_a, **_k):
        gen_called["n"] += 1
        return "SHOULD NOT HAPPEN"

    monkeypatch.setattr("agent.nodes.generate_answer", _gen)

    result = run_agent("¿Cuál es el menú secreto de Marte?")
    nodes = result["nodes"]
    assert "retrieve_knowledge" in nodes
    assert "refuse_honestly" in nodes
    assert "generate_response" not in nodes
    assert gen_called["n"] == 0
    assert "información suficiente" in result["answer"].lower()
    assert result["error"] == "insufficient_context"

    saved = load_trace(result["run_id"])
    assert saved is not None
    assert saved["nodes"] == nodes
