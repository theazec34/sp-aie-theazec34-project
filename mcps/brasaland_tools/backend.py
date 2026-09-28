"""HTTP client over the real Incidents Manager + Inventory APIs.

Field names / IDs match ``/api/incidents`` and ``/inventory/*`` exactly.
Status changes always go through ``PATCH /api/incidents/{id}/status``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx

_REPO = Path(__file__).resolve().parents[2]
_API = _REPO / "services" / "api"
for _p in (_REPO, _API):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
# ``http`` = call live FastAPI; ``direct`` = in-process repositories (tests / offline).
DATA_MODE = os.getenv("MCP_DATA_MODE", "direct").strip().lower()


class BackendError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _http_client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=float(os.getenv("MCP_HTTP_TIMEOUT_S", "8")))


# ----- Incidents -----


def create_incident(payload: dict[str, Any]) -> dict[str, Any]:
    if DATA_MODE == "direct":
        from app.incidents.models import IncidentCreate
        from app.incidents.repository import IncidentRepository

        repo = IncidentRepository()
        try:
            created = repo.create(IncidentCreate.model_validate(payload))
            return created.model_dump(mode="json")
        finally:
            repo.close()

    with _http_client() as client:
        r = client.post("/api/incidents", json=payload)
        if r.status_code >= 400:
            raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
        return r.json()


def get_incident(incident_id: int) -> dict[str, Any] | None:
    if DATA_MODE == "direct":
        from app.incidents.repository import IncidentRepository

        repo = IncidentRepository()
        try:
            item = repo.get(incident_id)
            return item.model_dump(mode="json") if item else None
        finally:
            repo.close()

    with _http_client() as client:
        r = client.get(f"/api/incidents/{incident_id}")
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
        return r.json()


def list_incidents(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = {k: v for k, v in (filters or {}).items() if v is not None}
    if DATA_MODE == "direct":
        from app.incidents.repository import IncidentRepository

        repo = IncidentRepository()
        try:
            items = repo.list(
                status=filters.get("status"),
                origin=filters.get("origin"),
                branch=filters.get("branch"),
                category=filters.get("category"),
            )
            return [i.model_dump(mode="json") for i in items]
        finally:
            repo.close()

    with _http_client() as client:
        r = client.get("/api/incidents", params=filters)
        if r.status_code >= 400:
            raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
        return list(r.json())


def update_incident_status(incident_id: int, status: str) -> dict[str, Any]:
    """MUST use PATCH /api/incidents/{id}/status — never a generic resource PATCH."""
    if DATA_MODE == "direct":
        from app.incidents.models import IncidentStatus
        from app.incidents.repository import IncidentRepository

        repo = IncidentRepository()
        try:
            existing = repo.get(incident_id)
            if existing is None:
                raise BackendError("Incidencia no encontrada", status_code=404)
            try:
                updated = repo.update_status(incident_id, IncidentStatus(status))
            except ValueError as exc:
                raise BackendError(str(exc), status_code=400) from exc
            assert updated is not None
            return updated.model_dump(mode="json")
        finally:
            repo.close()

    with _http_client() as client:
        r = client.patch(
            f"/api/incidents/{incident_id}/status",
            json={"status": status},
        )
        if r.status_code >= 400:
            raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
        return r.json()


# ----- Inventory (read path) -----


def query_products(
    *,
    product_id: int | None = None,
    name_query: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if DATA_MODE == "direct":
        from sqlmodel import Session, select

        from app.database import engine
        from app.inventory.models import Ingredient
        from app.inventory.stock import stock_map_for_ids

        with Session(engine) as session:
            if product_id is not None:
                ingredient = session.get(Ingredient, product_id)
                if ingredient is None or ingredient.id is None:
                    return []
                stocks = stock_map_for_ids(session, [ingredient.id])
                return [_ingredient_dict(ingredient, stocks.get(ingredient.id, 0.0))]

            ingredients = list(
                session.exec(select(Ingredient).order_by(Ingredient.id)).all()
            )
            if name_query:
                q = name_query.lower()
                ingredients = [
                    i
                    for i in ingredients
                    if q in (i.name or "").lower() or q in (i.sku or "").lower()
                ]
            ingredients = ingredients[:limit]
            ids = [i.id for i in ingredients if i.id is not None]
            stocks = stock_map_for_ids(session, ids)
            return [
                _ingredient_dict(i, stocks.get(i.id, 0.0))
                for i in ingredients
                if i.id is not None
            ]

    headers = {}
    token = os.getenv("MCP_INVENTORY_BEARER", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with _http_client() as client:
        if product_id is not None:
            r = client.get(f"/inventory/products/{product_id}", headers=headers)
            if r.status_code == 404:
                return []
            if r.status_code >= 400:
                raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
            return [r.json()]
        r = client.get("/inventory/products", headers=headers)
        if r.status_code >= 400:
            raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
        products = list(r.json())
        if name_query:
            q = name_query.lower()
            products = [
                p
                for p in products
                if q in str(p.get("name", "")).lower()
                or q in str(p.get("sku", "")).lower()
            ]
        return products[:limit]


def _ingredient_dict(ingredient: Any, stock: float) -> dict[str, Any]:
    return {
        "id": ingredient.id,
        "name": ingredient.name,
        "sku": ingredient.sku,
        "unit": ingredient.unit,
        "category": ingredient.category,
        "country": ingredient.country,
        "current_stock": float(stock),
    }


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return response.text
