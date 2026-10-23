"""Brasaland RAG retrieval + generation — Phase 2.

Public API:
  - ``retrieve(query, *, k, min_score) -> list[dict]``
  - ``generate_answer(question, context) -> str``
  - ``query(question) -> str``  (= retrieve + generate_answer)

Never returns raw Qdrant hits to HTTP/UI callers of ``query()``.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from data.process.rag import (
    _embedding_provider,
    _load_env,
    collection_name,
    embed,
    get_qdrant_client,
)

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
# Cosine scores on multilingual MiniLM for this short ES corpus typically
# land ~0.35–0.85 for on-topic hits and <0.25 for noise. 0.32 keeps
# loyalty/allergen questions alive while dropping off-topic noise.
DEFAULT_MIN_SCORE = 0.32

COMPANY_VOICE = (
    "Eres un vendedor/asesor de operaciones de Brasaland entrenado. "
    "Respondes a gerentes de local, marketing y personal de piso con "
    "seguridad y claridad, como lo haría un vendedor entrenado."
)

BUSINESS_RULES = (
    "Usa ÚNICAMENTE el contexto recuperado de los manuales oficiales. "
    "No inventes políticas, precios, kg, porcentajes ni alérgenos. "
    "Si el contexto no alcanza para responder, dilo explícitamente. "
    "Ante alérgenos, NUNCA digas 'sin riesgo' ni 'cero riesgo' de "
    "contaminación cruzada — sigue la redacción del manual. "
    "Mantén montos en COP y USD exactamente como aparecen; no conviertas "
    "moneda. Responde en el mismo idioma que la pregunta (español)."
)

REFUSAL_ES = (
    "No tengo información suficiente en los manuales oficiales de Brasaland "
    "para responder esa pregunta con seguridad. Te recomiendo consultar el "
    "documento fuente correspondiente o escalar a Operaciones."
)


def _default_min_score() -> float:
    raw = os.getenv("RAG_MIN_SCORE", "").strip()
    if raw:
        return float(raw)
    # Hash embeddings are not semantic — keep a low bar; keyword fallback covers misses.
    if _embedding_provider() in {"hash", "offline", "local"}:
        return 0.05
    return DEFAULT_MIN_SCORE


def _default_top_k() -> int:
    raw = os.getenv("RAG_TOP_K", "").strip()
    return int(raw) if raw else DEFAULT_TOP_K


def _tokenize(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-záéíóúñü0-9]+", (text or "").lower())
        if len(t) >= 3
    }


def _keyword_score(query: str, text: str) -> float:
    q, d = _tokenize(query), _tokenize(text)
    if not q or not d:
        return 0.0
    return len(q & d) / float(len(q))


def _scroll_all_payloads(collection: str, *, limit: int = 200) -> list[dict[str, Any]]:
    """Read payloads from the collection for keyword fallback (small demo corpus)."""
    client = get_qdrant_client()
    out: list[dict[str, Any]] = []
    next_offset = None
    while len(out) < limit:
        kwargs: dict[str, Any] = {
            "collection_name": collection,
            "limit": min(64, limit - len(out)),
            "with_payload": True,
            "with_vectors": False,
        }
        if next_offset is not None:
            kwargs["offset"] = next_offset
        records, next_offset = client.scroll(**kwargs)
        for rec in records:
            payload = dict(getattr(rec, "payload", None) or {})
            if payload.get("text"):
                out.append(payload)
        if next_offset is None:
            break
    return out


def _keyword_retrieve(query: str, *, k: int, collection: str) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for payload in _scroll_all_payloads(collection):
        score = _keyword_score(query, str(payload.get("text") or ""))
        # Boost if source filename tokens match (loyalty, allergen, waste…)
        src = str(payload.get("source_document") or "")
        score = max(score, _keyword_score(query, src) * 0.8)
        if score <= 0:
            continue
        row = dict(payload)
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:k]]


def _generation_settings() -> tuple[str, str, str]:
    _load_env()
    base_url = os.getenv("GENERATION_BASE_URL", "").strip()
    api_key = os.getenv("GENERATION_API_KEY", "").strip()
    model_id = os.getenv("GENERATION_MODEL_ID", "").strip()
    if not base_url:
        base_url = os.getenv("EMBEDDING_BASE_URL", "").strip()
    if not api_key:
        api_key = os.getenv("EMBEDDING_API_KEY", "").strip() or "not-needed"
    embedding_id = os.getenv("EMBEDDING_MODEL_ID", "").strip()
    if embedding_id and model_id and embedding_id == model_id:
        raise RuntimeError(
            "GENERATION_MODEL_ID must differ from EMBEDDING_MODEL_ID"
        )
    return base_url, api_key, model_id


def generation_provider() -> str:
    """openai (4Geeks chat) | grounded (offline fallback from retrieved text)."""
    explicit = os.getenv("GENERATION_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    _, _, model_id = _generation_settings()
    base_url = os.getenv("GENERATION_BASE_URL", "").strip() or os.getenv(
        "EMBEDDING_BASE_URL", ""
    ).strip()
    if base_url and model_id:
        return "openai"
    return "grounded"


def _search(
    *,
    vector: list[float],
    k: int,
    collection: str,
) -> list[Any]:
    """Thin Qdrant search wrapper — mocked in unit tests."""
    client = get_qdrant_client()
    # qdrant-client ≥1.12 prefers query_points
    if hasattr(client, "query_points"):
        result = client.query_points(
            collection_name=collection,
            query=vector,
            limit=k,
            with_payload=True,
        )
        return list(result.points)
    return list(
        client.search(
            collection_name=collection,
            query_vector=vector,
            limit=k,
            with_payload=True,
        )
    )


def retrieve(
    query: str,
    *,
    k: int = DEFAULT_TOP_K,
    min_score: float | None = None,
    collection: str | None = None,
) -> list[dict[str, Any]]:
    """Embed query, search Qdrant, filter by ``min_score``.

    Returns payload dicts (plus optional ``score`` for logging). May return
    fewer than ``k`` results — never forces a fixed hit count.
    """
    if not query or not query.strip():
        raise ValueError("retrieve() requires a non-empty query")

    _load_env()
    threshold = _default_min_score() if min_score is None else min_score
    coll = collection or collection_name()
    vector = embed(query.strip())
    hits = _search(vector=vector, k=k, collection=coll)

    payloads: list[dict[str, Any]] = []
    for hit in hits:
        score = float(getattr(hit, "score", 0.0) or 0.0)
        if score < threshold:
            continue
        payload = dict(getattr(hit, "payload", None) or {})
        payload["score"] = score
        payloads.append(payload)

    if payloads:
        return payloads

    # Hash / cold collection: vector search often empty → keyword fallback.
    logger.info("vector retrieve empty for %r — trying keyword fallback", query[:80])
    return _keyword_retrieve(query.strip(), k=k, collection=coll)


def assemble_context(chunks: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for chunk in chunks:
        source = chunk.get("source_document", "?")
        section = chunk.get("section", "?")
        text = chunk.get("text", "")
        blocks.append(f"[{source} / {section}]\n{text}")
    return "\n\n---\n\n".join(blocks)


def refusal_message() -> str:
    return REFUSAL_ES


def _grounded_generate(question: str, context: list[dict[str, Any]]) -> str:
    """Offline grounded answer from retrieved chunks only (no external LLM).

    Used when GENERATION_* portal credentials are not configured. Production
    should set GENERATION_PROVIDER=openai with the 4Geeks chat model.
    """
    if not context:
        return refusal_message()
    body = " ".join(c.get("text", "") for c in context)
    # Prefer the highest-scoring chunk as lead, keep remaining as support.
    lead = context[0].get("text", "").strip()
    sources = sorted(
        {str(c.get("source_document", "")) for c in context if c.get("source_document")}
    )
    source_note = ", ".join(sources) if sources else "manuales Brasaland"
    # Allergen safety: never invent "sin riesgo"
    answer = (
        f"Según los manuales oficiales ({source_note}): {lead}"
    )
    if len(context) > 1:
        extra = context[1].get("text", "").strip()
        if extra and extra not in answer:
            answer = f"{answer} Además: {extra}"
    # Cap length for UI readability
    if len(answer) > 1200:
        answer = answer[:1197] + "..."
    # Faithfulness: do not add numbers not in context — body already from chunks
    _ = (question, body)
    return answer


def _openai_generate(question: str, context: list[dict[str, Any]]) -> str:
    from openai import OpenAI

    base_url, api_key, model_id = _generation_settings()
    if not base_url or not model_id:
        raise RuntimeError(
            "GENERATION_BASE_URL and GENERATION_MODEL_ID required for "
            "GENERATION_PROVIDER=openai"
        )
    # 18s: razonar con LLM; si el gateway no llega, grounded hace fallback
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=18.0)
    if not context:
        user = (
            f"No se recuperó contexto relevante de los manuales.\n\n"
            f"Pregunta: {question}\n\n"
            f"Responde honestamente que no tienes información suficiente."
        )
    else:
        ctx = assemble_context(context)
        user = (
            f"Contexto de los manuales oficiales:\n---\n{ctx}\n---\n\n"
            f"Pregunta: {question}"
        )
    messages = [
        {"role": "system", "content": f"{COMPANY_VOICE}\n\n{BUSINESS_RULES}"},
        {"role": "user", "content": user},
    ]
    delays = (1.0, 2.0)
    last_exc: BaseException | None = None
    for attempt in range(len(delays) + 1):
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            return content.strip() or refusal_message()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= len(delays):
                break
            logger.warning("generation failed attempt %s: %s", attempt + 1, exc)
            time.sleep(delays[attempt])
    assert last_exc is not None
    raise last_exc


def _llm_credentials_ready() -> bool:
    base_url, api_key, model_id = _generation_settings()
    if not base_url or not model_id:
        return False
    key = (api_key or "").strip()
    return bool(key) and key.lower() not in {"not-needed", "changeme", "xxx"}


def _should_use_llm() -> bool:
    """Use LLM when credentials exist, unless GENERATION_USE_LLM=0."""
    flag = os.getenv("GENERATION_USE_LLM", "").strip().lower()
    if flag in {"0", "false", "no"}:
        return False
    if flag in {"1", "true", "yes"}:
        return True
    # Auto: si hay API key de 4Geeks/OpenAI → razonar con LLM
    return generation_provider() == "openai" and _llm_credentials_ready()


_OFFSCOPE_MENU = re.compile(
    r"("
    r"cu[aá]l\s+es\s+el\s+men[uú]\s*\??\s*$|"
    r"carta\s+completa|todo\s+el\s+men[uú]|"
    r"qu[eé]\s+hay\s+en\s+la\s+carta"
    r")",
    re.IGNORECASE,
)


def _offscope_message(question: str) -> str | None:
    """Honest redirect when the manuals cannot answer the ask."""
    q = question or ""
    if _OFFSCOPE_MENU.search(q):
        return (
            "BrasAI no tiene la carta completa del restaurante: solo el manual "
            "de alérgenos por plato. Prueba p.ej. «¿Qué alérgenos tiene la "
            "Costilla BBQ?» o «¿La paella tiene gluten?». Para stock/proveedores "
            "usa el Agente soporte."
        )
    return None


def generate_answer(question: str, context: list[dict[str, Any]]) -> str:
    """Generation step only — reusable by agents without re-running retrieve."""
    if not question or not question.strip():
        raise ValueError("generate_answer() requires a non-empty question")
    _load_env()
    provider = generation_provider()
    prefer_llm = _should_use_llm()
    if not context:
        if provider == "openai" and prefer_llm:
            try:
                return _openai_generate(question.strip(), [])
            except Exception as exc:  # noqa: BLE001
                logger.warning("openai generation failed, grounded fallback: %s", exc)
                return refusal_message()
        return refusal_message()
    if provider == "openai" and prefer_llm:
        try:
            return _openai_generate(question.strip(), context)
        except Exception as exc:  # noqa: BLE001
            logger.warning("openai generation failed, grounded fallback: %s", exc)
            return _grounded_generate(question.strip(), context)
    if provider in {"grounded", "openai"}:
        return _grounded_generate(question.strip(), context)
    raise RuntimeError(f"Unknown GENERATION_PROVIDER={provider!r}")


def query(question: str) -> str:
    """Pipeline entry: retrieve → generate_answer. Returns answer string only."""
    if not question or not question.strip():
        raise ValueError("query() requiere una pregunta no vacía")
    q = question.strip()
    off = _offscope_message(q)
    if off:
        return off

    chunks = retrieve(q)
    if not chunks:
        return generate_answer(q, [])

    # Filtrar ruido del keyword fallback. Si no hay score (tests/mocks), aceptar.
    scored = [c for c in chunks if "score" in c]
    if scored:
        strong = [c for c in scored if float(c.get("score") or 0) >= 0.34]
        use = strong or scored[:1]
        if float(use[0].get("score") or 0) < 0.2:
            return refusal_message()
    else:
        use = chunks

    clean = [{k: v for k, v in c.items() if k != "score"} for c in use]
    return generate_answer(q, clean)
