# Brasaland MCP Server — OAuth company tools

Independent **Model Context Protocol** server that exposes Incidents Manager and
read-only inventory capabilities. The LangGraph agent consumes it as an MCP
client (`langchain-mcp-adapters`); it no longer calls those backends directly.

## Design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | **Streamable HTTP** (`/mcp`) | Multiple remote clients (agent, Playground, partners); OAuth Bearer works over HTTP. `stdio` is local-only and awkward for OAuth. |
| Auth | **mcpauth** resource server | Spec-aligned OAuth 2.1 / OIDC; Protected Resource Metadata; `required_scopes`. **Not** FastMCP built-in auth. |
| Inventory | Read-only + explicit reject | `query_inventory` reads; `mutate_inventory` always returns `INVENTORY_WRITE_FORBIDDEN`. |
| Discovery | Tool names, descriptions, JSON schemas + PRM | External agents can understand capabilities without reading source. |

## Layout

```text
mcps/brasaland_tools/     # MCP server (NOT under services/)
  server.py               # FastMCP tools + Starlette app
  auth.py                 # mcpauth + dev JWT / OIDC
  backend.py              # HTTP or in-process Incidents + Inventory
  scopes.py / errors.py
services/agent/tools/mcp_client.py   # langchain-mcp-adapters client
```

## Scopes (least privilege)

| Scope | Purpose |
|-------|---------|
| `brasaland:tools` | Baseline — required to list/call any tool |
| `incidents:read` | get / list incidents |
| `incidents:write` | create + `update_status` |
| `inventory:read` | query stock (no write scope exists) |

## Tools

### `manage_incidents`

Actions: `create` | `get` | `list` | `update_status`.

Status changes **must** use the lifecycle endpoint
`PATCH /api/incidents/{id}/status` (never a generic incident PATCH). Field names
and enums match the Incidents Manager API exactly.

### `query_inventory`

Read-only. Returns `id`, `name`, `sku`, `unit`, `category`, `country`,
`current_stock` (same as `GET /inventory/products`).

### `mutate_inventory`

Always rejected with `error_code=INVENTORY_WRITE_FORBIDDEN` (HTTP 403 semantics).

## Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `AUTH_MISSING_TOKEN` / `AUTH_INVALID_TOKEN` | 401 | Authentication |
| `AUTHZ_INSUFFICIENT_SCOPE` | 403 | Authorization / scopes |
| `VALIDATION_*` | 400 | Bad tool input |
| `INCIDENT_NOT_FOUND` / `INVENTORY_NOT_FOUND` | 404 | Missing entity |
| `INCIDENT_INVALID_TRANSITION` | 400 | Lifecycle violation |
| `INVENTORY_WRITE_FORBIDDEN` | 403 | Explicit write reject |
| `BACKEND_*` | 502/503 | Upstream failure |

Each tool invocation logs: **client**, **tool**, **result**.

## Run the server

```bash
# Dev (HS256 JWT + in-process data)
export MCP_AUTH_MODE=dev
export MCP_DATA_MODE=direct
export MCP_PORT=8100
uv run python -m mcps.brasaland_tools
# or: uv run brasaland-mcp
```

Mint a token for MCP Playground / agents:

```bash
curl -s -X POST http://127.0.0.1:8100/dev/token \
  -H 'content-type: application/json' \
  -d '{"client_id":"playground","scope":"brasaland:tools incidents:read incidents:write inventory:read"}'
```

### MCP Playground (Codespaces)

1. Start the server on port `8100`.
2. Forward the port and set visibility to **public**.
3. Paste the forwarded URL + `/mcp` into MCP Playground (not `localhost`).
4. Use `Authorization: Bearer <access_token>` from `/dev/token`.
5. Run one workflow per tool; confirm `mutate_inventory` fails with
   `INVENTORY_WRITE_FORBIDDEN`.

### OIDC production mode

```bash
export MCP_AUTH_MODE=oidc
export MCP_AUTH_ISSUER=https://your-oidc-issuer
export MCP_AUTH_AUDIENCE=https://mcp.brasaland.local
export MCP_DATA_MODE=http
export MCP_API_BASE_URL=http://api:8000
```

## Agent migration

- Nodes `lookup_ticket` / `lookup_inventory` call `manage_incidents_via_mcp` /
  `query_inventory_via_mcp` only.
- Former direct tools raise `RuntimeError("DEPRECATED...")` if imported.
- Routing RAG ↔ tools is unchanged; only the tool transport is MCP.

```bash
uv run pytest tests/pipelines/test_mcp_server.py tests/pipelines/test_agent_tools.py -q
```
