"""Inventory stock lookup tool — reads real inventory ORM (GET only).

Auth note: HTTP ``GET /inventory/products`` requires JWT. This tool uses the
in-process SQLModel session (same service layer as the API) so the agent can
query stock without inventing data. No create/update/delete.
"""

from __future__ import annotations

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

from agent.tools.contracts import (
    InventoryLookupInput,
    InventoryLookupOutput,
    InventoryProductRecord,
)

logger = logging.getLogger("agent.tools.inventory")

DEFAULT_TIMEOUT_S = float(os.getenv("AGENT_TOOL_TIMEOUT_S", "4"))

_API = Path(__file__).resolve().parents[2] / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))


def _fetch_products(payload: InventoryLookupInput) -> InventoryLookupOutput:
    from sqlmodel import Session, select

    from app.database import engine
    from app.inventory.models import Ingredient
    from app.inventory.stock import stock_map_for_ids

    with Session(engine) as session:
        if payload.product_id is not None:
            ingredient = session.get(Ingredient, payload.product_id)
            if ingredient is None or ingredient.id is None:
                return InventoryLookupOutput(
                    ok=False,
                    error=f"Producto {payload.product_id} no encontrado",
                )
            stocks = stock_map_for_ids(session, [ingredient.id])
            rec = InventoryProductRecord(
                id=ingredient.id,
                name=ingredient.name,
                sku=ingredient.sku,
                unit=ingredient.unit,
                category=ingredient.category,
                country=ingredient.country,
                current_stock=float(stocks.get(ingredient.id, 0.0)),
            )
            return InventoryLookupOutput(ok=True, products=[rec])

        ingredients = list(
            session.exec(select(Ingredient).order_by(Ingredient.id)).all()
        )
        if payload.name_query:
            q = payload.name_query.lower()
            ingredients = [
                i
                for i in ingredients
                if q in (i.name or "").lower() or q in (i.sku or "").lower()
            ]
        ingredients = ingredients[: payload.limit]
        ids = [i.id for i in ingredients if i.id is not None]
        stocks = stock_map_for_ids(session, ids)
        products = [
            InventoryProductRecord(
                id=i.id,  # type: ignore[arg-type]
                name=i.name,
                sku=i.sku,
                unit=i.unit,
                category=i.category,
                country=i.country,
                current_stock=float(stocks.get(i.id, 0.0)),  # type: ignore[arg-type]
            )
            for i in ingredients
            if i.id is not None
        ]
        return InventoryLookupOutput(ok=True, products=products)


def lookup_inventory_stock(
    payload: InventoryLookupInput,
    *,
    timeout_s: float | None = None,
) -> InventoryLookupOutput:
    """Read-only inventory lookup with explicit timeout."""
    limit = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_fetch_products, payload)
            return future.result(timeout=limit)
    except FuturesTimeout:
        logger.warning("inventory tool timed out after %ss", limit)
        return InventoryLookupOutput(
            ok=False,
            timed_out=True,
            error=f"Timeout ({limit}s) al consultar inventario",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("inventory tool failed")
        return InventoryLookupOutput(
            ok=False,
            error=f"No se pudo consultar inventario: {type(exc).__name__}",
        )
