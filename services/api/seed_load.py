#!/usr/bin/env python3
"""Seed a realistic high-volume dataset for cache/latency measurements.

Creates varied incidents and extra suppliers (not identical "test" rows).
Idempotent via source_key / unique supplier names.

Usage (from repo root or services/api):
  cd services/api && uv run python seed_load.py
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
ROOT = API_DIR.parents[1]
sys.path.insert(0, str(API_DIR))
sys.path.insert(0, str(ROOT / "packages" / "shared" / "python"))

from app.incidents.models import (  # noqa: E402
    IncidentBranch,
    IncidentCategory,
    IncidentCreate,
    IncidentOrigin,
    IncidentStatus,
)
from app.incidents.repository import IncidentRepository  # noqa: E402
from app.suppliers.models import (  # noqa: E402
    Country,
    Currency,
    ProductCategory,
    SupplierCreate,
    SupplierStatus,
)
from app.suppliers.repository import SupplierRepository  # noqa: E402

INCIDENT_TARGET = 800
SUPPLIER_EXTRA = 40

TITLES = [
    "Horno lento en servicio noche",
    "Falta de carbón en pico viernes",
    "Queja por tiempo de espera delivery",
    "TPV reinicia durante cobro",
    "Fuga menor en cámara frigorífica",
    "Personal insuficiente en turno tarde",
    "Corte de nevera de salsas",
    "Pedido Glovo incompleto",
    "Cliente reporta plato frío",
    "Rotura de extractor cocina",
]

DESCRIPTIONS = [
    "Equipo reporta latencia al alcanzar temperatura objetivo.",
    "Stock del ítem crítico bajo el umbral operativo de apertura.",
    "Cliente solicita reembolso parcial; ticket adjunto en POS.",
    "Reinicio automático tras actualizar firmware; logs locales.",
    "Mantenimiento preventivo pendiente desde la semana anterior.",
    "Turno cubierto al 70%; impacto en ticket medio.",
    "Temperatura fuera de rango 8 minutos; se estabilizó.",
    "Faltaba guarnición en 3 pedidos consecutivos de la misma zona.",
    "Tiempo mesa→entrega superior a 25 minutos en hora punta.",
    "Pieza de recambio pedida al proveedor de mantenimiento.",
]


def _seed_incidents(rng: random.Random) -> tuple[int, int, int]:
    repo = IncidentRepository()
    inserted = 0
    skipped = 0
    categories = list(IncidentCategory)
    origins = list(IncidentOrigin)
    branches = list(IncidentBranch)
    statuses = list(IncidentStatus)
    base = datetime.now(timezone.utc) - timedelta(days=120)

    try:
        for i in range(INCIDENT_TARGET):
            source_key = f"load-cache-{i:04d}"
            if repo.get_by_source_key(source_key) is not None:
                skipped += 1
                continue
            created_at = base + timedelta(
                hours=rng.randint(0, 120 * 24),
                minutes=rng.randint(0, 59),
            )
            status = rng.choice(statuses)
            payload = IncidentCreate(
                title=f"{rng.choice(TITLES)} · lote {i % 17}",
                description=f"{rng.choice(DESCRIPTIONS)} Ref #{1000 + i}.",
                category=rng.choice(categories),
                origin=rng.choice(origins),
                branch=rng.choice(branches),
            )
            repo.create(
                payload,
                status=status,
                created_at=created_at,
                updated_at=created_at + timedelta(minutes=rng.randint(0, 180)),
                source_key=source_key,
            )
            inserted += 1
        summary = repo.summary()
        total = summary.total
    finally:
        repo.close()
    return inserted, skipped, total


def _seed_suppliers(rng: random.Random) -> tuple[int, int, int]:
    repo = SupplierRepository()
    inserted = 0
    skipped = 0
    categories = list(ProductCategory)
    cities_co = ["Medellín", "Bogotá", "Cali", "Barranquilla", "Envigado"]
    cities_us = ["Miami", "Orlando", "Fort Lauderdale", "Doral"]

    try:
        for i in range(SUPPLIER_EXTRA):
            country = Country.COLOMBIA if i % 3 else Country.USA
            city = rng.choice(cities_co if country is Country.COLOMBIA else cities_us)
            name = f"Brasaland Supply {city} #{i + 1:02d}"
            if repo.name_exists(name):
                skipped += 1
                continue
            cats = rng.sample(categories, k=rng.randint(1, 3))
            rate = (
                round(rng.uniform(1200, 85000), 2)
                if country is Country.COLOMBIA
                else round(rng.uniform(1.5, 48.0), 2)
            )
            payload = SupplierCreate(
                name=name,
                country=country,
                categories=cats,
                rate_per_unit=rate,
                currency=Currency.COP if country is Country.COLOMBIA else Currency.USD,
                status=SupplierStatus.ACTIVE if i % 7 else SupplierStatus.SUSPENDED,
                contact_email=f"compras.{i + 1}@{city.lower().replace(' ', '')}.brasaland.test",
                notes=f"Ruta {city}; lead time {rng.randint(1, 5)} días; MOQ {rng.choice([10, 25, 50])}.",
            )
            repo.create(payload)
            inserted += 1
        total = len(repo.list())
    finally:
        repo.close()
    return inserted, skipped, total


def main() -> int:
    rng = random.Random(42)
    try:
        inc_ins, inc_skip, inc_total = _seed_incidents(rng)
        sup_ins, sup_skip, sup_total = _seed_suppliers(rng)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR — seed_load falló: {exc}", file=sys.stderr)
        return 1

    print(
        f"Incidents: +{inc_ins} (skip {inc_skip}) → total {inc_total}\n"
        f"Suppliers: +{sup_ins} (skip {sup_skip}) → total {sup_total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
