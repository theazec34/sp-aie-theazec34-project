"""Distinct error codes for auth / authorization / validation failures."""

from __future__ import annotations

from enum import Enum
from typing import Any


class McpErrorCode(str, Enum):
    """Stable machine-readable codes (not a generic \"error\" blob)."""

    AUTH_MISSING_TOKEN = "AUTH_MISSING_TOKEN"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_INVALID_HEADER = "AUTH_INVALID_HEADER"
    AUTHZ_INSUFFICIENT_SCOPE = "AUTHZ_INSUFFICIENT_SCOPE"
    VALIDATION_INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    VALIDATION_UNKNOWN_STATUS = "VALIDATION_UNKNOWN_STATUS"
    INCIDENT_NOT_FOUND = "INCIDENT_NOT_FOUND"
    INCIDENT_INVALID_TRANSITION = "INCIDENT_INVALID_TRANSITION"
    INVENTORY_NOT_FOUND = "INVENTORY_NOT_FOUND"
    INVENTORY_WRITE_FORBIDDEN = "INVENTORY_WRITE_FORBIDDEN"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    BACKEND_ERROR = "BACKEND_ERROR"


# Exit / HTTP status mapping for documentation and clients
ERROR_HTTP_STATUS: dict[McpErrorCode, int] = {
    McpErrorCode.AUTH_MISSING_TOKEN: 401,
    McpErrorCode.AUTH_INVALID_TOKEN: 401,
    McpErrorCode.AUTH_INVALID_HEADER: 401,
    McpErrorCode.AUTHZ_INSUFFICIENT_SCOPE: 403,
    McpErrorCode.VALIDATION_INVALID_INPUT: 400,
    McpErrorCode.VALIDATION_UNKNOWN_STATUS: 400,
    McpErrorCode.INCIDENT_NOT_FOUND: 404,
    McpErrorCode.INCIDENT_INVALID_TRANSITION: 400,
    McpErrorCode.INVENTORY_NOT_FOUND: 404,
    McpErrorCode.INVENTORY_WRITE_FORBIDDEN: 403,
    McpErrorCode.BACKEND_UNAVAILABLE: 503,
    McpErrorCode.BACKEND_ERROR: 502,
}


def error_payload(
    code: McpErrorCode,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": False,
        "error_code": code.value,
        "error": message,
        "http_status": ERROR_HTTP_STATUS[code],
    }
    if details:
        body["details"] = details
    return body
