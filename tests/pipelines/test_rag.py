"""Unit tests for Brasaland RAG retrieve/query (mocked Qdrant + generation)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from data.pipelines import rag as rag_pipeline


class _FakeHit(SimpleNamespace):
    pass


def test_retrieve_filters_below_min_score(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_hits = [
        _FakeHit(id=1, score=0.9, payload={"text": "a", "source_document": "loyalty-program"}),
        _FakeHit(id=2, score=0.5, payload={"text": "b", "source_document": "waste-protocol"}),
    ]
    monkeypatch.setattr(rag_pipeline, "_embedding_provider", lambda: "fastembed")
    monkeypatch.setattr(rag_pipeline, "embed", lambda _q: [0.1, 0.2, 0.3])
    monkeypatch.setattr(rag_pipeline, "_search", lambda **_kw: fake_hits)

    result = rag_pipeline.retrieve("test", k=5, min_score=0.75)

    assert len(result) == 1
    assert result[0]["text"] == "a"
    assert result[0]["score"] == 0.9


def test_retrieve_may_return_fewer_than_k(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_hits = [
        _FakeHit(id=1, score=0.8, payload={"text": "only"}),
    ]
    monkeypatch.setattr(rag_pipeline, "_embedding_provider", lambda: "fastembed")
    monkeypatch.setattr(rag_pipeline, "embed", lambda _q: [0.0])
    monkeypatch.setattr(rag_pipeline, "_search", lambda **_kw: fake_hits)

    result = rag_pipeline.retrieve("q", k=5, min_score=0.3)

    assert len(result) == 1
    assert len(result) < 5


def test_query_returns_llm_output_not_raw_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rag_pipeline,
        "retrieve",
        lambda _q: [{"text": "chunk crudo del manual", "source_document": "loyalty-program"}],
    )
    monkeypatch.setattr(
        rag_pipeline,
        "generate_answer",
        lambda _q, _ctx: "Respuesta de vendedor entrenado",
    )

    answer = rag_pipeline.query("¿Cuántos puntos para Oro?")

    assert answer == "Respuesta de vendedor entrenado"
    assert "chunk crudo" not in answer


def test_query_honest_refusal_when_no_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_pipeline, "retrieve", lambda _q: [])
    monkeypatch.setenv("GENERATION_PROVIDER", "grounded")

    answer = rag_pipeline.query("¿Cuál es el menú secreto de Marte?")

    assert "información suficiente" in answer.lower()


def test_generate_answer_composable_without_retrieve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GENERATION_PROVIDER", "grounded")
    context = [
        {
            "text": "Oro (50+ puntos): 15% de descuento permanente.",
            "source_document": "loyalty-program",
            "section": "Niveles",
        }
    ]
    answer = rag_pipeline.generate_answer("¿Nivel Oro?", context)
    assert "50+" in answer or "15%" in answer
    assert "manuales" in answer.lower() or "Oro" in answer


def test_retrieve_keyword_fallback_when_vector_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_pipeline, "embed", lambda _q: [0.0])
    monkeypatch.setattr(rag_pipeline, "_search", lambda **_kw: [])
    monkeypatch.setattr(
        rag_pipeline,
        "_scroll_all_payloads",
        lambda *_a, **_k: [
            {
                "text": "Brasa Points es el programa de fidelización de Brasaland.",
                "source_document": "loyalty-program",
            },
            {
                "text": "Protocolo de desperdicio y merma en cocina.",
                "source_document": "waste-protocol",
            },
        ],
    )
    result = rag_pipeline.retrieve("Que son los Brasa Points?", k=3, min_score=0.9)
    assert result
    assert "Brasa Points" in result[0]["text"]


def test_retrieve_hash_prefers_keyword_over_misleading_vector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setattr(
        rag_pipeline,
        "_search",
        lambda **_kw: [
            type(
                "H",
                (),
                {
                    "score": 0.9,
                    "payload": {
                        "text": "Pedidos de emergencia con recargo 8%.",
                        "source_document": "supplier-ordering",
                    },
                },
            )()
        ],
    )
    monkeypatch.setattr(
        rag_pipeline,
        "_scroll_all_payloads",
        lambda *_a, **_k: [
            {
                "text": "Niveles del programa: Plata, Oro y Platino de fidelización.",
                "source_document": "loyalty-program",
            },
            {
                "text": "Pedidos de emergencia con recargo 8%.",
                "source_document": "supplier-ordering",
            },
        ],
    )
    result = rag_pipeline.retrieve("niveles de fidelización", k=3)
    assert result
    assert "loyalty" in result[0].get("source_document", "")


def test_generate_defaults_to_grounded_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GENERATION_PROVIDER", "openai")
    monkeypatch.delenv("GENERATION_USE_LLM", raising=False)
    monkeypatch.delenv("GENERATION_API_KEY", raising=False)
    monkeypatch.delenv("GENERATION_BASE_URL", raising=False)
    monkeypatch.delenv("GENERATION_MODEL_ID", raising=False)

    def _boom(*_a, **_k):
        raise AssertionError("LLM must not run without credentials")

    monkeypatch.setattr(rag_pipeline, "_openai_generate", _boom)
    answer = rag_pipeline.generate_answer(
        "¿Qué son Brasa Points?",
        [
            {
                "text": "Brasa Points es el programa de fidelización.",
                "source_document": "loyalty-program",
            }
        ],
    )
    assert "Brasa Points" in answer
    assert "manuales" in answer.lower()


def test_offscope_menu_redirect() -> None:
    msg = rag_pipeline.query("cual es el menu?")
    assert "carta completa" in msg.lower() or "alérgenos" in msg.lower()
