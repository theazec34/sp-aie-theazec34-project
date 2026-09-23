# Progress — Brasaland Digital

## Estado (2026-09-23)
- **`main`:** PRs **#1–#21**, **#23–#37** (LangGraph Part 1 #37).
- **Hito en curso:** LangGraph external tools (Part 2) — `feature/langgraph-external-tools`.
- **Fuera de alcance:** `hito-3` / `3.5`.

## LangGraph Part 2 — external tools
- Tools: `lookup_support_ticket` (IncidentRepository) + `lookup_inventory_stock` (SQLModel)
- Timeout: `AGENT_TOOL_TIMEOUT_S` (default 4s) + `tool_fallback`
- Routing automático: `classify_intent` → rag | ticket | inventory
- Evals: `tests/pipelines/test_agent_tools.py` (+ Part 1 siguen verdes)
- Docs: `docs/agent/langgraph-external-tools.md`

## LangGraph Part 1
- Paquete `services/agent/` · `POST /agent/query` · traces · checkpoint

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#36 |
| LangGraph agent base | #37 |
| LangGraph external tools | este PR |
