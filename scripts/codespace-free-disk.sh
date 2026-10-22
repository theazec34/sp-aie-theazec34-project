#!/usr/bin/env bash
# Libera disco en Codespaces / Docker sin tocar el código ni los .md
# Uso: bash scripts/codespace-free-disk.sh
#      bash scripts/codespace-free-disk.sh --volumes   # también borra volúmenes Compose
set -euo pipefail
cd "$(dirname "$0")/.."

WITH_VOLUMES=0
for arg in "$@"; do
  case "$arg" in
    --volumes) WITH_VOLUMES=1 ;;
    -h|--help)
      echo "Uso: $0 [--volumes]"
      echo "  Sin flags: para Compose, purga builder + imágenes/contendedores huérfanos,"
      echo "  borra .next y cachés npm. NO borra .md ni el código."
      echo "  --volumes: además docker system prune --volumes (pierdes datos Redis/TinyDB del stack)."
      exit 0
      ;;
  esac
done

echo "== Antes =="
df -h / | awk 'NR==1 || /\/$/'

echo
echo "[1/5] Parando Compose…"
docker compose down --remove-orphans 2>/dev/null || true

echo "[2/5] Purgando BuildKit / buildx…"
docker builder prune -af 2>/dev/null || true
docker buildx prune -af 2>/dev/null || true

echo "[3/5] docker system prune…"
if [[ "$WITH_VOLUMES" -eq 1 ]]; then
  docker system prune -af --volumes
else
  docker system prune -af
fi

echo "[4/5] Cachés Next / npm (bind mounts)…"
rm -rf uis/website/.next uis/backoffice/.next 2>/dev/null || true
rm -rf uis/website/node_modules/.cache uis/backoffice/node_modules/.cache 2>/dev/null || true
npm cache clean --force 2>/dev/null || true
rm -rf "${HOME}/.npm/_cacache" 2>/dev/null || true

echo "[5/5] git gc…"
git gc --prune=now 2>/dev/null || true

echo
echo "== Después =="
df -h / | awk 'NR==1 || /\/$/'
echo
echo "Siguiente:"
echo "  git pull"
echo "  docker compose up --build -d"
echo
echo "Si df sigue <2G libres → GitHub Codespaces → ⋯ → Rebuild container"
echo "(NO borres los .md: ~5MB; el hueco es Docker.)"
