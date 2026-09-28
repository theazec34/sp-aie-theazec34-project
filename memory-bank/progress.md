# Progress — Brasaland Digital

## Estado (2026-09-28)
- **`main`:** PRs **#1–#38** (LangGraph Part 2 #38).
- **Hito en curso:** MCP OAuth company tools — `feature/mcp-oauth-tools`.
- **Fuera de alcance:** `hito-3` / `3.5`.

## MCP OAuth tools (hito actual)
- Servidor en `mcps/brasaland_tools/` (FastMCP + **mcpauth**, Streamable HTTP `:8100`)
- Tools: `manage_incidents` (create/get/list/`update_status` → `PATCH /api/incidents/{id}/status`), `query_inventory` (read-only), `mutate_inventory` (reject `INVENTORY_WRITE_FORBIDDEN`)
- Scopes: `brasaland:tools`, `incidents:read|write`, `inventory:read`
- Agente migrado: `services/agent/tools/mcp_client.py` (`langchain-mcp-adapters`); paths directos deprecados
- Tests: `tests/pipelines/test_mcp_server.py` + agent tools actualizados
- Docs: `docs/mcp/mcp-oauth-tools.md`

## LangGraph Part 2 — external tools (#38)
- Tools + routing + fallback (ahora vía MCP en este hito)

## LangGraph Part 1 (#37)
- Paquete `services/agent/` · `POST /agent/query` · traces · checkpoint

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#36 |
| LangGraph agent base | #37 |
| LangGraph external tools | #38 |
| MCP OAuth tools | este PR |
