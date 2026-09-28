"""Invocation logging — one structured line per tool call."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mcps.brasaland_tools")


def log_tool_invocation(
    *,
    tool: str,
    client_id: str | None,
    subject: str | None,
    result: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Log client, tool name, and outcome for every invocation."""
    payload = {
        "tool": tool,
        "client": client_id or "unknown",
        "subject": subject or "anonymous",
        "result": result,
    }
    if extra:
        payload.update(extra)
    logger.info("mcp_tool_invocation %s", payload)
