#!/usr/bin/env python3
"""Seed TinyDB with the Brasaland supplier directory from CONTEXT."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.suppliers.repository import SupplierRepository
from app.suppliers.seed_data import SUPPLIERS_SEED


def main() -> int:
    repo = SupplierRepository()
    before = repo.count()
    inserted, skipped = repo.seed_if_empty(SUPPLIERS_SEED)
    after = repo.count()
    repo.close()

    print("Brasaland — Supplier directory seeder")
    print(f"  Database ........ {repo.db_path}")
    print(f"  Before .......... {before}")
    print(f"  Inserted ....... {inserted}")
    print(f"  Skipped ......... {skipped} (already present)")
    print(f"  After ........... {after}")
    if inserted:
        print(f"OK — {inserted} proveedor(es) cargado(s).")
    else:
        print("OK — no hay cambios (directorio ya sembrado).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
