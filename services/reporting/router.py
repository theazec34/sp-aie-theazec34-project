"""FastAPI reporting module — business KPIs (delegates ETL to data/pipelines)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Repo root → data.pipelines.*; services/api → app.auth
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
for _p in (_REPO_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.deps import get_current_user  # noqa: E402
from app.users.models import UserInDB  # noqa: E402
from data.pipelines.pipeline import (  # noqa: E402
    trigger_weekly_location_performance_flow,
)
from data.pipelines.weekly_location_performance.db import (  # noqa: E402
    get_latest_run,
    query_weekly_location_performance,
)
from data.process.weekly_kpis import PIPELINE_NAME  # noqa: E402

router = APIRouter(prefix="/reporting", tags=["reporting"])


class PipelineRunRequest(BaseModel):
    week_start: date | None = None
    pipeline_name: str = Field(default=PIPELINE_NAME)


class PipelineRunAccepted(BaseModel):
    run_id: str | None = None
    status: str
    week_start: str | None = None
    rows_extracted: int | None = None
    rows_upserted: int | None = None


@router.get("/weekly-location-performance")
def weekly_location_performance(
    week_start: date | None = Query(
        default=None,
        description="ISO Monday of the week (default: latest computed week)",
    ),
    _user: UserInDB = Depends(get_current_user),
) -> dict:
    """KPI rows for the CEO/Ops weekly cost & waste report (CONTEXT contract)."""
    return query_weekly_location_performance(week_start)


@router.get("/pipeline-runs/latest")
def pipeline_runs_latest(
    pipeline_name: str = Query(default=PIPELINE_NAME),
    _user: UserInDB = Depends(get_current_user),
) -> dict:
    """Metadata of the most recent pipeline run."""
    latest = get_latest_run(pipeline_name=pipeline_name)
    if latest is None:
        raise HTTPException(status_code=404, detail="No pipeline runs recorded yet")
    return latest


@router.post("/pipeline-runs", response_model=PipelineRunAccepted)
def pipeline_runs_trigger(
    body: PipelineRunRequest | None = None,
    _user: UserInDB = Depends(get_current_user),
) -> PipelineRunAccepted:
    """Manually trigger weekly_location_performance_flow (imports flow from data/pipelines)."""
    body = body or PipelineRunRequest()
    if body.pipeline_name != PIPELINE_NAME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported pipeline_name; expected {PIPELINE_NAME}",
        )
    result = trigger_weekly_location_performance_flow(
        week_start=body.week_start,
        triggered_by="api_manual",
    )
    return PipelineRunAccepted(
        run_id=result.get("run_id"),
        status=result.get("status", "completed"),
        week_start=result.get("week_start"),
        rows_extracted=result.get("rows_extracted"),
        rows_upserted=result.get("rows_upserted"),
    )
