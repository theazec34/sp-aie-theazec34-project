"""External tools package — MCP client for the LangGraph agent."""

from agent.tools.mcp_client import manage_incidents_via_mcp, query_inventory_via_mcp
from agent.tools.routing import classify_intent, extract_product_query, extract_ticket_id

__all__ = [
    "classify_intent",
    "extract_ticket_id",
    "extract_product_query",
    "manage_incidents_via_mcp",
    "query_inventory_via_mcp",
]
