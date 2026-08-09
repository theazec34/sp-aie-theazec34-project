#!/usr/bin/env python3
"""Seed demo inventory data (idempotent by ingredient SKU).

CONTEXT: ≥6 ingredients, ≥4 entries, ≥3 exits (incl. one waste).
`user_uuid` = TinyDB numeric user id as string (e.g. "1").
"""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlmodel import Session, select

from app.database import engine, init_db
from app.inventory import models as _inventory_models  # noqa: F401
from app.inventory.models import Ingredient, IngredientEntry, IngredientExit
from app.users.repository import UserRepository

INGREDIENTS = [
    {
        "name": "Falda de ternera",
        "sku": "BRS-BEEF-001",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
    },
    {
        "name": "Costilla de cerdo",
        "sku": "BRS-PORK-001",
        "unit": "kg",
        "category": "meat",
        "country": "US",
    },
    {
        "name": "Chimichurri",
        "sku": "BRS-SAUCE-001",
        "unit": "litro",
        "category": "sauce",
        "country": "CO",
    },
    {
        "name": "Salsa BBQ de la casa",
        "sku": "BRS-SAUCE-002",
        "unit": "litro",
        "category": "sauce",
        "country": "US",
    },
    {
        "name": "Yuca",
        "sku": "BRS-PROD-001",
        "unit": "kg",
        "category": "produce",
        "country": "CO",
    },
    {
        "name": "Caja para llevar (M)",
        "sku": "BRS-PKG-001",
        "unit": "unidad",
        "category": "packaging",
        "country": "CO",
    },
]


def _resolve_user_uuid() -> str:
    users = UserRepository()
    try:
        listed = users.list()
        if not listed:
            print(
                "WARN — no hay usuarios en TinyDB; user_uuid='1'. "
                "Ejecuta antes: PYTHONPATH=. python seed_auth.py",
                file=sys.stderr,
            )
            return "1"
        return str(listed[0].id)
    finally:
        users.close()


def main() -> int:
    init_db()
    user_uuid = _resolve_user_uuid()

    with Session(engine) as session:
        by_sku: dict[str, Ingredient] = {}
        created_ingredients = 0
        for row in INGREDIENTS:
            existing = session.exec(
                select(Ingredient).where(Ingredient.sku == row["sku"])
            ).first()
            if existing is None:
                ingredient = Ingredient(**row)
                session.add(ingredient)
                session.commit()
                session.refresh(ingredient)
                created_ingredients += 1
                by_sku[row["sku"]] = ingredient
            else:
                by_sku[row["sku"]] = existing

        entry_count = session.exec(select(IngredientEntry)).all()
        if len(entry_count) == 0:
            beef = by_sku["BRS-BEEF-001"]
            pork = by_sku["BRS-PORK-001"]
            sauce = by_sku["BRS-SAUCE-001"]
            entries = [
                IngredientEntry(
                    ingredient_id=beef.id,  # type: ignore[arg-type]
                    quantity=50.0,
                    supplier_name="Carnes del Valle S.A.",
                    location_id=1,
                    user_uuid=user_uuid,
                ),
                IngredientEntry(
                    ingredient_id=beef.id,  # type: ignore[arg-type]
                    quantity=30.0,
                    supplier_name="Carnes del Valle S.A.",
                    location_id=2,
                    user_uuid=user_uuid,
                ),
                IngredientEntry(
                    ingredient_id=pork.id,  # type: ignore[arg-type]
                    quantity=40.0,
                    supplier_name="MiamiMeat Co.",
                    location_id=10,
                    user_uuid=user_uuid,
                ),
                IngredientEntry(
                    ingredient_id=sauce.id,  # type: ignore[arg-type]
                    quantity=20.0,
                    supplier_name="Salsas Artesanales Ltda.",
                    location_id=3,
                    user_uuid=user_uuid,
                ),
            ]
            for entry in entries:
                session.add(entry)
            session.commit()
            created_entries = len(entries)
        else:
            created_entries = 0

        exit_count = session.exec(select(IngredientExit)).all()
        if len(exit_count) == 0:
            beef = by_sku["BRS-BEEF-001"]
            pork = by_sku["BRS-PORK-001"]
            sauce = by_sku["BRS-SAUCE-001"]
            exits = [
                IngredientExit(
                    ingredient_id=beef.id,  # type: ignore[arg-type]
                    quantity=12.0,
                    reason="consumption",
                    location_id=1,
                    user_uuid=user_uuid,
                ),
                IngredientExit(
                    ingredient_id=pork.id,  # type: ignore[arg-type]
                    quantity=5.0,
                    reason="consumption",
                    location_id=10,
                    user_uuid=user_uuid,
                ),
                IngredientExit(
                    ingredient_id=sauce.id,  # type: ignore[arg-type]
                    quantity=1.5,
                    reason="waste",
                    location_id=3,
                    user_uuid=user_uuid,
                ),
            ]
            for exit_row in exits:
                session.add(exit_row)
            session.commit()
            created_exits = len(exits)
        else:
            created_exits = 0

        n_ing = len(session.exec(select(Ingredient)).all())
        n_ent = len(session.exec(select(IngredientEntry)).all())
        n_ex = len(session.exec(select(IngredientExit)).all())

    print("Brasaland — Inventory seeder")
    print(f"  user_uuid ........ {user_uuid}  (TinyDB numeric id as str)")
    print(f"  ingredients ...... {n_ing} (+{created_ingredients} new)")
    print(f"  entries .......... {n_ent} (+{created_entries} new)")
    print(f"  exits ............ {n_ex} (+{created_exits} new)")
    print("OK — inventario sembrado (stock = entries − exits).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
