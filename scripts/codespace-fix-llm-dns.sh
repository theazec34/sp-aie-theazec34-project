#!/usr/bin/env bash
# Codespaces: el contenedor backend a menudo no resuelve DNS externo
# (llm.4geeks.ai). El host sí. Este script resuelve en el host e inyecta
# /etc/hosts en backend (+ worker si está up).
set -euo pipefail

HOST="${LLM_HOST:-llm.4geeks.ai}"
IP="${LLM_4GEEKS_IP:-}"

if [[ -z "$IP" ]]; then
  IP="$(getent hosts "$HOST" | awk '{print $1; exit}')"
fi
if [[ -z "$IP" ]]; then
  IP="$(getent ahostsv4 "$HOST" | awk '{print $1; exit}')"
fi
if [[ -z "$IP" ]]; then
  echo "ERROR: no se pudo resolver $HOST en el host Codespace" >&2
  exit 1
fi

echo "Host resuelve $HOST → $IP"

for svc in backend worker; do
  if docker compose ps --status running --services 2>/dev/null | grep -qx "$svc"; then
    docker compose exec -T "$svc" sh -c \
      "grep -qE '[[:space:]]${HOST}\$' /etc/hosts 2>/dev/null && sed -i '/[[:space:]]${HOST}\$/d' /etc/hosts; \
       echo '${IP} ${HOST}' >> /etc/hosts; \
       getent hosts '${HOST}' || grep '${HOST}' /etc/hosts"
    echo "OK: /etc/hosts actualizado en $svc"
  else
    echo "skip: $svc no está running"
  fi
done

echo "Prueba: docker compose exec -T backend curl -sS -o /dev/null -w '%{http_code}\\n' https://${HOST}/v1/models"
