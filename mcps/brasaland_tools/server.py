"""Brasaland company tools MCP Server (Streamable HTTP + mcpauth OAuth).

Exposes:
- ``manage_incidents`` — create / query / update status (PATCH .../status)
- ``query_inventory`` — read-only stock lookup
- ``mutate_inventory`` — always rejects writes (least privilege)

Auth: mcpauth Bearer JWT (not FastMCP built-in auth).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from fastmcp import FastMCP
from mcpauth.exceptions import BearerAuthExceptionCode, MCPAuthBearerAuthException
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route

from mcps.brasaland_tools.auth import (
    DEV_AUDIENCE,
    build_mcp_auth,
    dev_token_endpoint,
    protected_resource_metadata,
    verify_dev_access_token,
)
from mcps.brasaland_tools.backend import (
    BackendError,
    create_incident,
    get_incident,
    list_incidents,
    query_products,
    update_incident_status,
)
from mcps.brasaland_tools.errors import McpErrorCode, error_payload
from mcps.brasaland_tools.logging_util import log_tool_invocation
from mcps.brasaland_tools.scopes import (
    INCIDENT_WRITE_SCOPES,
    SCOPE_INVENTORY_READ,
    SCOPE_TOOLS,
    TOOL_REQUIRED_SCOPES,
)

logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

mcp = FastMCP(
    name="brasaland-company-tools",
    instructions=(
        "Brasaland operational tools: Incidents Manager (create/query/status) "
        "and read-only inventory. Requires OAuth Bearer JWT with least-privilege "
        "scopes. Inventory writes are always rejected."
    ),
)

mcp_auth, auth_mode = build_mcp_auth()


def _require_scopes(required: list[str]) -> None:
    info = mcp_auth.auth_info
    if info is None:
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_AUTH_HEADER)
    missing = [s for s in required if s not in info.scopes]
    if missing:
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES)


def _client_meta() -> tuple[str | None, str | None]:
    info = mcp_auth.auth_info
    if info is None:
        return None, None
    return info.client_id, info.subject


def _tool_error(code: McpErrorCode, message: str, **details: Any) -> dict[str, Any]:
    return error_payload(code, message, details=details or None)


@mcp.tool(
    name="manage_incidents",
    description=(
        "Manage Brasaland Incidents Manager tickets. "
        "Actions: create (new ticket), get (by id), list (filters), "
        "update_status (lifecycle via PATCH /api/incidents/{id}/status only). "
        "Domain enums must match the API: status open|in_progress|resolved|discarded; "
        "origin customer|branch|internal; category equipment_failure|supply_issue|"
        "customer_complaint|staff_issue|facility_issue|pos_system|delivery_issue|other; "
        "branch values like medellin_centro, miami_doral, etc. "
        "Requires scopes: brasaland:tools + incidents:read; write actions also need "
        "incidents:write."
    ),
)
def manage_incidents(
    action: Literal["create", "get", "list", "update_status"],
    incident_id: int | None = None,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    status: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Incidents Manager tool — create, query, and update status."""
    tool = "manage_incidents"
    client_id, subject = _client_meta()
    try:
        _require_scopes(TOOL_REQUIRED_SCOPES[tool])

        if action in ("create", "update_status"):
            _require_scopes(INCIDENT_WRITE_SCOPES)

        if action == "create":
            if not all([title, description, category, origin, branch]):
                result = _tool_error(
                    McpErrorCode.VALIDATION_INVALID_INPUT,
                    "create requires title, description, category, origin, branch",
                )
                log_tool_invocation(
                    tool=tool, client_id=client_id, subject=subject,
                    result=result["error_code"],
                )
                return result
            created = create_incident(
                {
                    "title": title,
                    "description": description,
                    "category": category,
                    "origin": origin,
                    "branch": branch,
                }
            )
            out = {"ok": True, "action": action, "incident": created}
            log_tool_invocation(
                tool=tool, client_id=client_id, subject=subject, result="ok",
                extra={"action": action, "incident_id": created.get("id")},
            )
            return out

        if action == "get":
            if incident_id is None:
                result = _tool_error(
                    McpErrorCode.VALIDATION_INVALID_INPUT,
                    "get requires incident_id",
                )
                log_tool_invocation(
                    tool=tool, client_id=client_id, subject=subject,
                    result=result["error_code"],
                )
                return result
            item = get_incident(incident_id)
            if item is None:
                result = _tool_error(
                    McpErrorCode.INCIDENT_NOT_FOUND,
                    f"Incidencia {incident_id} no encontrada",
                    incident_id=incident_id,
                )
                log_tool_invocation(
                    tool=tool, client_id=client_id, subject=subject,
                    result=result["error_code"],
                )
                return result
            out = {"ok": True, "action": action, "incident": item}
            log_tool_invocation(
                tool=tool, client_id=client_id, subject=subject, result="ok",
                extra={"action": action, "incident_id": incident_id},
            )
            return out

        if action == "list":
            items = list_incidents(
                {
                    "status": status,
                    "origin": origin,
                    "branch": branch,
                    "category": category,
                }
            )
            trimmed = items[: max(1, min(limit, 50))]
            out = {"ok": True, "action": action, "incidents": trimmed, "count": len(trimmed)}
            log_tool_invocation(
                tool=tool, client_id=client_id, subject=subject, result="ok",
                extra={"action": action, "count": len(trimmed)},
            )
            return out

        if action == "update_status":
            if incident_id is None or not status:
                result = _tool_error(
                    McpErrorCode.VALIDATION_INVALID_INPUT,
                    "update_status requires incident_id and status",
                )
                log_tool_invocation(
                    tool=tool, client_id=client_id, subject=subject,
                    result=result["error_code"],
                )
                return result
            try:
                updated = update_incident_status(incident_id, status)
            except BackendError as exc:
                if exc.status_code == 404:
                    code = McpErrorCode.INCIDENT_NOT_FOUND
                elif exc.status_code == 400:
                    code = McpErrorCode.INCIDENT_INVALID_TRANSITION
                else:
                    code = McpErrorCode.BACKEND_ERROR
                result = _tool_error(code, str(exc), incident_id=incident_id)
                log_tool_invocation(
                    tool=tool, client_id=client_id, subject=subject,
                    result=result["error_code"],
                )
                return result
            out = {"ok": True, "action": action, "incident": updated}
            log_tool_invocation(
                tool=tool, client_id=client_id, subject=subject, result="ok",
                extra={"action": action, "incident_id": incident_id, "status": status},
            )
            return out

        result = _tool_error(
            McpErrorCode.VALIDATION_INVALID_INPUT,
            f"Unknown action: {action}",
        )
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result

    except MCPAuthBearerAuthException as exc:
        code = (
            McpErrorCode.AUTHZ_INSUFFICIENT_SCOPE
            if exc.code == BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES
            else McpErrorCode.AUTH_INVALID_TOKEN
        )
        result = _tool_error(code, str(exc.code.value), exception=exc.code.value)
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result
    except BackendError as exc:
        result = _tool_error(
            McpErrorCode.BACKEND_ERROR, str(exc), status_code=exc.status_code
        )
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result = _tool_error(
            McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}"
        )
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result


