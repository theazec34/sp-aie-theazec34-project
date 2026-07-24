#!/usr/bin/env python3
"""Seed admin user + profile into TinyDB (idempotent by email)."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.auth.security import hash_password
from app.profiles.repository import ProfileRepository
from app.users.models import UserRole
from app.users.repository import UserRepository

ADMIN_EMAIL = "alfredobormujo@gmail.com"
ADMIN_PASSWORD = "alfreditopambi12"
ADMIN_NAME = "Alfredo Bormujo"


def main() -> int:
    users = UserRepository()
    profiles = ProfileRepository()
    try:
        existing = users.get_by_email(ADMIN_EMAIL)
        if existing is not None:
            if profiles.get_by_user_id(existing.id) is None:
                profiles.create(user_id=existing.id, name=ADMIN_NAME)
            print(f"OK — usuario ya existe (id={existing.id}, email={ADMIN_EMAIL})")
            return 0

        user = users.create(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        profiles.create(user_id=user.id, name=ADMIN_NAME)
        print("Brasaland — Auth seeder")
        print(f"  Created admin id={user.id}")
        print(f"  Email ........... {ADMIN_EMAIL}")
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
