# Brasaland LangGraph Agent — Part 2/3 (external tools → MCP)

Extends Part 1 with **live operational tools** and automatic routing.
Part 3 migrates those tools to the **MCP Server** (`mcps/brasaland_tools`) via
`langchain-mcp-adapters`. The agent must not call Incidents Manager / inventory
repositories directly.

## Why tools (not more RAG)

Ticket status and stock change in real time. Indexing them in Qdrant would go
stale immediately. Tools are exposed by the company MCP Server (OAuth) and
consumed by the agent as an MCP client.

## Tools (via MCP)

| MCP tool | Agent node | Data source | Auth |
|----------|------------|-------------|------|
| `manage_incidents` | `lookup_ticket` | Incidents Manager (`/api/incidents`, status via `PATCH .../status`) | OAuth scopes `incidents:read` / `incidents:write` |
| `query_inventory` | `lookup_inventory` | Inventory ORM / `GET /inventory/products` | OAuth scope `inventory:read` (writes rejected) |

Client: `services/agent/tools/mcp_client.py`. Timeout: `AGENT_TOOL_TIMEOUT_S`
(default **4s**). Never invent status/stock on failure. See
[`docs/mcp/mcp-oauth-tools.md`](../mcp/mcp-oauth-tools.md).

## Routing

`classify_intent(question)` → `rag` | `ticket` | `inventory` without user hints.

```text
receive_question
  ├─ empty ──► refuse
  ├─ ticket ► lookup_ticket ► answer_from_ticket | tool_fallback
  ├─ inventory ► lookup_inventory ► answer_from_inventory | tool_fallback
  └─ rag ───► retrieve ► generate | refuse
```

## Traces

Each run records nodes + `sources_used` (`rag`, `ticket_tool`, `inventory_tool`).

## Evals

```bash
uv run pytest tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_tools.py -q
```
