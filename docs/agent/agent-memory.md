# Brasaland Agent Memory (Hito 8 · Parte 1)

Episodic operational memory for the **Manager support agent**. Extends the
LangGraph agent that already consumes the MCP Server — does not replace it.

## Architecture choice

| Option | Verdict |
|--------|---------|
| Context window only | Rejected — resets every conversation (Felipe’s pain). |
| VectorDB / RAG collection | Rejected for *writes* — company knowledge stays read-only. |
| Knowledge graph | Overkill for ~14 locations + few categories. |
| Fine-tuning | Slow, expensive, no selective forget. |
| **Episodic KV (Redis + file)** | **Chosen** — explicit R/W, TTL, consolidate by location+category, audit trail. Redis already in Compose (Celery); file backend for CI. |

**Namespace:** `brasaland_agent_memory` — never `brasaland_knowledge` / `*_knowledge`.

## Explicit interface

`agent.memory.interface.AgentMemory`:

- `read_relevant(question)` / `format_context`
- `self_evaluate` → `propuesta_memoria` (no write)
- `propose` (pending, max 1) → question in the same reply
- `handle_confirmation` → approve / reject / edit / discard + audit
- Store: `get_memory_store().write|read|consolidate|cleanup`

## Self-evaluation

Single structured pass (`SelfEvalResult`) after relevant turns. Rules aligned with
[`CONTEXT-agent-memory.es.md`](./CONTEXT-agent-memory.es.md); optional LLM refine
via `AGENT_MEMORY_LLM=1` (still one call, not multi-agent).

### Must propose (examples)

1. Vegetable supplier in Medellín delivers Wednesdays (correction).
2. Miami Beach now closes 11pm weekends.
3. Location 7 zero-sales alert was a power outage (known pattern).

### Must NOT propose (examples)

1. “¿Ticket promedio de ayer en Bogotá?” — telemetry one-off.
2. “Gracias, eso resuelve mi duda.” — closing.
3. “Traduce esto al inglés para Ashley.” — one-shot task.

## Confirmation

`classify_confirmation` → labels `approve|reject|edit|ambiguous|topic_change`
(ES/EN). Silence / ambiguity → **discard** (never silent approve). Only one
pending proposal per `session_id`.

## Consolidation & cleanup

- Dedup on write (same location+category+fact).
- `consolidate()` merges by location+category (max 5 facts summarized).
- `cleanup()`: TTL `AGENT_MEMORY_TTL_DAYS` (default 90) + hard cap
  `AGENT_MEMORY_MAX_ENTRIES` (default 200) + soft consolidate at 80% cap.

## Security / poisoning

- Forbidden: payroll, customer PII (policy).
- No write without explicit approve/edit.
- Ambiguous / topic change → discard + audit.
- Audit JSONL: proposal, outcome, user message, timestamp (`data/eval/agent_memory_audit/`).

## Why not multi-agent for self-eval?

Self-eval is a structured classifier on the same turn. A second agent would add
latency and dual-write risk without improving governance (user still confirms).

## API

```http
POST /agent/query
{ "question": "...", "session_id": "mgr-medellin-1" }
```

## Tests & evidence

```bash
uv run pytest tests/pipelines/test_agent_memory.py -q
```

Evidence cycles: [`data/eval/agent_memory_evidence.md`](../../data/eval/agent_memory_evidence.md).
