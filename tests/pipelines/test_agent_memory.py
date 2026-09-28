"""Agent memory evals — propose / confirm / reject / no RAG writes."""

from __future__ import annotations

import json
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
from agent.memory.audit import read_audit  # noqa: E402
from agent.memory.confirm import classify_confirmation  # noqa: E402
from agent.memory.interface import get_agent_memory  # noqa: E402
from agent.memory.pending import clear_pending, get_pending  # noqa: E402
from agent.memory.self_eval import evaluate_for_memory  # noqa: E402
from agent.memory.store import (  # noqa: E402
    MEMORY_NAMESPACE,
    FileMemoryStore,
    get_memory_store,
    reset_memory_store_for_tests,
)


@pytest.fixture()
def mem_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGENT_MEMORY_BACKEND", "file")
    monkeypatch.setenv("AGENT_MEMORY_DIR", str(tmp_path / "mem"))
    monkeypatch.setenv("AGENT_MEMORY_AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setenv("MCP_INPROCESS", "1")
    monkeypatch.setenv("MCP_AUTH_MODE", "dev")
    monkeypatch.setenv("MCP_DATA_MODE", "direct")
    reset_memory_store_for_tests()
    get_compiled_graph.cache_clear()
    yield tmp_path
    reset_memory_store_for_tests()
    get_compiled_graph.cache_clear()


def test_namespace_is_not_rag():
    from agent.memory.store import _assert_not_rag

    assert MEMORY_NAMESPACE == "brasaland_agent_memory"
    assert not MEMORY_NAMESPACE.endswith("_knowledge")
    with pytest.raises(RuntimeError, match="RAG"):
        _assert_not_rag("brasaland_knowledge")
    with pytest.raises(RuntimeError, match="RAG"):
        _assert_not_rag("company_knowledge")


def test_self_eval_memorable_examples():
    m1 = evaluate_for_memory(
        "En realidad el proveedor de vegetales en Medellín entrega los miércoles, "
        "no los martes como dijiste antes."
    )
    assert m1.memorable and m1.propuesta_memoria is not None

    m2 = evaluate_for_memory(
        "La location de Miami Beach ahora cierra a las 11pm los fines de semana, "
        "cambió el mes pasado."
    )
    assert m2.memorable and m2.propuesta_memoria is not None

    m3 = evaluate_for_memory(
        "Esa alerta de ventas en cero en la location 7 fue porque hubo un apagón, "
        "no fue un error del POS — ya pasó dos veces este mes."
    )
    assert m3.memorable and m3.propuesta_memoria is not None


def test_self_eval_non_memorable_examples():
    assert evaluate_for_memory("¿Cuál fue el ticket promedio de ayer en Bogotá?").memorable is False
    assert evaluate_for_memory("Gracias, eso resuelve mi duda.").memorable is False
    assert evaluate_for_memory(
        "¿Puedes traducir esto al inglés para el reporte de Ashley?"
    ).memorable is False


def test_forbidden_payroll_never_proposed():
    r = evaluate_for_memory(
        "En realidad el salario de Carlos en Medellín es 5 millones, corrige eso."
    )
    assert r.memorable is False
    assert r.discard_reason and "forbidden" in r.discard_reason


def test_confirm_classifier_labels():
    assert classify_confirmation("sí").label == "approve"
    assert classify_confirmation("yes").label == "approve"
    assert classify_confirmation("no").label == "reject"
    assert classify_confirmation("editar: cierra a las 10pm").label == "edit"
    assert classify_confirmation("edit: closes at 10pm").edited_fact == "closes at 10pm"
    assert classify_confirmation("¿Cuál es el stock de lomo?").label == "topic_change"
    assert classify_confirmation("tal vez mañana vemos").label == "ambiguous"


def test_cycle_approved_then_reflected(mem_env):
    """Evidence cycle A — approve → fact available on next turn."""
    sid = "sess-approve-1"
    correction = (
        "En realidad el proveedor de vegetales en Medellín entrega los miércoles, "
        "no los martes como dijiste antes."
    )
    # Force a non-tool path with memory proposal by mocking generate/retrieve
    import agent.nodes as nodes

    def _fake_retrieve(_q, **_k):
        return [
            {
                "text": "Horarios estándar documentados.",
                "source_document": "ops",
                "section": "x",
                "company": "brasaland",
                "language": "es",
                "chunk_index": 0,
            }
        ]

    monkey = pytest.MonkeyPatch()
    monkey.setattr(nodes, "retrieve", _fake_retrieve)
    monkey.setattr(nodes, "generate_answer", lambda q, c: "Entendido, tomo nota de tu corrección.")

    r1 = run_agent(correction, session_id=sid)
    assert r1.get("memory_proposal") is not None
    assert "recuerde" in r1["answer"].lower() or "remember" in r1["answer"].lower()
    assert get_pending(sid) is not None
    # Must NOT have written yet
    assert get_memory_store().list_all() == []

    r2 = run_agent("sí", session_id=sid)
    assert r2.get("memory_decision") == "approved"
    assert get_pending(sid) is None
    entries = get_memory_store().list_all()
    assert len(entries) == 1
    assert "miércoles" in entries[0].fact.lower() or "miercoles" in entries[0].fact.lower()

    audits = read_audit(session_id=sid)
    assert any(a.outcome.value == "approved" for a in audits)

    # Next interaction surfaces memory
    r3 = run_agent("¿Qué día entrega vegetales en Medellín?", session_id=sid)
    assert "memory" in r3["sources_used"] or "miércoles" in r3["answer"].lower() or (
        get_agent_memory().read_relevant("Medellín vegetales")
    )
    monkey.undo()


def test_cycle_rejected_memory_unchanged(mem_env):
    """Evidence cycle B — reject → store stays empty."""
    sid = "sess-reject-1"
    import agent.nodes as nodes

    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        nodes,
        "retrieve",
        lambda _q, **_k: [
            {
                "text": "doc",
                "source_document": "ops",
                "section": "x",
                "company": "brasaland",
                "language": "es",
                "chunk_index": 0,
            }
        ],
    )
    monkey.setattr(nodes, "generate_answer", lambda q, c: "Ok.")

    msg = (
        "La location de Miami Beach ahora cierra a las 11pm los fines de semana, "
        "cambió el mes pasado."
    )
    r1 = run_agent(msg, session_id=sid)
    assert r1.get("memory_proposal") is not None
    r2 = run_agent("no", session_id=sid)
    assert r2.get("memory_decision") == "rejected"
    assert get_memory_store().list_all() == []
    audits = read_audit(session_id=sid)
    assert any(a.outcome.value == "rejected" for a in audits)
    monkey.undo()


