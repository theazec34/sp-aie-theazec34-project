#!/usr/bin/env bash
# Evidencia reproducible de controles críticos (post-fix).
set -euo pipefail

FAIL=0
pass() { echo "PASS — $*"; }
fail() { echo "FAIL — $*"; FAIL=1; }

echo "=== verify hardening $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# Compose: Redis/Qdrant no deben publicarse al host
if grep -n 'redis:' -A20 docker-compose.yml | grep -qE '^\s+ports:'; then
  fail "Redis publica ports: en docker-compose.yml"
else
  pass "Redis sin ports públicos en compose"
fi

if grep -A20 '^\s*qdrant:' docker-compose.yml | grep -qE '^\s+ports:'; then
  fail "Qdrant publica ports: en docker-compose.yml"
else
  pass "Qdrant sin ports públicos en compose"
fi

if grep -A30 '^\s*flower:' docker-compose.yml | grep -q '127.0.0.1:5555'; then
  pass "Flower solo en loopback 127.0.0.1:5555"
else
  fail "Flower no está acotado a loopback"
fi

# seed_auth sin password hardcodeado
if grep -E 'ADMIN_PASSWORD\s*=\s*"' services/api/seed_auth.py >/dev/null 2>&1; then
  fail "seed_auth.py aún tiene password literal"
else
  pass "seed_auth.py sin password hardcodeado"
fi

# Incidents router exige JWT
if grep -q 'dependencies=\[Depends(get_current_user)\]' services/api/app/incidents/router.py; then
  pass " /api/incidents exige JWT"
else
  fail "/api/incidents sin dependencia JWT"
fi

# Supplier irreversible confirm
if grep -q 'payload.confirm' services/api/app/suppliers/router.py; then
  pass "Cambio de estado proveedor exige confirm"
else
  fail "Proveedor status sin confirm"
fi

# Host checks (best-effort)
if [[ -f /etc/ssh/sshd_config ]]; then
  if grep -E '^\s*PermitRootLogin\s+no' /etc/ssh/sshd_config >/dev/null; then
    pass "PermitRootLogin no"
  else
    fail "PermitRootLogin no está en 'no' (aplica 10-apply-host.sh en el servidor)"
  fi
else
  echo "SKIP — sshd_config ausente (CI/Codespaces); evidencia en servidor de ops"
fi

if id brasaland >/dev/null 2>&1; then
  pass "Usuario brasaland existe"
else
  echo "SKIP — usuario brasaland no creado en este entorno (script 10-apply-host.sh)"
fi

echo
if [[ "${FAIL}" -eq 0 ]]; then
  echo "RESULT: all critical checks passed (or skipped where N/A)"
  exit 0
fi
echo "RESULT: ${FAIL} failure(s)"
exit 1
