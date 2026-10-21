#!/bin/sh
# Seeds (API only) then uvicorn — or exec Compose command (worker/flower).
set -e

cd /app/api
# Must include /app so `import data.pipelines.*` resolves (COPY data → /app/data).
# Do NOT set PYTHONPATH=. alone — that hides the monorepo data package.
export PYTHONPATH="/app/api:/app"

# Worker / Flower pass a command via Compose → skip API seed + uvicorn.
if [ "$#" -gt 0 ]; then
  echo "[entrypoint] exec: $*"
  exec "$@"
fi

echo "[backend] Seeding auth / suppliers / inventory (idempotent)…"
export SEED_ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@brasaland.com}"
export SEED_ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-ChangeMeLocalOnly12!}"
export SEED_ADMIN_NAME="${SEED_ADMIN_NAME:-Admin Brasaland}"
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
