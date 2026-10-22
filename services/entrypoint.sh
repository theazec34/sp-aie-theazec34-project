#!/bin/sh
# Seeds rápidos → uvicorn → seeds lentos en background.
# Así /health y el login no esperan a seed_inventory.
set -e

cd /app/api
export PYTHONPATH="/app/api:/app"

# Worker / Flower pass a command via Compose → skip API seed + uvicorn.
if [ "$#" -gt 0 ]; then
  echo "[entrypoint] exec: $*"
  exec "$@"
fi

if [ -z "${SECRET_KEY:-}" ]; then
  echo "[backend] ERROR — SECRET_KEY vacía. Copia .env.example → .env (raíz) y reinicia." >&2
  exit 1
fi

echo "[backend] Seeding auth / suppliers / intake (rápido)…"
export SEED_ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-admin@brasaland.com}"
export SEED_ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-ChangeMeLocalOnly12!}"
export SEED_ADMIN_NAME="${SEED_ADMIN_NAME:-Admin Brasaland}"
python seed_auth.py
# --force: unifica tarifas a EUR (€) aunque ya hubiera seed COP/USD
SEED_SUPPLIERS_FORCE="${SEED_SUPPLIERS_FORCE:-1}" python seed.py --force
python seed_public_intake.py || echo "[backend] WARN — seed_public_intake failed." >&2

echo "[backend] Starting uvicorn on 0.0.0.0:8000 (--reload)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
UVICORN_PID=$!

# Wait until /health answers so Compose healthcheck / login can proceed.
i=0
until curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "[backend] ERROR — uvicorn no respondió /health a tiempo." >&2
    kill "$UVICORN_PID" 2>/dev/null || true
    exit 1
  fi
  sleep 1
done
echo "[backend] /health OK"

# Inventory / telemetry seeds — never block login.
(
  if command -v timeout >/dev/null 2>&1; then
    timeout 45 python seed_inventory.py || echo "[backend] WARN — seed_inventory timed out/failed." >&2
    timeout 30 python seed_telemetry.py || echo "[backend] WARN — seed_telemetry failed." >&2
  else
    python seed_inventory.py || echo "[backend] WARN — seed_inventory failed." >&2
    python seed_telemetry.py || echo "[backend] WARN — seed_telemetry failed." >&2
  fi
) &

wait "$UVICORN_PID"
