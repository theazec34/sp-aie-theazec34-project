#!/bin/sh
# Idempotent seeds then uvicorn with hot reload.
# Optimal for local/demo: one `docker compose up` leaves the API ready to use.
set -e

cd /app/api
export PYTHONPATH=.

echo "[backend] Seeding auth / suppliers / inventory (idempotent)…"
python seed_auth.py
python seed.py
python seed_inventory.py

echo "[backend] Starting uvicorn on 0.0.0.0:8000 (--reload)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
