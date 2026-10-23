#!/usr/bin/env bash
# Codespaces: el bridge Docker resuelve llm.4geeks.ai pero TCP:443 hace timeout.
# Este script:
#  1) Arranca llm-proxy (nginx en network_mode:host → puerto 18080)
#  2) Apunta GENERATION/EMBEDDING_BASE_URL a host.docker.internal:18080
#  3) Recrea backend (+ worker)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ENV_FILE="${ENV_FILE:-.env}"
PROXY_URL="${LLM_PROXY_BASE_URL:-http://host.docker.internal:18080/v1}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: no existe $ENV_FILE" >&2
  exit 1
fi

upsert_env() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$val" >>"$ENV_FILE"
  fi
}

echo "→ .env: BASE_URL → $PROXY_URL"
upsert_env GENERATION_BASE_URL "$PROXY_URL"
upsert_env EMBEDDING_BASE_URL "$PROXY_URL"

echo "→ docker compose up llm-proxy backend worker"
docker compose up -d llm-proxy
docker compose up -d --force-recreate backend worker

echo "→ prueba host proxy"
curl -sS -o /dev/null -w "host→proxy %{http_code}\n" --max-time 20 \
  -H "Authorization: Bearer $(grep -E '^GENERATION_API_KEY=' "$ENV_FILE" | cut -d= -f2-)" \
  "http://127.0.0.1:18080/v1/models" || true

echo "→ prueba backend→proxy"
docker compose exec -T backend curl -sS -o /dev/null -w "backend→proxy %{http_code}\n" --max-time 30 \
  -H "Authorization: Bearer $(docker compose exec -T backend printenv GENERATION_API_KEY)" \
  "${PROXY_URL%/v1}/v1/models" || true

echo "Listo. Reindex: docker compose exec -T backend python -c \"from data.process.rag import setup; print(setup(recreate=True))\""
