#!/usr/bin/env python3
"""Seed admin user + profile into TinyDB (idempotent by email).

Credenciales SOLO desde entorno — nunca hardcodear passwords en el repo
(OWASP A02 / BRIEFING AI-secure).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.auth.security import hash_password
from app.profiles.repository import ProfileRepository
from app.users.models import UserRole
from app.users.repository import UserRepository


def main() -> int:
    email = (os.environ.get("SEED_ADMIN_EMAIL") or "").strip()
    password = os.environ.get("SEED_ADMIN_PASSWORD") or ""
    name = (os.environ.get("SEED_ADMIN_NAME") or "Admin Brasaland").strip()

    if not email or not password:
        print(
            "ERROR — define SEED_ADMIN_EMAIL y SEED_ADMIN_PASSWORD en el entorno "
            "(no hay credenciales por defecto en el código).",
            file=sys.stderr,
        )
        return 2
    if len(password) < 12:
        print(
            "ERROR — SEED_ADMIN_PASSWORD debe tener al menos 12 caracteres.",
            file=sys.stderr,
        )
        return 2

    users = UserRepository()
    profiles = ProfileRepository()
    try:
        # Migrar emails .local de semillas antiguas (email-validator los rechaza).
        for doc in list(users._table.all()):
            old = (doc.get("email") or "").strip().lower()
            if old.endswith(".local"):
                new = old[: -len(".local")] + ".com"
                users._table.update({"email": new}, doc_ids=[doc.doc_id])
                print(f"OK — migrado email {old} → {new}")

        existing = users.get_by_email(email)
        if existing is not None:
            if profiles.get_by_user_id(existing.id) is None:
                profiles.create(user_id=existing.id, name=name)
            print(f"OK — usuario ya existe (id={existing.id}, email={email})")
            return 0

        user = users.create(
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
        )
        profiles.create(user_id=user.id, name=name)
        print("Brasaland — Auth seeder")
        print(f"  Created admin id={user.id}")
        print(f"  Email ........... {email}")
        print(f"  Role ............ {user.role.value}")
        print("OK — admin sembrado (password hasheada en TinyDB).")
        return 0
    except OSError as exc:
        print(f"ERROR — no se pudo acceder a TinyDB: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR — seed_auth falló: {exc}", file=sys.stderr)
        return 1
    finally:
        users.close()
        profiles.close()


if __name__ == "__main__":
    raise SystemExit(main())
