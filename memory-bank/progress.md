# Progress — Brasaland Digital

## Estado (2026-09-23)
- **`main`:** PRs **#1–#21**, **#23–#36** (RAG #35, Celery DEV-55 #36).
- **Hito en curso:** LangGraph agent base — rama `feature/langgraph-agent-base`.
- **Fuera de alcance:** `hito-3` / `3.5`.

## LangGraph agent (Part 1)
- Paquete: `services/agent/` (state, nodes, graph, tracing, router)
- Nodos: `receive_question` → `retrieve_knowledge` → `generate_response` | `refuse_honestly`
- Condicionales: pregunta vacía / sin contexto → refusal (sin alucinar)
- Checkpoint: `MemorySaver` por `run_id`
- Traces: `data/eval/agent_traces/`
- API: `POST /agent/query`, `GET /agent/traces/{run_id}`
- Evals: `tests/pipelines/test_agent_graph.py` (≥3) + RAG tests siguen en verde
- Diseño: `docs/agent/langgraph-agent-base.md`

## Hitos en main
| Área | PR |
|------|-----|
| Producto base + Docker + perf/cache | #1–#21 |
| Telemetría | #23–#26 |
| Pipeline | #27–#29 |
| Nightly | #30 |
| Sentimiento | #31 |
| Ventas ML | #32–#33 |
| Docs review | #34 |
| RAG knowledge | #35 |
| Celery DEV-55 | #36 |
| LangGraph agent base | este PR |
