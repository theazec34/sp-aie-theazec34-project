"""Public REST API for centralized incidents under /api/incidents."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.cache import INCIDENTS_SUMMARY_TTL, incidents_cache
from app.incidents.models import (
    Incident,
    IncidentCreate,
    IncidentStatusUpdate,
    IncidentSummary,
)
from app.incidents.repository import IncidentRepository

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

_SUMMARY_KEY = "incidents:summary"


def _invalidate_incident_caches() -> None:
    incidents_cache.invalidate(_SUMMARY_KEY)


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate) -> Incident:
    repo = IncidentRepository()
    try:
        created = repo.create(payload)
        _invalidate_incident_caches()
        return created
    finally:
        repo.close()


@router.get("", response_model=list[Incident])
def list_incidents(
    status_filter: str | None = Query(None, alias="status"),
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[Incident]:
    repo = IncidentRepository()
    try:
        return repo.list(
            status=status_filter,
            origin=origin,
            branch=branch,
            category=category,
        )
    finally:
        repo.close()


@router.get("/summary", response_model=IncidentSummary)
def incidents_summary(response: Response) -> IncidentSummary:
    cached = incidents_cache.get(_SUMMARY_KEY)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return IncidentSummary.model_validate(cached)

    repo = IncidentRepository()
    try:
        summary = repo.summary()
        incidents_cache.set(
            _SUMMARY_KEY,
            summary.model_dump(mode="json"),
            INCIDENTS_SUMMARY_TTL,
        )
        response.headers["X-Cache"] = "MISS"
        return summary
    finally:
        repo.close()


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: int) -> Incident:
    repo = IncidentRepository()
    try:
        item = repo.get(incident_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidencia no encontrada",
            )
        return item
    finally:
        repo.close()


@router.patch("/{incident_id}/status", response_model=Incident)
def patch_incident_status(
    incident_id: int, payload: IncidentStatusUpdate
) -> Incident:
    repo = IncidentRepository()
    try:
        existing = repo.get(incident_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidencia no encontrada",
            )
        try:
            updated = repo.update_status(incident_id, payload.status)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"field": "status", "message": str(exc)},
            ) from exc
        assert updated is not None
        _invalidate_incident_caches()
        return updated
    finally:
        repo.close()
