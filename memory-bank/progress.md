# Progress — Brasaland Digital

## Estado (2026-10-19)
- **`main`:** PRs **#1–#39** (+ Agent Memory / Guardrails en ramas previas según historial).
- **Hito en curso:** **Hito 9 Parte 1 — RFP intake** en rama `feature/rfp-intake`.
- **Fuera de alcance:** `hito-3` / `3.5`.
- **Estabilidad:** reglas en `AGENTS.md` (base main, un hito→PR→merge, `uv add`, RAG≠memoria).

## RFP Intake Parte 1 (hito actual)
- Grafo LangGraph dedicado: `data/pipelines/rfp_intake/` (convert → classify → orchestrate → workers → synthesize)
- Persistencia SQLModel: `rfp_ticket`, `rfp_metadata`, `rfp_department_section` (Postgres/Supabase; no TinyDB)
- API async: `POST /rfp/tickets` → 202 + `analizando`; poll `GET /rfp/tickets/{id}`
- UI backoffice: `/rfp` (upload + estado en tiempo casi real)
- Semillas: `rfp-requests/brasaland/` (formal / informal / inválido)
- CLI: `scripts/run_rfp_intake.py`
- Docs: `docs/rfp/rfp-intake-part1.md`, BRIEFING completo
- Tests: `tests/pipelines/test_rfp_intake.py`

## Agent Memory
- Episódica KV: Redis opcional + file (`brasaland_agent_memory`) — **nunca** RAG `*_knowledge`
- Docs: `docs/agent/agent-memory.md`

## MCP OAuth tools (#39)
- `mcps/brasaland_tools/` + agente vía `langchain-mcp-adapters`

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#36 |
| LangGraph agent base | #37 |
| LangGraph external tools | #38 |
| MCP OAuth tools | #39 |
| Agent Memory / Guardrails | ramas previas |
| RFP intake Parte 1 | este PR (`feature/rfp-intake`) |
