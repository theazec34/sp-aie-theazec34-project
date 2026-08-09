#!/bin/sh
# Idempotent seeds then uvicorn with hot reload.
# Optimal for local/demo: one `docker compose up` leaves the API ready to use.
set -e

cd /app/api
export PYTHONPATH=.

echo "[backend] Seeding auth / suppliers / inventory (idempotent)…"
python seed_auth.py
python seed.py

# Inventory seed may talk to Supabase; never block API boot.
if command -v timeout >/dev/null 2>&1; then
  if ! timeout 30 python seed_inventory.py; then
    echo "[backend] WARN — seed_inventory timed out or failed; starting API anyway." >&2
  fi
else
  python seed_inventory.py || echo "[backend] WARN — seed_inventory failed; starting API anyway." >&2
fi

echo "[backend] Starting uvicorn on 0.0.0.0:8000 (--reload)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
