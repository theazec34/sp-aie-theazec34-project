"""MCP tool handlers sin FastMCP/mcpauth — para el agente in-process en Docker.

Codespaces a menudo no puede `pip install` dentro del contenedor (DNS/egress).
El grafo LangGraph llama estas funciones con ``MCP_INPROCESS=1``; la superficie
sigue siendo la de las tools MCP (backend.py), no IncidentRepository directo.
"""

from __future__ import annotations

from typing import Any, Literal

from mcps.brasaland_tools.backend import (
    BackendError,
    create_incident,
    front_ops_summary,
    get_incident,
    inventory_ops_summary,
    list_careers_ops,
    list_incidents,
    list_inventory_orders,
    list_reservations_ops,
    list_suppliers,
    query_products,
    supplier_directory_summary,
    update_incident_status,
)
from mcps.brasaland_tools.errors import McpErrorCode, error_payload
from mcps.brasaland_tools.logging_util import log_tool_invocation

CLIENT = "brasaland-langgraph-agent"
SUBJECT = "inprocess"


def _err(code: McpErrorCode, message: str, **details: Any) -> dict[str, Any]:
    return error_payload(code, message, details=details or None)


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
    tool = "manage_incidents"
    try:
        if action == "create":
            if not all([title, description, category, origin, branch]):
                out = _err(
                    McpErrorCode.VALIDATION_INVALID_INPUT,
                    "create requires title, description, category, origin, branch",
                )
                log_tool_invocation(
                    tool=tool, client_id=CLIENT, subject=SUBJECT, result=out["error_code"]
                )
                return out
            created = create_incident(
                {
                    "title": title,
                    "description": description,
                    "category": category,
                    "origin": origin,
                    "branch": branch,
                }
            )
            log_tool_invocation(
                tool=tool, client_id=CLIENT, subject=SUBJECT, result="ok"
            )
            return {"ok": True, "action": action, "incident": created}

        if action == "get":
            if incident_id is None:
                return _err(McpErrorCode.VALIDATION_INVALID_INPUT, "get requires incident_id")
            item = get_incident(incident_id)
            if item is None:
                return _err(
                    McpErrorCode.INCIDENT_NOT_FOUND,
                    f"Incidencia {incident_id} no encontrada",
                    incident_id=incident_id,
                )
            return {"ok": True, "action": action, "incident": item}

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
            return {
                "ok": True,
                "action": action,
                "incidents": trimmed,
                "count": len(trimmed),
            }

        if action == "update_status":
            if incident_id is None or not status:
                return _err(
                    McpErrorCode.VALIDATION_INVALID_INPUT,
                    "update_status requires incident_id and status",
                )
            try:
                updated = update_incident_status(incident_id, status)
            except BackendError as exc:
                if exc.status_code == 404:
                    code = McpErrorCode.INCIDENT_NOT_FOUND
                elif exc.status_code == 400:
                    code = McpErrorCode.INCIDENT_INVALID_TRANSITION
                else:
                    code = McpErrorCode.BACKEND_ERROR
                return _err(code, str(exc), incident_id=incident_id)
            return {"ok": True, "action": action, "incident": updated}

        return _err(McpErrorCode.VALIDATION_INVALID_INPUT, f"Unknown action: {action}")
    except BackendError as exc:
        return _err(McpErrorCode.BACKEND_ERROR, str(exc), status_code=exc.status_code)
    except Exception as exc:  # noqa: BLE001
        return _err(McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}")


