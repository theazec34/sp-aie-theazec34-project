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


# ----- Suppliers (read path) -----


def list_suppliers(
    *,
    name_query: str | None = None,
    branch: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if DATA_MODE == "direct":
        from app.suppliers.repository import SupplierRepository
        from app.suppliers.seed_data import SUPPLIERS_SEED

        repo = SupplierRepository()
        try:
            # Codespaces: volumen vacío / seed fallido → rehidratar directorio base
            if repo.count() == 0:
                repo.seed_if_empty(SUPPLIERS_SEED)
            items = [s.model_dump(mode="json") for s in repo.list()]
        finally:
            repo.close()
    else:
        headers = {}
        token = os.getenv("MCP_INVENTORY_BEARER", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with _http_client() as client:
            r = client.get("/suppliers", headers=headers)
            if r.status_code >= 400:
                raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
            items = list(r.json())

    if name_query:
        q = name_query.lower()
        items = [
            s
            for s in items
            if q in str(s.get("name", "")).lower()
            or q in str(s.get("contact_email") or "").lower()
        ]
    if branch:
        b = branch.strip().lower()
        marker = f"branch={b}"
        filtered = [
            s
            for s in items
            if marker in str(s.get("notes") or "").lower()
            or b in str(s.get("notes") or "").lower()
        ]
        # Si no hay fichas por sede, devolver directorio global (seed base)
        if filtered:
            items = filtered
    return items[:limit]


def supplier_directory_summary(*, limit: int = 10) -> dict[str, Any]:
    """Rank suppliers by tariff (€) and basic counts — read-only."""
    suppliers = list_suppliers(limit=500)
    active = [s for s in suppliers if str(s.get("status", "")).lower() == "active"]
    ranked = sorted(
        suppliers,
        key=lambda s: float(s.get("rate_per_unit") or 0),
        reverse=True,
    )
    top = ranked[:limit]
    top_active = sorted(
        active,
        key=lambda s: float(s.get("rate_per_unit") or 0),
        reverse=True,
    )[:1]
    return {
        "count": len(suppliers),
        "active_count": len(active),
        "currency": "EUR",
        "top_by_rate_eur": top,
        "highest_rate_active": top_active[0] if top_active else None,
    }


# ----- Inventory movements / history -----


def list_inventory_orders(
    *,
    kind: str | None = None,
    name_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Unified inbound/outbound history (same shape as GET /inventory/orders)."""
    if DATA_MODE == "direct":
        from sqlmodel import Session, select
        from sqlalchemy.orm import selectinload

        from app.database import engine
        from app.inventory.models import IngredientEntry, IngredientExit

        orders: list[dict[str, Any]] = []
        with Session(engine) as session:
            entries = session.exec(
                select(IngredientEntry)
                .options(selectinload(IngredientEntry.ingredient))  # type: ignore[arg-type]
                .order_by(IngredientEntry.created_at.desc())  # type: ignore[union-attr]
            ).all()
            exits = session.exec(
                select(IngredientExit)
                .options(selectinload(IngredientExit.ingredient))  # type: ignore[arg-type]
                .order_by(IngredientExit.created_at.desc())  # type: ignore[union-attr]
            ).all()
            for entry in entries:
                ing = entry.ingredient
                if ing is None:
                    continue
                orders.append(
                    {
                        "kind": "inbound",
                        "id": entry.id,
                        "ingredient_id": entry.ingredient_id,
                        "quantity": float(entry.quantity),
                        "unit": getattr(ing, "unit", None),
                        "ingredient_name": ing.name,
                        "supplier_name": entry.supplier_name,
                        "reason": None,
                        "created_at": (
                            entry.created_at.isoformat()
                            if entry.created_at is not None
                            else None
                        ),
                    }
                )
            for exit_row in exits:
                ing = exit_row.ingredient
                if ing is None:
                    continue
                orders.append(
                    {
                        "kind": "outbound",
                        "id": exit_row.id,
                        "ingredient_id": exit_row.ingredient_id,
                        "quantity": float(exit_row.quantity),
                        "unit": getattr(ing, "unit", None),
                        "ingredient_name": ing.name,
                        "supplier_name": None,
                        "reason": exit_row.reason,
                        "created_at": (
                            exit_row.created_at.isoformat()
                            if exit_row.created_at is not None
                            else None
                        ),
                    }
                )
            orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)
    else:
        headers = {}
        token = os.getenv("MCP_INVENTORY_BEARER", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with _http_client() as client:
            r = client.get("/inventory/orders", headers=headers)
            if r.status_code >= 400:
                raise BackendError(r.text, status_code=r.status_code, body=_safe_json(r))
            raw = list(r.json())
        orders = []
        for row in raw:
            ing = row.get("ingredient") or {}
            orders.append(
                {
                    "kind": row.get("kind"),
                    "id": row.get("id"),
                    "ingredient_id": row.get("ingredient_id"),
                    "quantity": float(row.get("quantity") or 0),
                    "unit": ing.get("unit"),
                    "ingredient_name": ing.get("name"),
                    "supplier_name": row.get("supplier_name"),
                    "reason": row.get("reason"),
                    "created_at": row.get("created_at"),
                }
            )

    if kind in {"inbound", "outbound"}:
        orders = [o for o in orders if o.get("kind") == kind]
    if name_query:
        q = name_query.lower()
        orders = [
            o
            for o in orders
            if q in str(o.get("ingredient_name") or "").lower()
            or q in str(o.get("supplier_name") or "").lower()
        ]
    return orders[:limit]


def inventory_ops_summary(*, limit: int = 10) -> dict[str, Any]:
    """Aggregates: stock snapshot + inbound kg by supplier + outbound totals."""
    products = query_products(limit=200)
    orders = list_inventory_orders(limit=500)
    inbound = [o for o in orders if o.get("kind") == "inbound"]
    outbound = [o for o in orders if o.get("kind") == "outbound"]

    by_supplier: dict[str, float] = {}
    for o in inbound:
        name = (o.get("supplier_name") or "sin_proveedor").strip() or "sin_proveedor"
        by_supplier[name] = by_supplier.get(name, 0.0) + float(o.get("quantity") or 0)

    top_suppliers_kg = sorted(
        [{"supplier_name": k, "total_qty": v} for k, v in by_supplier.items()],
        key=lambda x: x["total_qty"],
        reverse=True,
    )[:limit]

    suppliers = list_suppliers(limit=200)
    rate_by_name = {
        str(s.get("name") or "").strip().lower(): float(s.get("rate_per_unit") or 0)
        for s in suppliers
    }
    for row in top_suppliers_kg:
        rate = rate_by_name.get(str(row["supplier_name"]).lower(), 0.0)
        row["rate_per_unit_eur"] = rate
        row["estimated_value_eur"] = round(rate * float(row["total_qty"]), 2)

    top_stock = sorted(
        products,
        key=lambda p: float(p.get("current_stock") or 0),
        reverse=True,
    )[:limit]

    return {
        "currency": "EUR",
        "products_count": len(products),
        "inbound_count": len(inbound),
        "outbound_count": len(outbound),
        "inbound_qty_total": round(sum(float(o.get("quantity") or 0) for o in inbound), 3),
        "outbound_qty_total": round(
            sum(float(o.get("quantity") or 0) for o in outbound), 3
        ),
        "top_suppliers_by_inbound_qty": top_suppliers_kg,
        "top_stock": top_stock,
        "highest_tariff_supplier": supplier_directory_summary(limit=1).get(
            "highest_rate_active"
        ),
    }


def list_reservations_ops(
    *,
    branch: str | None = None,
    day: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Reservas del intake público (filtrable por sede en notes y por día)."""
    from datetime import date as date_cls

    from app.public_intake.repository import PublicIntakeRepository

    repo = PublicIntakeRepository()
    try:
        rows = [r.model_dump(mode="json") for r in repo.list_reservations()]
    finally:
        repo.close()

    if day in {"today", "hoy"}:
        target = date_cls.today().isoformat()
        rows = [r for r in rows if str(r.get("date") or "")[:10] == target]
    elif day in {"tomorrow", "manana", "mañana"}:
        from datetime import timedelta

        target = (date_cls.today() + timedelta(days=1)).isoformat()
        rows = [r for r in rows if str(r.get("date") or "")[:10] == target]

    if branch:
        b = branch.strip().lower()
        marker = f"[sede:{b}]"
        rows = [
            r
            for r in rows
            if marker in str(r.get("notes") or "").lower()
            or b in str(r.get("notes") or "").lower()
        ]
    rows.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("time") or "")))
    return rows[:limit]


