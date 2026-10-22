#!/usr/bin/env sh
# Limpia caché BuildKit corrupta (error típico en Codespaces):
#   parent snapshot ... does not exist: not found
# y vuelve a construir Compose.
set -eu
cd "$(dirname "$0")/.."

echo "[docker-rebuild] Parando stack…"
docker compose down --remove-orphans 2>/dev/null || true

echo "[docker-rebuild] Purgando builder cache…"
docker builder prune -af 2>/dev/null || true
docker buildx prune -af 2>/dev/null || true

echo "[docker-rebuild] Build sin caché + up…"
docker compose build --no-cache
docker compose up
