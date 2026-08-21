"""Business reporting API package (stub — design hito).

Future FastAPI routers will live here or be mounted from ``services/api``.
ETL stays in ``data/pipelines`` / ``data/process``.
"""

from __future__ import annotations

PLANNED_ENDPOINTS = (
    "GET /reporting/weekly-location-performance",
    "GET /reporting/pipeline-runs/latest",
    "POST /reporting/pipeline-runs",
)

PIPELINE_ENTRYPOINTS = {
    "query_kpis": "data.pipelines.weekly_location_performance.query_weekly_location_performance",
    "latest_run": "data.pipelines.weekly_location_performance.get_latest_run",
    "trigger": "data.pipelines.weekly_location_performance.trigger_weekly_location_performance_flow",
}