def list_careers_ops(
    *,
    branch: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Candidaturas web (filtro blando por sede en message/email)."""
    from app.public_intake.repository import PublicIntakeRepository

    repo = PublicIntakeRepository()
    try:
        rows = [c.model_dump(mode="json") for c in repo.list_careers()]
    finally:
        repo.close()

    if branch:
        b = branch.strip().lower()
        rows = [
            r
            for r in rows
            if b in str(r.get("message") or "").lower()
            or b in str(r.get("email") or "").lower()
            or b in str(r.get("name") or "").lower()
        ]
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return rows[:limit]


def front_ops_summary(
    *,
    branch: str | None = None,
) -> dict[str, Any]:
    res_today = list_reservations_ops(branch=branch, day="today", limit=100)
    res_tomorrow = list_reservations_ops(branch=branch, day="tomorrow", limit=100)
    careers = list_careers_ops(branch=branch, limit=100)
    guests_today = sum(int(r.get("guests") or 0) for r in res_today)
    return {
        "branch": branch,
        "reservations_today": len(res_today),
        "guests_today": guests_today,
        "reservations_tomorrow": len(res_tomorrow),
        "careers_total": len(careers),
        "sample_reservations_today": res_today[:8],
        "sample_careers": careers[:8],
    }


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return response.text