def query_inventory(
    product_id: int | None = None,
    name_query: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    try:
        products = query_products(
            product_id=product_id, name_query=name_query, limit=limit
        )
        if product_id is not None and not products:
            return _err(
                McpErrorCode.INVENTORY_NOT_FOUND,
                f"Producto {product_id} no encontrado",
                product_id=product_id,
            )
        log_tool_invocation(
            tool="query_inventory", client_id=CLIENT, subject=SUBJECT, result="ok"
        )
        return {"ok": True, "products": products, "count": len(products)}
    except BackendError as exc:
        return _err(McpErrorCode.BACKEND_ERROR, str(exc))
    except Exception as exc:  # noqa: BLE001
        return _err(McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}")


def query_inventory_ops(
    view: Literal["summary", "history", "inbound", "outbound"] = "summary",
    name_query: str | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    try:
        if view == "summary":
            summary = inventory_ops_summary(limit=limit)
            out: dict[str, Any] = {"ok": True, "view": view, "summary": summary}
        else:
            kind = None if view == "history" else view
            orders = list_inventory_orders(
                kind=kind, name_query=name_query, limit=limit
            )
            out = {
                "ok": True,
                "view": view,
                "orders": orders,
                "count": len(orders),
            }
        log_tool_invocation(
            tool="query_inventory_ops", client_id=CLIENT, subject=SUBJECT, result="ok"
        )
        return out
    except BackendError as exc:
        return _err(McpErrorCode.BACKEND_ERROR, str(exc))
    except Exception as exc:  # noqa: BLE001
        return _err(McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}")


def query_suppliers(
    action: Literal["list", "top_rate", "summary"] = "summary",
    name_query: str | None = None,
    branch: str | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    try:
        if action == "summary":
            if branch:
                suppliers = list_suppliers(branch=branch, limit=500)
                active = [
                    s for s in suppliers if str(s.get("status", "")).lower() == "active"
                ]
                ranked = sorted(
                    suppliers,
                    key=lambda s: float(s.get("rate_per_unit") or 0),
                    reverse=True,
                )
                summary = {
                    "count": len(suppliers),
                    "active_count": len(active),
                    "currency": "EUR",
                    "branch": branch,
                    "top_by_rate_eur": ranked[:limit],
                    "highest_rate_active": (
                        sorted(
                            active,
                            key=lambda s: float(s.get("rate_per_unit") or 0),
                            reverse=True,
                        )[:1]
                        or [None]
                    )[0],
                }
            else:
                summary = supplier_directory_summary(limit=limit)
            out: dict[str, Any] = {"ok": True, "action": action, "summary": summary}
        elif action == "top_rate":
            suppliers = list_suppliers(
                name_query=name_query, branch=branch, limit=200
            )
            ranked = sorted(
                suppliers,
                key=lambda s: float(s.get("rate_per_unit") or 0),
                reverse=True,
            )[:limit]
            out = {
                "ok": True,
                "action": action,
                "currency": "EUR",
                "branch": branch,
                "suppliers": ranked,
                "count": len(ranked),
            }
        else:
            suppliers = list_suppliers(
                name_query=name_query, branch=branch, limit=limit
            )
            out = {
                "ok": True,
                "action": action,
                "currency": "EUR",
                "branch": branch,
                "suppliers": suppliers,
                "count": len(suppliers),
            }
        log_tool_invocation(
            tool="query_suppliers", client_id=CLIENT, subject=SUBJECT, result="ok"
        )
        return out
    except BackendError as exc:
        return _err(McpErrorCode.BACKEND_ERROR, str(exc))
    except Exception as exc:  # noqa: BLE001
        return _err(McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}")


def query_front_ops(
    action: Literal["summary", "reservations", "careers"] = "summary",
    branch: str | None = None,
    day: Literal["today", "tomorrow", "all"] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    try:
        if action == "summary":
            out: dict[str, Any] = {
                "ok": True,
                "action": action,
                "summary": front_ops_summary(branch=branch),
            }
        elif action == "careers":
            rows = list_careers_ops(branch=branch, limit=limit)
            out = {
                "ok": True,
                "action": action,
                "branch": branch,
                "careers": rows,
                "count": len(rows),
            }
        else:
            day_key = None if day in {None, "all"} else day
            rows = list_reservations_ops(
                branch=branch, day=day_key, limit=limit
            )
            out = {
                "ok": True,
                "action": action,
                "branch": branch,
                "day": day or "all",
                "reservations": rows,
                "count": len(rows),
            }
        log_tool_invocation(
            tool="query_front_ops", client_id=CLIENT, subject=SUBJECT, result="ok"
        )
        return out
    except BackendError as exc:
        return _err(McpErrorCode.BACKEND_ERROR, str(exc))
    except Exception as exc:  # noqa: BLE001
        return _err(McpErrorCode.BACKEND_ERROR, f"{type(exc).__name__}: {exc}")


def mutate_inventory(
    operation: Literal["create", "update", "delete", "inbound", "outbound"],
    product_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = _err(
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
        tool="mutate_inventory",
        client_id=CLIENT,
        subject=SUBJECT,
        result=out["error_code"],
    )
    return out


TOOL_HANDLERS = {
    "manage_incidents": manage_incidents,
    "query_inventory": query_inventory,
    "query_inventory_ops": query_inventory_ops,
    "query_suppliers": query_suppliers,
    "query_front_ops": query_front_ops,
    "mutate_inventory": mutate_inventory,
}
