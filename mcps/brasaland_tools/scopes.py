"""Least-privilege OAuth scopes for Brasaland MCP tools."""

from __future__ import annotations

# Baseline scope required to reach the MCP HTTP surface (list/call tools).
SCOPE_TOOLS = "brasaland:tools"

# Incidents Manager
SCOPE_INCIDENTS_READ = "incidents:read"
SCOPE_INCIDENTS_WRITE = "incidents:write"

# Inventory — read only by design (no write scope is ever granted for inventory).
SCOPE_INVENTORY_READ = "inventory:read"

ALL_SCOPES: list[str] = [
    SCOPE_TOOLS,
    SCOPE_INCIDENTS_READ,
    SCOPE_INCIDENTS_WRITE,
    SCOPE_INVENTORY_READ,
]

TOOL_REQUIRED_SCOPES: dict[str, list[str]] = {
    "manage_incidents": [SCOPE_TOOLS, SCOPE_INCIDENTS_READ],
    "query_inventory": [SCOPE_TOOLS, SCOPE_INVENTORY_READ],
    "mutate_inventory": [SCOPE_TOOLS, SCOPE_INVENTORY_READ],
}

# Write operations on incidents need the write scope in addition to read.
INCIDENT_WRITE_SCOPES = [SCOPE_TOOLS, SCOPE_INCIDENTS_WRITE]
