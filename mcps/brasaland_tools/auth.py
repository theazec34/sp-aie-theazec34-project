"""OAuth 2.1 resource-server wiring via mcpauth (not FastMCP built-in auth)."""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
from mcpauth import MCPAuth
from mcpauth.config import (
    AuthServerConfig,
    AuthServerType,
    AuthorizationServerMetadata,
)
from mcpauth.exceptions import (
    MCPAuthTokenVerificationException,
    MCPAuthTokenVerificationExceptionCode,
)
from mcpauth.types import AuthInfo
from mcpauth.utils import fetch_server_config
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcps.brasaland_tools.scopes import ALL_SCOPES, SCOPE_TOOLS

DEV_ISSUER = os.getenv("MCP_AUTH_DEV_ISSUER", "https://auth.brasaland.local/dev")
DEV_AUDIENCE = os.getenv("MCP_AUTH_AUDIENCE", "https://mcp.brasaland.local")
DEV_SECRET = os.getenv("MCP_AUTH_DEV_SECRET", "brasaland-mcp-dev-secret-change-me")


def _dev_server_config() -> AuthServerConfig:
    return AuthServerConfig(
        type=AuthServerType.OAUTH,
        metadata=AuthorizationServerMetadata(
            issuer=DEV_ISSUER,
            authorization_endpoint=f"{DEV_ISSUER}/authorize",
            token_endpoint=f"{DEV_ISSUER}/token",
            jwks_uri=f"{DEV_ISSUER}/jwks",
            response_types_supported=["code"],
            grant_types_supported=["authorization_code", "client_credentials"],
            code_challenge_methods_supported=["S256"],
            scope_supported=ALL_SCOPES,
            token_endpoint_auth_methods_supported=["client_secret_post", "none"],
        ),
    )


def build_mcp_auth() -> tuple[MCPAuth, str]:
    """
    Build MCPAuth resource-server helpers.

    Modes:
    - ``MCP_AUTH_MODE=dev`` (default): HS256 JWT verified locally (tests / Codespaces).
    - ``MCP_AUTH_MODE=oidc``: discover issuer via ``MCP_AUTH_ISSUER`` and verify JWT (JWKS).
    """
    mode = os.getenv("MCP_AUTH_MODE", "dev").strip().lower()
    if mode == "oidc":
        issuer = os.getenv("MCP_AUTH_ISSUER", "").strip()
        if not issuer:
            raise ValueError("MCP_AUTH_ISSUER is required when MCP_AUTH_MODE=oidc")
        server = fetch_server_config(issuer, AuthServerType.OIDC)
        return MCPAuth(server=server), "jwt"

    return MCPAuth(server=_dev_server_config()), "dev_jwt"


def verify_dev_access_token(token: str) -> AuthInfo:
    """Verify HS256 JWT issued by the local/dev issuer (mcpauth VerifyAccessTokenFunction)."""
    try:
        claims = jwt.decode(
            token,
            DEV_SECRET,
            algorithms=["HS256"],
            audience=DEV_AUDIENCE,
            options={"require": ["exp", "sub", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise MCPAuthTokenVerificationException(
            MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN,
            cause=exc,
        ) from exc

    scope_claim = claims.get("scope") or claims.get("scopes") or ""
    if isinstance(scope_claim, list):
        scopes = [str(s) for s in scope_claim]
    else:
        scopes = [s for s in str(scope_claim).split() if s]

    return AuthInfo(
        token=token,
        issuer=str(claims["iss"]),
        subject=str(claims["sub"]),
        client_id=claims.get("client_id") or claims.get("azp"),
        audience=claims.get("aud"),
        scopes=scopes,
        claims=dict(claims),
    )


def issue_dev_token(
    *,
    subject: str = "brasaland-agent",
    client_id: str = "brasaland-agent",
    scopes: list[str] | None = None,
    ttl_s: int = 3600,
) -> str:
    """Mint a short-lived HS256 access token for local / Playground use."""
    now = int(time.time())
    scope_list = scopes or [
        SCOPE_TOOLS,
        "incidents:read",
        "incidents:write",
        "inventory:read",
    ]
    payload: dict[str, Any] = {
        "iss": DEV_ISSUER,
        "sub": subject,
        "aud": DEV_AUDIENCE,
        "client_id": client_id,
        "scope": " ".join(scope_list),
        "iat": now,
        "exp": now + ttl_s,
    }
    return jwt.encode(payload, DEV_SECRET, algorithm="HS256")


async def protected_resource_metadata(request: Request) -> JSONResponse:
    """RFC 9728 Protected Resource Metadata for MCP discovery."""
    resource = os.getenv("MCP_RESOURCE_URL", str(request.base_url).rstrip("/") + "/mcp")
    issuer = os.getenv("MCP_AUTH_ISSUER", DEV_ISSUER)
    return JSONResponse(
        {
            "resource": resource,
            "authorization_servers": [issuer],
            "scopes_supported": ALL_SCOPES,
            "bearer_methods_supported": ["header"],
            "resource_documentation": (
                "https://github.com/theazec34/brasaland-digital/blob/main/docs/mcp/mcp-oauth-tools.md"
            ),
        }
    )


async def dev_token_endpoint(request: Request) -> JSONResponse:
    """
    Dev-only token helper (client_credentials-like) so MCP Playground / agents
    can obtain a Bearer JWT without a full OIDC stack.
    Disabled when MCP_AUTH_MODE=oidc.
    """
    if os.getenv("MCP_AUTH_MODE", "dev").strip().lower() == "oidc":
        return JSONResponse(
            {
                "error": "invalid_request",
                "error_description": "Dev token endpoint disabled in oidc mode",
                "error_code": "AUTH_DEV_TOKEN_DISABLED",
            },
            status_code=404,
        )

    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}

    scopes_raw = body.get("scope") or " ".join(
        [SCOPE_TOOLS, "incidents:read", "incidents:write", "inventory:read"]
    )
    scopes = [s for s in str(scopes_raw).split() if s]
    subject = str(body.get("sub") or "playground-client")
    client_id = str(body.get("client_id") or "mcp-playground")
    token = issue_dev_token(subject=subject, client_id=client_id, scopes=scopes)
    return JSONResponse(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(scopes),
        }
    )
