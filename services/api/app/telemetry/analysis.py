"""Re-export canonical analysis module for ``from app.telemetry.analysis import …``.

Source of truth: ``services/telemetry/analysis.py`` (path required by the report hito).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVICES_ROOT = Path(__file__).resolve().parents[3]
if str(_SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICES_ROOT))

from telemetry.analysis import (  # noqa: E402
    AUTH_EVENT_TYPES,
    ERROR_EVENT_TYPES,
    auth_failure_rate,
    build_report,
    default_period,
    error_rate_by_type,
    events_per_day,
    latency_by_route,
    load_events,
)

__all__ = [
    "AUTH_EVENT_TYPES",
    "ERROR_EVENT_TYPES",
    "auth_failure_rate",
    "build_report",
    "default_period",
    "error_rate_by_type",
    "events_per_day",
    "latency_by_route",
    "load_events",
]
