"""Evals for Brasaland MCP Server (OAuth via mcpauth + tools discovery)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

_REPO = Path(__file__).resolve().parents[2]
_SERVICES = _REPO / "services"
_API = _SERVICES / "api"
for _p in (_REPO, _SERVICES, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture()
def mcp_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_AUTH_MODE", "dev")
    monkeypatch.setenv("MCP_DATA_MODE", "direct")
    monkeypatch.setenv("MCP_AUTH_SHOW_ERRORS", "1")
    # Reload server module so auth/config pick up env.
    import importlib

    import mcps.brasaland_tools.auth as auth_mod
    import mcps.brasaland_tools.server as server_mod

    importlib.reload(auth_mod)
    importlib.reload(server_mod)
    return server_mod


@pytest.fixture()
def client(mcp_env):
    with TestClient(mcp_env.create_app()) as c:
        yield c


@pytest.fixture()
def token(mcp_env):
    from mcps.brasaland_tools.auth import issue_dev_token

    return issue_dev_token(client_id="pytest-client")


def test_metadata_and_protected_resource_public(client):
    as_meta = client.get("/.well-known/oauth-authorization-server")
    assert as_meta.status_code == 200
    body = as_meta.json()
    assert "issuer" in body
    assert "authorization_endpoint" in body

    prm = client.get("/.well-known/oauth-protected-resource")
    assert prm.status_code == 200
    prm_body = prm.json()
    assert "scopes_supported" in prm_body
    assert "incidents:read" in prm_body["scopes_supported"]
    assert "inventory:read" in prm_body["scopes_supported"]


def test_unauthenticated_mcp_rejected(client):
    """No Bearer token → cannot reach MCP (list/call tools)."""
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code == 401
    body = r.json()
    assert body.get("error") in {
        "missing_auth_header",
        "invalid_token",
        "invalid_auth_header_format",
        "missing_bearer_token",
    } or "error" in body


def test_invalid_token_rejected(client):
    r = client.post(
        "/mcp",
        headers={"Authorization": "Bearer not-a-real-jwt"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert r.status_code == 401


def test_missing_required_scope_rejected(client, mcp_env):
    from mcps.brasaland_tools.auth import issue_dev_token

    weak = issue_dev_token(scopes=["inventory:read"], client_id="weak")
    r = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {weak}"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert r.status_code == 403
    assert r.json().get("error") == "missing_required_scopes"


def test_manage_incidents_create_get_status(mcp_env, token, caplog):
    """Create + get + update_status via MCP tool functions (real Incident store)."""
    from mcps.brasaland_tools.auth import verify_dev_access_token

    auth_info = verify_dev_access_token(token)
    mcp_env.mcp_auth._context_var.set(auth_info)

    with caplog.at_level(logging.INFO, logger="mcps.brasaland_tools"):
        created = mcp_env.manage_incidents(
            action="create",
            title="MCP horno",
            description="Prueba MCP create",
            category="equipment_failure",
            origin="branch",
            branch="medellin_centro",
        )
    assert created["ok"] is True
    incident_id = created["incident"]["id"]
    assert created["incident"]["status"] == "open"

    got = mcp_env.manage_incidents(action="get", incident_id=incident_id)
    assert got["ok"] is True
    assert got["incident"]["id"] == incident_id

    updated = mcp_env.manage_incidents(
        action="update_status",
        incident_id=incident_id,
        status="in_progress",
    )
    assert updated["ok"] is True
    assert updated["incident"]["status"] == "in_progress"

    # Lifecycle endpoint path is enforced in backend.update_incident_status.
    assert any("manage_incidents" in r.message for r in caplog.records)


def test_query_inventory_and_write_rejected(mcp_env, token, caplog):
    from mcps.brasaland_tools.auth import verify_dev_access_token
    from mcps.brasaland_tools.errors import McpErrorCode

    # Ensure inventory ORM tables exist (same as API startup).
    import app.inventory.models  # noqa: F401
    from app.database import init_db

    init_db()

    mcp_env.mcp_auth._context_var.set(verify_dev_access_token(token))

    listed = mcp_env.query_inventory(limit=5)
    assert listed["ok"] is True
    assert "products" in listed

    with caplog.at_level(logging.INFO, logger="mcps.brasaland_tools"):
        denied = mcp_env.mutate_inventory(operation="create", product_id=1, payload={"x": 1})
    assert denied["ok"] is False
    assert denied["error_code"] == McpErrorCode.INVENTORY_WRITE_FORBIDDEN.value
    assert denied["http_status"] == 403
    assert any("mutate_inventory" in r.message for r in caplog.records)


def test_tool_discovery_schemas(mcp_env):
    """Discovery: tool names + descriptions available without reading source."""
    names = {"manage_incidents", "query_inventory", "mutate_inventory"}
    for name in names:
        assert hasattr(mcp_env, name)
    doc = (mcp_env.manage_incidents.__doc__ or "") + str(
        getattr(mcp_env.manage_incidents, "__tool__", "")
    )
    # Tool decorator description is on the FastMCP registration; docstring also documents lifecycle.
    desc_source = doc + (mcp_env.manage_incidents.__doc__ or "")
    # Read description from FastMCP tool registry when available.
    try:
        tools_dict = getattr(mcp_env.mcp, "_tool_manager", None)
        if tools_dict is not None and hasattr(tools_dict, "_tools"):
            t = tools_dict._tools.get("manage_incidents")
            if t is not None:
                desc_source += getattr(t, "description", "") or ""
    except Exception:  # noqa: BLE001
        pass
    assert "inventory" in (mcp_env.mcp.instructions or "").lower()
    assert "incident" in (mcp_env.mcp.instructions or "").lower()
    # Per-tool descriptions must be rich enough for external discovery.
    assert len((mcp_env.query_inventory.__doc__ or "")) > 20
    assert "read-only" in (mcp_env.query_inventory.__doc__ or "").lower() or (
        "read" in (mcp_env.mcp.instructions or "").lower()
    )

def test_dev_token_endpoint(client):
    r = client.post("/dev/token", json={"client_id": "playground", "scope": "brasaland:tools incidents:read"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "Bearer"
    assert r.json()["access_token"]


def test_error_codes_distinct():
    from mcps.brasaland_tools.errors import ERROR_HTTP_STATUS, McpErrorCode

    assert ERROR_HTTP_STATUS[McpErrorCode.AUTH_MISSING_TOKEN] == 401
    assert ERROR_HTTP_STATUS[McpErrorCode.AUTHZ_INSUFFICIENT_SCOPE] == 403
    assert ERROR_HTTP_STATUS[McpErrorCode.VALIDATION_INVALID_INPUT] == 400
    assert ERROR_HTTP_STATUS[McpErrorCode.INVENTORY_WRITE_FORBIDDEN] == 403
    assert len(set(ERROR_HTTP_STATUS.values())) >= 3