@mcp.tool(
    name="query_inventory",
    description=(
        "Read-only inventory consultation. Returns products with id, name, sku, "
        "unit, category, country, current_stock (same fields as GET /inventory/products). "
        "Never creates, updates, or deletes inventory. "
        "Requires scopes: brasaland:tools + inventory:read."
    ),
)
def query_inventory(
    product_id: int | None = None,
    name_query: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Read-only inventory lookup."""
    tool = "query_inventory"
    client_id, subject = _client_meta()
    try:
        _require_scopes(TOOL_REQUIRED_SCOPES[tool])
        products = query_products(
            product_id=product_id, name_query=name_query, limit=limit
        )
        if product_id is not None and not products:
            result = _tool_error(
                McpErrorCode.INVENTORY_NOT_FOUND,
                f"Producto {product_id} no encontrado",
                product_id=product_id,
            )
            log_tool_invocation(
                tool=tool, client_id=client_id, subject=subject,
                result=result["error_code"],
            )
            return result
        out = {"ok": True, "products": products, "count": len(products)}
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result="ok",
            extra={"count": len(products)},
        )
        return out
    except MCPAuthBearerAuthException as exc:
        code = (
            McpErrorCode.AUTHZ_INSUFFICIENT_SCOPE
            if exc.code == BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES
            else McpErrorCode.AUTH_INVALID_TOKEN
        )
        result = _tool_error(code, str(exc.code.value))
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result
    except BackendError as exc:
        result = _tool_error(McpErrorCode.BACKEND_ERROR, str(exc))
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result


@mcp.tool(
    name="mutate_inventory",
    description=(
        "Inventory mutation entrypoint — ALWAYS rejected. Inventory via MCP is "
        "read-only by design (least privilege). Use query_inventory for stock. "
        "Any create/update/delete attempt returns INVENTORY_WRITE_FORBIDDEN. "
        "Requires scopes: brasaland:tools + inventory:read (still cannot write)."
    ),
)
def mutate_inventory(
    operation: Literal["create", "update", "delete", "inbound", "outbound"],
    product_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicitly reject every inventory write attempt."""
    tool = "mutate_inventory"
    client_id, subject = _client_meta()
    try:
        _require_scopes([SCOPE_TOOLS, SCOPE_INVENTORY_READ])
    except MCPAuthBearerAuthException as exc:
        code = (
            McpErrorCode.AUTHZ_INSUFFICIENT_SCOPE
            if exc.code == BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES
            else McpErrorCode.AUTH_INVALID_TOKEN
        )
        result = _tool_error(code, str(exc.code.value))
        log_tool_invocation(
            tool=tool, client_id=client_id, subject=subject, result=result["error_code"],
        )
        return result

    result = _tool_error(
        McpErrorCode.INVENTORY_WRITE_FORBIDDEN,
        (
            f"Inventory is read-only through MCP. Operation '{operation}' is "
            "forbidden; use query_inventory for consultation only."
        ),
        operation=operation,
        product_id=product_id,
        payload=payload,
    )
    log_tool_invocation(
        tool=tool, client_id=client_id, subject=subject,
        result=result["error_code"],
        extra={"operation": operation},
    )
    return result


def create_app() -> Starlette:
    """Starlette app: Protected Resource Metadata + mcpauth Bearer + Streamable HTTP."""
    verify = verify_dev_access_token if auth_mode == "dev_jwt" else "jwt"
    bearer_cls = mcp_auth.bearer_auth_middleware(
        verify,
        audience=os.getenv("MCP_AUTH_AUDIENCE", DEV_AUDIENCE),
        required_scopes=[SCOPE_TOOLS],
        show_error_details=os.getenv("MCP_AUTH_SHOW_ERRORS", "1") == "1",
    )
    bearer_auth = Middleware(bearer_cls)

    mcp_http = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        stateless_http=True,
    )

    routes: list[Any] = [
        mcp_auth.metadata_route(),
        Route(
            "/.well-known/oauth-protected-resource",
            protected_resource_metadata,
            methods=["GET", "OPTIONS"],
        ),
        Route(
            "/.well-known/oauth-protected-resource/mcp",
            protected_resource_metadata,
            methods=["GET", "OPTIONS"],
        ),
        Route("/dev/token", dev_token_endpoint, methods=["POST"]),
        Mount("/", app=mcp_http, middleware=[bearer_auth]),
    ]
    # FastMCP http_app lifespan must be wired on the outer Starlette app.
    return Starlette(routes=routes, lifespan=mcp_http.lifespan)


app = create_app()


def main() -> None:
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8100"))
    uvicorn.run(
        "mcps.brasaland_tools.server:app",
        host=host,
        port=port,
        reload=os.getenv("MCP_RELOAD", "0") == "1",
    )


if __name__ == "__main__":
    main()
