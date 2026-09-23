# Brasaland LangGraph Agent — Part 2 (external tools)

Extends Part 1 with **live operational tools** and automatic routing.

## Why tools (not more RAG)

Ticket status and stock change in real time. Indexing them in Qdrant would go
stale immediately. Tools call the existing incident / inventory services.

## Tools

| Tool | Contract | Data source | Auth |
|------|----------|-------------|------|
| `lookup_support_ticket` | `TicketLookupInput` → `TicketLookupOutput` | `IncidentRepository` (same TinyDB as `GET /api/incidents`) | Incidents GET is **public** (no JWT) |
| `lookup_inventory_stock` | `InventoryLookupInput` → `InventoryLookupOutput` | SQLModel inventory + `stock_map_for_ids` (same as `GET /inventory/products`) | HTTP inventory requires JWT; tool uses **in-process** service layer |

Both are **read-only**, have an explicit timeout (`AGENT_TOOL_TIMEOUT_S`, default **4s**), and never invent status/stock on failure.

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