def test_ambiguous_discards_not_approve(mem_env):
    sid = "sess-amb-1"
    mem = get_agent_memory()
    from agent.memory.models import MemoryCategory, MemoryProposal
    from agent.memory.pending import set_pending
    from agent.memory.models import PendingProposal

    prop = MemoryProposal(
        fact="test fact",
        reason="unit",
        location="miami",
        category=MemoryCategory.HOURS,
        source_message="x",
    )
    set_pending(PendingProposal(session_id=sid, proposal=prop))
    ack, outcome, conf = mem.handle_confirmation(sid, "mmm no sé", user_id="u1")
    assert outcome is not None
    assert outcome.value == "discarded_ambiguous"
    assert get_pending(sid) is None
    assert get_memory_store().list_all() == []


def test_only_one_pending_proposal(mem_env):
    sid = "sess-one-1"
    mem = get_agent_memory()
    from agent.memory.models import MemoryCategory, MemoryProposal

    p1 = MemoryProposal(
        fact="fact1", reason="r", location="miami",
        category=MemoryCategory.HOURS, source_message="a",
    )
    p2 = MemoryProposal(
        fact="fact2", reason="r", location="miami",
        category=MemoryCategory.HOURS, source_message="b",
    )
    assert mem.propose(sid, p1) is not None
    assert mem.propose(sid, p2) is None  # blocked while pending
    clear_pending(sid)


def test_consolidate_and_cleanup(mem_env):
    store = get_memory_store()
    from agent.memory.models import MemoryCategory, MemoryEntry

    for i in range(3):
        store.write(
            MemoryEntry(
                fact=f"Medellín supplier note {i}",
                location="medellin",
                category=MemoryCategory.SUPPLIER,
            )
        )
    removed = store.consolidate()
    assert removed >= 2
    assert len(store.list_all()) == 1
    stats = store.cleanup()
    assert "expired" in stats
