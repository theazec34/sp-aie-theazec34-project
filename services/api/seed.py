#!/usr/bin/env python3
"""Seed TinyDB with the Brasaland supplier directory from CONTEXT."""

from __future__ import annotations

import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.suppliers.repository import SupplierRepository
from app.suppliers.seed_data import SUPPLIERS_SEED


def main() -> int:
    force = (
        "--force" in sys.argv
        or os.getenv("SEED_SUPPLIERS_FORCE", "").strip() in {"1", "true", "yes"}
    )
    repo = SupplierRepository()
    try:
        before = repo.count()
        if force:
            inserted = repo.replace_all(SUPPLIERS_SEED)
            skipped = 0
        else:
            inserted, skipped = repo.seed_if_empty(SUPPLIERS_SEED)
        after = repo.count()
    except OSError as exc:
        print(f"ERROR — no se pudo acceder a la base TinyDB: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR — seeder de proveedores falló: {exc}", file=sys.stderr)
        return 1
    finally:
        repo.close()

    print("Brasaland — Supplier directory seeder")
    print(f"  Database ........ {repo.db_path}")
    print(f"  Force ........... {force}")
    print(f"  Before .......... {before}")
    print(f"  Inserted ....... {inserted}")
    print(f"  Skipped ......... {skipped}")
    print(f"  After ........... {after}")
    if force:
        print(f"OK — directorio reemplazado ({inserted} proveedores, tarifas EUR).")
    elif inserted:
        print(f"OK — {inserted} proveedor(es) cargado(s).")
    else:
        print("OK — no hay cambios (usa --force o SEED_SUPPLIERS_FORCE=1 para EUR).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
