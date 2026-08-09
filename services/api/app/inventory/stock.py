"""Stock calculation helpers — current_stock is never persisted."""

from __future__ import annotations

from sqlmodel import Session, col, func, select

from app.inventory.models import Ingredient, IngredientEntry, IngredientExit
from app.inventory.schemas import IngredientRead


def sum_entries(session: Session, ingredient_id: int) -> float:
    total = session.exec(
        select(func.coalesce(func.sum(IngredientEntry.quantity), 0.0)).where(
            IngredientEntry.ingredient_id == ingredient_id
        )
    ).one()
    return float(total)


def sum_exits(session: Session, ingredient_id: int) -> float:
    total = session.exec(
        select(func.coalesce(func.sum(IngredientExit.quantity), 0.0)).where(
            IngredientExit.ingredient_id == ingredient_id
        )
    ).one()
    return float(total)


def current_stock(session: Session, ingredient_id: int) -> float:
    return sum_entries(session, ingredient_id) - sum_exits(session, ingredient_id)


def to_ingredient_read(session: Session, ingredient: Ingredient) -> IngredientRead:
    return IngredientRead(
        id=ingredient.id,  # type: ignore[arg-type]
        name=ingredient.name,
        sku=ingredient.sku,
        unit=ingredient.unit,
        category=ingredient.category,
        country=ingredient.country,
        current_stock=current_stock(session, ingredient.id),  # type: ignore[arg-type]
    )


def stock_map_for_ids(session: Session, ingredient_ids: list[int]) -> dict[int, float]:
    """Bulk stock for a set of ingredients (avoids N+1 on list endpoints)."""
    if not ingredient_ids:
        return {}

    entry_rows = session.exec(
        select(
            IngredientEntry.ingredient_id,
            func.coalesce(func.sum(IngredientEntry.quantity), 0.0),
        )
        .where(col(IngredientEntry.ingredient_id).in_(ingredient_ids))
        .group_by(IngredientEntry.ingredient_id)
    ).all()
    exit_rows = session.exec(
        select(
            IngredientExit.ingredient_id,
            func.coalesce(func.sum(IngredientExit.quantity), 0.0),
        )
        .where(col(IngredientExit.ingredient_id).in_(ingredient_ids))
        .group_by(IngredientExit.ingredient_id)
    ).all()

    entries = {int(i): float(q) for i, q in entry_rows}
    exits = {int(i): float(q) for i, q in exit_rows}
    return {iid: entries.get(iid, 0.0) - exits.get(iid, 0.0) for iid in ingredient_ids}
