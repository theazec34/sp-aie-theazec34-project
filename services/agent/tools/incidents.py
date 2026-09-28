"""DEPRECATED — direct Incidents Manager access from the agent.

The LangGraph agent must call the Brasaland MCP Server
(``manage_incidents`` via ``agent.tools.mcp_client``). This module is kept
only so older imports fail loudly instead of silently reintroducing a second
path to the Incidents Manager.
"""

from __future__ import annotations

from agent.tools.contracts import TicketLookupInput, TicketLookupOutput


def lookup_support_ticket(
    payload: TicketLookupInput,
    *,
    timeout_s: float | None = None,
) -> TicketLookupOutput:
    raise RuntimeError(
        "DEPRECATED: lookup_support_ticket was removed. "
        "Use agent.tools.mcp_client.manage_incidents_via_mcp "
        "(MCP Server) instead of calling IncidentRepository directly."
    )
