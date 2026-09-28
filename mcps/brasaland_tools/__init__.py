"""Brasaland MCP Server — Incidents Manager + read-only inventory (OAuth via mcpauth)."""

from mcps.brasaland_tools.server import app, create_app, mcp

__all__ = ["app", "create_app", "mcp"]
