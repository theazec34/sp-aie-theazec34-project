"""Property allowlists for tags (aligned with docs/telemetry/event-schemas.json).

Unknown event_types keep non-PII keys. Known types drop keys outside the allowlist.
"""

from __future__ import annotations

from typing import Any

# Keys that must never land in tags regardless of event_type.
_PII_KEYS = frozenset(
    {
        "email",
        "password",
        "name",
        "full_name",
        "phone",
        "telephone",
        "address",
        "token",
        "access_token",
        "refresh_token",
        "jwt",
        "authorization",
    }
)

# Allowlisted property keys per event_type (from event-schemas.json / telemetry-plan.md).
PROPERTY_ALLOWLISTS: dict[str, frozenset[str]] = {
    "inbound_order_created": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_sku",
            "product_category",
            "quantity",
            "unit",
            "currency",
            "unit_cost",
            "total_cost",
            "supplier_id",
            "supplier_name",
            "order_id",
            "city",
        }
    ),
    "outbound_order_created": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_sku",
            "product_category",
            "quantity",
            "unit",
            "currency",
            "reason",
            "order_id",
            "city",
        }
    ),
    "stock_waste_registered": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_sku",
            "product_category",
            "quantity",
            "unit",
            "currency",
            "reason",
            "order_id",
            "city",
            "unit_cost",
            "total_cost",
        }
    ),
    "stock_threshold_triggered": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_sku",
            "product_category",
            "unit",
            "current_stock",
            "threshold",
            "triggering_order_kind",
            "triggering_order_id",
            "city",
        }
    ),
    "direct_stock_edit_rejected": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "attempted_field",
            "http_status",
            "route",
        }
    ),
    "ingredient_price_variance_detected": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_sku",
            "product_category",
            "unit",
            "currency",
            "supplier_name",
            "unit_cost",
            "baseline_unit_cost",
            "variance_pct",
            "threshold_pct",
            "order_id",
            "city",
        }
    ),
    "auth_login_succeeded": frozenset({"result"}),
    "auth_login_failed": frozenset({"result", "failure_reason"}),
    "auth_session_expired": frozenset({"route", "http_status"}),
    "outbound_order_rejected": frozenset(
        {
            "location_id",
            "country",
            "product_id",
            "product_category",
            "quantity",
            "unit",
            "http_status",
            "error_code",
            "route",
        }
    ),
    "inventory_validation_failed": frozenset(
        {"route", "field", "message_key", "http_status"}
    ),
    "product_created": frozenset(
        {
            "product_id",
            "product_sku",
            "product_category",
            "unit",
            "country",
        }
    ),
    "inventory_products_viewed": frozenset({"route", "result_count"}),
    "api_latency_recorded": frozenset(
        {"route", "method", "status_code", "duration_ms"}
    ),
    "frontend_error_captured": frozenset(
        {"route", "error_name", "message_sanitized"}
    ),
    "page_viewed": frozenset({"route", "referrer_route"}),
    "flow_abandoned": frozenset({"route", "step", "idle_ms"}),
    "supplier_directory_viewed": frozenset({"route", "result_count"}),
    "web_vital_recorded": frozenset(
        {"name", "value", "rating", "route", "id", "navigationType", "delta"}
    ),
}

# Envelope metadata folded into tags (not part of properties allowlist).
_ENVELOPE_TAG_KEYS = ("schema_version", "request_id")


def filter_tags(
    event_type: str,
    properties: dict[str, Any],
    *,
    schema_version: str,
    request_id: str,
) -> dict[str, Any]:
    """Build JSONB tags: allowlisted properties + schema_version/request_id."""
    allowed = PROPERTY_ALLOWLISTS.get(event_type)
    tags: dict[str, Any] = {}
    for key, value in properties.items():
        if key in _PII_KEYS or key in _ENVELOPE_TAG_KEYS:
            continue
        if allowed is not None and key not in allowed:
            continue
        tags[key] = value
    tags["schema_version"] = schema_version
    tags["request_id"] = request_id
    return tags
