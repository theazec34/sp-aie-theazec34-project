"""DEPRECATED — direct inventory ORM access from the agent.

Use ``agent.tools.mcp_client.query_inventory_via_mcp`` (MCP ``query_inventory``).
"""

from __future__ import annotations

from agent.tools.contracts import InventoryLookupInput, InventoryLookupOutput


def lookup_inventory_stock(
    payload: InventoryLookupInput,
    *,
    timeout_s: float | None = None,
) -> InventoryLookupOutput:
    raise RuntimeError(
        "DEPRECATED: lookup_inventory_stock was removed. "
        "Use agent.tools.mcp_client.query_inventory_via_mcp "
        "(MCP Server) instead of calling the inventory ORM directly."
    )
