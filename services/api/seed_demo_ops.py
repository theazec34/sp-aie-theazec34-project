"""Seed demo rico multi-sede para probar BrasAI / Agente / backoffice.

Idempotente: usa emails/SKU/source_key estables. Fuerza con SEED_DEMO_FORCE=1.

Incluye:
- Proveedores por sede (notes branch=<id>, tarifas EUR)
- Reservas (hoy / mañana) y candidaturas
- Entradas/salidas de inventario con nombres de proveedor reales
- Incidencias por sede
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlmodel import Session, select

from app.database import engine, init_db
from app.incidents.models import (
    IncidentBranch,
    IncidentCategory,
    IncidentCreate,
    IncidentOrigin,
    IncidentStatus,
)
from app.incidents.repository import IncidentRepository
from app.inventory import models as _inventory_models  # noqa: F401
from app.inventory.models import Ingredient, IngredientEntry, IngredientExit
from app.public_intake.models import CareerCreate, ReservationCreate
from app.public_intake.repository import PublicIntakeRepository
from app.suppliers.models import (
    Country,
    Currency,
    ProductCategory,
    SupplierCreate,
    SupplierStatus,
)
from app.suppliers.repository import SupplierRepository
from app.suppliers.seed_data import SUPPLIERS_SEED
from app.users.repository import UserRepository

# Sedes demo (alineadas con INCIDENT_BRANCHES del backoffice)
DEMO_BRANCHES: list[tuple[str, str, Country]] = [
    ("medellin_centro", "Medellín Centro", Country.COLOMBIA),
    ("medellin_laureles", "Medellín Laureles", Country.COLOMBIA),
    ("bogota_chapinero", "Bogotá Chapinero", Country.COLOMBIA),
    ("cali_granada", "Cali Granada", Country.COLOMBIA),
    ("miami_doral", "Miami Doral", Country.USA),
    ("miami_hialeah", "Miami Hialeah", Country.USA),
    ("miami_kendall", "Miami Kendall", Country.USA),
    ("fort_lauderdale", "Fort Lauderdale", Country.USA),
    ("orlando_international", "Orlando International", Country.USA),
]

# location_id numérico usado en inventario ORM (mapa estable)
BRANCH_LOCATION_ID: dict[str, int] = {
    "medellin_centro": 1,
    "medellin_laureles": 2,
    "bogota_chapinero": 3,
    "cali_granada": 4,
    "miami_doral": 10,
    "miami_hialeah": 11,
    "miami_kendall": 12,
    "fort_lauderdale": 13,
    "orlando_international": 14,
}


def _force() -> bool:
    return os.getenv("SEED_DEMO_FORCE", "").strip().lower() in {"1", "true", "yes"}


def _user_uuid() -> str:
    users = UserRepository()
    try:
        listed = users.list()
        return str(listed[0].id) if listed else "1"
    finally:
        users.close()


def seed_suppliers_by_branch() -> dict[str, int]:
    """Base EUR directory + un proveedor carne/verdura por sede."""
    repo = SupplierRepository()
    created = 0
    try:
        if _force() or repo.count() == 0:
            if _force():
                repo.replace_all(SUPPLIERS_SEED)
                created += len(SUPPLIERS_SEED)
            else:
                ins, _ = repo.seed_if_empty(SUPPLIERS_SEED)
                created += ins

        rates = [22.5, 18.9, 16.4, 14.2, 31.0, 28.5, 25.0, 27.8, 29.2]
        for i, (branch, label, country) in enumerate(DEMO_BRANCHES):
            meat_name = f"Carnes {label} Demo"
            veg_name = f"Huerta {label} Demo"
            for name, cat, rate in (
                (meat_name, ProductCategory.CARNE, rates[i % len(rates)]),
                (
                    veg_name,
                    ProductCategory.VERDURAS,
                    round(1.8 + (i % 5) * 0.35, 2),
                ),
            ):
                if repo.name_exists(name):
                    continue
                repo.create(
                    SupplierCreate(
                        name=name,
                        country=country,
                        categories=[cat],
                        rate_per_unit=rate,
                        currency=Currency.EUR,
                        status=SupplierStatus.ACTIVE,
                        contact_email=(
                            f"pedidos.{branch.replace('_', '.')}@example.com"
                        ),
                        notes=(
                            f"branch={branch}; sede={label}; "
                            f"entrega local 48h; tarifa EUR demo."
                        ),
                    )
                )
                created += 1
        return {"suppliers_total": repo.count(), "suppliers_created": created}
    finally:
        repo.close()


def seed_reservations_and_careers() -> dict[str, int]:
    repo = PublicIntakeRepository()
    res_n = 0
    car_n = 0
    try:
        if repo.db_path.exists() and repo.db_path.stat().st_size == 0:
            repo.db_path.write_text("{}\n", encoding="utf-8")
            repo.close()
            repo = PublicIntakeRepository()

        existing_res = {r.email.lower() for r in repo.list_reservations()}
        existing_car = {c.email.lower() for c in repo.list_careers()}
        today = date.today()
        tomorrow = today + timedelta(days=1)

        guests_cycle = [2, 3, 4, 5, 6, 8]
        hours = [13, 14, 20, 21, 22]
        for i, (branch, label, _) in enumerate(DEMO_BRANCHES):
            for day_offset, day in ((0, today), (1, tomorrow)):
                email = f"reserva.{branch}.{day_offset}@example.com"
                if email in existing_res and not _force():
                    continue
                if email in existing_res and _force():
                    # TinyDB no tiene delete-by-email fácil → skip duplicates
                    continue
                repo.create_reservation(
                    ReservationCreate(
                        full_name=f"Cliente Demo {label}",
                        phone=f"+34 600 {100 + i:03d} {day_offset}{i % 10}",
                        email=email,
                        date=day,
                        time=time(hours[i % len(hours)], 0),
                        guests=guests_cycle[i % len(guests_cycle)],
                        notes=(
                            f"[sede:{branch}] Reserva demo {label}. "
                            f"{'Hoy' if day_offset == 0 else 'Mañana'}."
                        ),
                    )
                )
                res_n += 1
                existing_res.add(email)

            car_email = f"candidato.{branch}@example.com"
            if car_email not in existing_car:
                dept = ("Sala", "Cocina", "Barra")[i % 3]
                repo.create_career(
                    CareerCreate(
                        name=f"Candidato {label}",
                        email=car_email,
                        phone=f"+57 300 {200 + i:03d} {1000 + i}",
                        department=dept,
                        experience_years=1 + (i % 6),
                        message=(
                            f"Interesado en {dept} en {label} ({branch}). "
                            "Disponibilidad fines de semana y turnos noche."
                        ),
                        cv_filename=f"cv-{branch}.pdf",
                        privacy_accepted=True,
                    )
                )
                car_n += 1

        return {
            "reservations_created": res_n,
            "reservations_total": len(repo.list_reservations()),
            "careers_created": car_n,
            "careers_total": len(repo.list_careers()),
        }
    finally:
        repo.close()


def seed_inventory_movements() -> dict[str, int]:
    """Más entradas/salidas ligadas a proveedores demo (para preguntas de kg)."""
    init_db()
    user_uuid = _user_uuid()
    created_e = 0
    created_x = 0
    with Session(engine) as session:
        ingredients = list(session.exec(select(Ingredient)).all())
        if not ingredients:
            return {"entries": 0, "exits": 0, "note": "run seed_inventory first"}

        by_sku = {i.sku: i for i in ingredients if i.sku}
        beef = by_sku.get("BRS-BEEF-001")
        pork = by_sku.get("BRS-PORK-001")
        sauce = by_sku.get("BRS-SAUCE-001")
        if not beef or not pork:
            return {"entries": 0, "exits": 0, "note": "missing core SKUs"}

        existing_keys = {
            (e.supplier_name, e.location_id, float(e.quantity), e.ingredient_id)
            for e in session.exec(select(IngredientEntry)).all()
        }

        plans: list[tuple[Ingredient, str, str, float]] = []
        for branch, label, _ in DEMO_BRANCHES:
            loc = BRANCH_LOCATION_ID[branch]
            plans.append(
                (beef, f"Carnes {label} Demo", branch, 25.0 + loc)
            )
            plans.append(
                (pork if "miami" in branch or "orlando" in branch or "fort" in branch else beef,
                 f"Carnes {label} Demo",
                 branch,
                 15.0 + (loc % 7)),
            )
            if sauce:
                plans.append((sauce, f"Huerta {label} Demo", branch, 8.0))

        for ing, supplier, branch, qty in plans:
            loc = BRANCH_LOCATION_ID[branch]
            key = (supplier, loc, float(qty), ing.id)
            if key in existing_keys:
                continue
            session.add(
                IngredientEntry(
                    ingredient_id=ing.id,  # type: ignore[arg-type]
                    quantity=float(qty),
                    supplier_name=supplier,
                    location_id=loc,
                    user_uuid=user_uuid,
                )
            )
            created_e += 1
            existing_keys.add(key)

        # Salidas de consumo/merma en sedes clave
        exit_plans = [
            (beef, 1, 6.0, "consumption"),
            (beef, 10, 4.5, "consumption"),
            (pork, 10, 3.0, "consumption"),
            (pork, 13, 2.0, "waste"),
            (sauce, 3, 1.0, "waste") if sauce else None,
            (beef, 2, 5.0, "consumption"),
        ]
        existing_exits = len(list(session.exec(select(IngredientExit)).all()))
        if existing_exits < 8:
            for plan in exit_plans:
                if plan is None:
                    continue
                ing, loc, qty, reason = plan
                session.add(
                    IngredientExit(
                        ingredient_id=ing.id,  # type: ignore[arg-type]
                        quantity=qty,
                        reason=reason,
                        location_id=loc,
                        user_uuid=user_uuid,
                    )
                )
                created_x += 1

        session.commit()
        n_e = len(list(session.exec(select(IngredientEntry)).all()))
        n_x = len(list(session.exec(select(IngredientExit)).all()))
    return {
        "entries_created": created_e,
        "exits_created": created_x,
        "entries_total": n_e,
        "exits_total": n_x,
    }


def seed_incidents_by_branch() -> dict[str, int]:
    repo = IncidentRepository()
    created = 0
    try:
        titles = [
            "Horno lento en servicio",
            "Falta de carbón en pico",
            "Queja de tiempo de espera",
            "Nevera con alarma de temperatura",
        ]
        for i, (branch, label, _) in enumerate(DEMO_BRANCHES):
            source_key = f"demo-ops-{branch}"
            if repo.get_by_source_key(source_key) is not None:
                continue
            try:
                branch_enum = IncidentBranch(branch)
            except ValueError:
                branch_enum = IncidentBranch.MIAMI_DORAL
            repo.create(
                IncidentCreate(
                    title=f"{titles[i % len(titles)]} — {label}",
                    description=(
                        f"Incidencia demo en {label} ({branch}) para pruebas "
                        "del agente de soporte."
                    ),
                    category=(
                        IncidentCategory.EQUIPMENT_FAILURE
                        if i % 2 == 0
                        else IncidentCategory.CUSTOMER_COMPLAINT
                    ),
                    origin=IncidentOrigin.BRANCH,
                    branch=branch_enum,
                ),
                status=(
                    IncidentStatus.OPEN
                    if i % 3
                    else IncidentStatus.IN_PROGRESS
                ),
                created_at=datetime.now(timezone.utc) - timedelta(hours=i * 3),
                source_key=source_key,
            )
            created += 1
        return {
            "incidents_created": created,
            "incidents_total": repo.summary().total,
        }
    finally:
        repo.close()


def main() -> int:
    print("Brasaland — Demo ops seeder (multi-sede)")
    print(f"  Force ........... {_force()}")
    stats: dict[str, object] = {}
    try:
        stats.update(seed_suppliers_by_branch())
        stats.update(seed_reservations_and_careers())
        # inventario base primero (SKUs)
        from seed_inventory import main as seed_inv_main

        seed_inv_main()
        stats.update(seed_inventory_movements())
        stats.update(seed_incidents_by_branch())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR — seed_demo_ops: {exc}", file=sys.stderr)
        return 1

    for k, v in stats.items():
        print(f"  {k:22} {v}")
    print("OK — demo multi-sede listo para preguntas del agente / backoffice.")
    print(
        "Prueba: «¿Cuál es el proveedor con la tarifa más alta en €?» · "
        "«¿Qué proveedor nos ha enviado más kg?» · "
        "Reservas web / Candidaturas en el panel."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
