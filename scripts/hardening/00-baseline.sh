#!/usr/bin/env bash
# Baseline de endurecimiento — documenta estado ANTES de aplicar controles.
# Uso: sudo bash scripts/hardening/00-baseline.sh | tee docs/security/evidence/baseline-$(date +%Y%m%d).txt
set -euo pipefail

echo "=== Brasaland security baseline $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo
echo "## Identity"
id || true
whoami || true
echo
echo "## Root SSH PermitRootLogin (sshd_config)"
grep -E '^\s*PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo "(sshd_config no legible o ausente en este entorno)"
echo
echo "## Listening TCP ports"
(ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || true) | head -60
echo
echo "## Docker published ports (compose)"
if command -v docker >/dev/null 2>&1; then
  docker compose ps 2>/dev/null || true
  docker ps --format 'table {{.Names}}\t{{.Ports}}' 2>/dev/null || true
else
  echo "(docker no disponible)"
fi
echo
echo "## UFW / firewall"
(ufw status verbose 2>/dev/null || iptables -L -n 2>/dev/null | head -40 || echo "(sin firewall CLI)")
echo
echo "## Sensitive paths permissions"
ls -la /workspace/.env 2>/dev/null || echo "(sin .env)"
ls -la /workspace/services/api/data 2>/dev/null || true
echo
echo "=== fin baseline ==="
