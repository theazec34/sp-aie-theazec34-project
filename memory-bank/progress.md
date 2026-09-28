# Progress — Brasaland Digital

## Estado (2026-09-28)
- **`main`:** PRs **#1–#39** (MCP OAuth #39 mergeado). Suite agente/MCP: 28 tests verdes en tip.
- **Hito en curso:** Agent Memory — `feature/agent-memory`.
- **Fuera de alcance:** `hito-3` / `3.5`.
- **Estabilidad:** reglas añadidas en `AGENTS.md` (base main, un hito→PR→merge, uv add, RAG≠memoria, sin rutas dobles).

## Agent Memory (hito actual)
- Episódica KV: Redis opcional + file (`brasaland_agent_memory`) — **nunca** RAG `*_knowledge`
- Interface: `services/agent/memory/` (self-eval, confirm labels, audit, consolidate/TTL)
- Grafo: `resolve_memory_confirm` + `session_id` en `/agent/query`
- Evidencia: ciclos aprobado/rechazado en `data/eval/agent_memory_evidence.md`
- Docs: `docs/agent/agent-memory.md`, `CONTEXT-agent-memory.es.md`

## MCP OAuth tools (#39)
- `mcps/brasaland_tools/` + agente vía `langchain-mcp-adapters`

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#36 |
| LangGraph agent base | #37 |
| LangGraph external tools | #38 |
| MCP OAuth tools | #39 |
| Agent Memory | este PR |
