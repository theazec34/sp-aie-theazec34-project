"""Weekly location performance pipeline package."""

from data.pipelines.weekly_location_performance.db import (
    get_latest_run,
    query_weekly_location_performance,
)

__all__ = [
    "get_latest_run",
    "query_weekly_location_performance",
]
