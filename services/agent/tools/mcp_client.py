"""LangGraph → MCP client via langchain-mcp-adapters (Streamable HTTP).

The agent MUST NOT call the Incidents Manager / inventory repositories directly;
all operational tool traffic goes through the Brasaland MCP Server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger("agent.tools.mcp_client")

DEFAULT_MCP_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8100/mcp")
DEFAULT_TIMEOUT_S = float(os.getenv("AGENT_TOOL_TIMEOUT_S", "4"))


def _bearer_token() -> str:
    token = os.getenv("MCP_ACCESS_TOKEN", "").strip()
    if token:
        return token
    # Dev convenience: mint a local HS256 token (same secret as MCP_AUTH_MODE=dev).
    if os.getenv("MCP_AUTH_MODE", "dev").strip().lower() == "dev":
        from mcps.brasaland_tools.auth import issue_dev_token

        return issue_dev_token(client_id="brasaland-langgraph-agent")
    raise RuntimeError(
        "MCP_ACCESS_TOKEN is required when MCP_AUTH_MODE is not 'dev'"
    )


def _server_config() -> dict[str, Any]:
    return {
        "brasaland": {
            "transport": "streamable_http",
            "url": os.getenv("MCP_SERVER_URL", DEFAULT_MCP_URL),
            "headers": {"Authorization": f"Bearer {_bearer_token()}"},
        }
    }


async def _ainvoke_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call one MCP tool through langchain-mcp-adapters MultiServerMCPClient."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(_server_config())
    tools = await client.get_tools()
    by_name = {t.name: t for t in tools}
    # Adapters may prefix tool names; match suffix.
    tool = by_name.get(tool_name)
    if tool is None:
        for name, candidate in by_name.items():
            if name.endswith(tool_name) or tool_name in name:
                tool = candidate
                break
    if tool is None:
        return {
            "ok": False,
            "error": f"MCP tool '{tool_name}' not found; available={sorted(by_name)}",
            "error_code": "MCP_TOOL_NOT_FOUND",
        }

    raw = await tool.ainvoke(arguments)
    return _normalize_tool_result(raw)


def _normalize_tool_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"ok": True, "text": raw}
        return {"ok": True, "text": raw}
    if isinstance(raw, list):
        # MCP content blocks
        texts = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
            else:
                texts.append(str(block))
        joined = "\n".join(texts)
        try:
            parsed = json.loads(joined)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"ok": True, "text": joined}
    return {"ok": True, "data": raw}


def invoke_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """
    Synchronous wrapper for LangGraph nodes.

    When ``MCP_INPROCESS=1`` (default in tests), call tool functions on the
    MCP server module directly *after* injecting AuthInfo — still the same
    tool surface, not IncidentRepository. Remote mode uses MultiServerMCPClient.
    """
    limit = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S
    inprocess = os.getenv("MCP_INPROCESS", "1").strip() in {"1", "true", "yes"}

    try:
        if inprocess:
            return _invoke_inprocess(tool_name, arguments)

        async def _run() -> dict[str, Any]:
            return await asyncio.wait_for(
                _ainvoke_tool(tool_name, arguments),
                timeout=limit,
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Nested event loop — use a dedicated thread.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _run()).result(timeout=limit + 1)
        return asyncio.run(_run())
    except TimeoutError:
        logger.warning("MCP tool %s timed out after %ss", tool_name, limit)
        return {
            "ok": False,
            "timed_out": True,
            "error": f"Timeout ({limit}s) al llamar MCP tool {tool_name}",
            "error_code": "MCP_TIMEOUT",
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("MCP tool %s failed", tool_name)
        return {
            "ok": False,
            "error": f"MCP client error: {type(exc).__name__}: {exc}",
            "error_code": "MCP_CLIENT_ERROR",
        }


def _invoke_inprocess(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Invoke MCP tool callables in-process with a valid mcpauth AuthInfo context.

    Used by CI/evals so we exercise the *same* tool functions the HTTP server
    exposes, without requiring a separate uvicorn process. This is still MCP
    tool surface — not a direct IncidentRepository path from the agent.
    """
    from mcps.brasaland_tools import server as mcp_server
    from mcps.brasaland_tools.auth import issue_dev_token, verify_dev_access_token

    token = _bearer_token() if os.getenv("MCP_ACCESS_TOKEN") else issue_dev_token(
        client_id="brasaland-langgraph-agent"
    )
    auth_info = verify_dev_access_token(token)
    # Populate mcpauth ContextVar the same way Bearer middleware does.
    mcp_server.mcp_auth._context_var.set(auth_info)  # noqa: SLF001

    fn = {
        "manage_incidents": mcp_server.manage_incidents,
        "query_inventory": mcp_server.query_inventory,
        "mutate_inventory": mcp_server.mutate_inventory,
    }.get(tool_name)
    if fn is None:
        return {
            "ok": False,
            "error": f"Unknown MCP tool {tool_name}",
            "error_code": "MCP_TOOL_NOT_FOUND",
        }
    result = fn(**arguments)
    if isinstance(result, dict):
        return result
    return {"ok": True, "data": result}


def manage_incidents_via_mcp(**kwargs: Any) -> dict[str, Any]:
    return invoke_mcp_tool("manage_incidents", kwargs)


def query_inventory_via_mcp(**kwargs: Any) -> dict[str, Any]:
    return invoke_mcp_tool("query_inventory", kwargs)
