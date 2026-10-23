"""Brasaland MCP Server — Incidents Manager + inventory + suppliers (OAuth via mcpauth).

Lazy exports so importing submodules (p. ej. backend) no obliga a cargar FastMCP
hasta que se use el servidor HTTP o las tools decoradas.
"""

from __future__ import annotations

from typing import Any

__all__ = ["app", "create_app", "mcp"]


def __getattr__(name: str) -> Any:
    if name in {"app", "create_app", "mcp"}:
        from mcps.brasaland_tools.server import app, create_app, mcp

        mapping = {"app": app, "create_app": create_app, "mcp": mcp}
        return mapping[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
