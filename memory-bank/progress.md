# Progress — Brasaland Digital

## Estado (2026-09-30)
- **`main`:** PRs **#1–#40** (Agent Memory #40 mergeado).
- **Hito en curso:** Agent Guardrails — `feature/agent-guardrails`.
- **Fuera de alcance:** `hito-3` / `3.5`.

## Agent Guardrails (hito actual · Hito 8 Parte 2)
- Paquete `services/agent/guardrails/` — system prompt seguro, input/output guards, aislamiento RAG/MCP
- Fallos tipados: `structural` | `content` | `security`
- Observabilidad: logs + `GET /agent/guardrails/summary`
- Tests deterministas: `tests/pipelines/test_agent_guardrails.py`
- Docs: `docs/agent/agent-guardrails.md`, `CONTEXT-agent-guardrails.es.md`

## Agent Memory (#40)
- Episódica `brasaland_agent_memory` + confirmación explícita

## MCP OAuth tools (#39)
- `mcps/brasaland_tools/` + agente vía MCP

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#38 |
| MCP OAuth tools | #39 |
| Agent Memory | #40 |
| Agent Guardrails | este PR |
