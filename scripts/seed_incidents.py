#!/usr/bin/env python3
"""Seed historical customer incidents from incidents-brasaland.csv (idempotent)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_PYTHON = ROOT / "packages" / "shared" / "python"
API_DIR = ROOT / "services" / "api"

sys.path.insert(0, str(SHARED_PYTHON))
sys.path.insert(0, str(API_DIR))

from brasaland_incidents.mapping import map_csv_row  # noqa: E402
from app.incidents.models import (  # noqa: E402
    IncidentBranch,
    IncidentCategory,
    IncidentCreate,
    IncidentOrigin,
    IncidentStatus,
)
from app.incidents.repository import IncidentRepository  # noqa: E402

DEFAULT_CSV = ROOT / "incidents-brasaland.csv"


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not csv_path.is_file():
        print(f"ERROR — no se encuentra el CSV: {csv_path}")
        return 1

    repo = IncidentRepository()
    inserted = 0
    skipped_dup = 0
    discarded: list[str] = []

    try:
        with csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=2):
                mapped, reason = map_csv_row(row)
                if mapped is None:
                    discarded.append(f"L{index}: {reason}")
                    continue

                if repo.get_by_source_key(mapped.source_key) is not None:
                    skipped_dup += 1
                    continue

                payload = IncidentCreate(
                    title=mapped.title,
                    description=mapped.description,
                    category=IncidentCategory(mapped.category),
                    origin=IncidentOrigin(mapped.origin),
                    branch=IncidentBranch(mapped.branch),
                )
                repo.create(
                    payload,
                    status=IncidentStatus(mapped.status),
                    created_at=mapped.created_at,
                    updated_at=mapped.created_at,
                    source_key=mapped.source_key,
                )
                inserted += 1

        summary = repo.summary()
    finally:
        repo.close()

    print(f"CSV: {csv_path.name}")
    print(f"Insertadas: {inserted}")
    print(f"Omitidas (ya existían): {skipped_dup}")
    print(f"Descartadas (inválidas/no mapeables): {len(discarded)}")
    if discarded:
        print("--- Detalle descartadas ---")
        for line in discarded:
            print(line)
    print("--- Summary (modelo) ---")
    print(f"total={summary.total}")
    print(f"by_status={summary.by_status}")
    print(f"by_category={dict((k, v) for k, v in summary.by_category.items() if v)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
