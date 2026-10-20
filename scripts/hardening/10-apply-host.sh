#!/usr/bin/env bash
# Endurecimiento del host de despliegue Brasaland (Ubuntu/Debian).
# Ejecutar como root en el servidor de ops — NO en el laptop de desarrollo.
#
# Controles:
#  - Usuario no-root `brasaland` para operación diaria
#  - SSH: PermitRootLogin no
#  - Permisos: código / logs / secretos separados
#  - UFW: solo 22, 80, 443 (+ 8000 solo si no hay reverse proxy)
#
# Uso: sudo bash scripts/hardening/10-apply-host.sh
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ejecuta como root (sudo)." >&2
  exit 1
fi

BRASA_USER="${BRASA_USER:-brasaland}"
APP_ROOT="${APP_ROOT:-/opt/brasaland}"
LOG_ROOT="${LOG_ROOT:-/var/log/brasaland}"
SECRET_ROOT="${SECRET_ROOT:-/etc/brasaland}"

echo "[1/5] Usuario operativo no-root: ${BRASA_USER}"
if ! id "${BRASA_USER}" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "${BRASA_USER}"
  usermod -aG docker "${BRASA_USER}" 2>/dev/null || true
fi

echo "[2/5] Estructura de carpetas y permisos"
mkdir -p "${APP_ROOT}" "${LOG_ROOT}" "${SECRET_ROOT}"
chown -R "${BRASA_USER}:${BRASA_USER}" "${APP_ROOT}" "${LOG_ROOT}"
chown root:"${BRASA_USER}" "${SECRET_ROOT}"
chmod 750 "${SECRET_ROOT}"
chmod 640 "${SECRET_ROOT}"/* 2>/dev/null || true
# .env nunca world-readable
if [[ -f "${SECRET_ROOT}/.env" ]]; then
  chmod 640 "${SECRET_ROOT}/.env"
  chown root:"${BRASA_USER}" "${SECRET_ROOT}/.env"
fi

echo "[3/5] SSH — deshabilitar login root directo"
SSHD="/etc/ssh/sshd_config"
if [[ -f "${SSHD}" ]]; then
  if grep -qE '^\s*PermitRootLogin' "${SSHD}"; then
    sed -i 's/^\s*PermitRootLogin.*/PermitRootLogin no/' "${SSHD}"
  else
    echo "PermitRootLogin no" >> "${SSHD}"
  fi
  if grep -qE '^\s*PasswordAuthentication' "${SSHD}"; then
    sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication no/' "${SSHD}"
  else
    echo "PasswordAuthentication no" >> "${SSHD}"
  fi
  systemctl reload sshd 2>/dev/null || systemctl reload ssh 2>/dev/null || true
  grep -E '^\s*PermitRootLogin' "${SSHD}" || true
else
  echo "AVISO: no hay sshd_config (entorno contenedorizado / Codespaces)."
fi

echo "[4/5] Firewall UFW — deny by default"
if command -v ufw >/dev/null 2>&1; then
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow OpenSSH
  ufw allow 80/tcp
  ufw allow 443/tcp
  # API directa solo si no hay nginx/caddy delante
  if [[ "${EXPOSE_API_PORT:-0}" == "1" ]]; then
    ufw allow 8000/tcp
  fi
  # Redis / Qdrant / Flower / MCP / Postgres NUNCA desde internet
  ufw --force enable
  ufw status verbose
else
  echo "AVISO: ufw no instalado — documentar iptables/cloud SG equivalentes."
fi

echo "[5/5] Verificación"
id "${BRASA_USER}"
ls -ld "${APP_ROOT}" "${LOG_ROOT}" "${SECRET_ROOT}"
echo "OK — hardening host aplicado. Opera como ${BRASA_USER}, no como root."
