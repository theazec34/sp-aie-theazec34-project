"""Business reporting API package.

Endpoints live in ``router.py`` and are mounted by ``services/api`` FastAPI.
ETL stays in ``data/pipelines`` — never duplicated here.
"""

from __future__ import annotations

PLANNED_ENDPOINTS = (
    "GET /reporting/weekly-location-performance",
    "GET /reporting/pipeline-runs/latest",
    "POST /reporting/pipeline-runs",
)
