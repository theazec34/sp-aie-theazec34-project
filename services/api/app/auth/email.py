"""Transactional email via Resend (with console fallback for local demos)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from tinydb import Query, TinyDB

from app.auth.config import get_settings
from app.users.repository import DEFAULT_DB_PATH

logger = logging.getLogger("brasaland.email")

RESEND_API_URL = "https://api.resend.com/emails"
RATE_LIMIT_PER_HOUR = 5


class ResetEmailRateLimiter:
    """Simple per-email hourly rate limit stored in TinyDB (bonus)."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("password_reset_rate_limits")

    def close(self) -> None:
        self._db.close()

    def allow(self, email: str) -> bool:
        email_key = email.lower().strip()
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=1)
        RateQ = Query()
        rows = self._table.search(RateQ.email == email_key)
        recent = []
        for row in rows:
            raw = row.get("requested_at")
            if not isinstance(raw, str):
                continue
            ts = datetime.fromisoformat(raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= window_start:
                recent.append(row)
        if len(recent) >= RATE_LIMIT_PER_HOUR:
            return False
        self._table.insert(
            {
                "email": email_key,
                "requested_at": now.isoformat(),
            }
        )
        return True


def build_reset_link(token: str) -> str:
    settings = get_settings()
    base = str(settings["FRONTEND_URL"]).rstrip("/")
    return f"{base}/reset-password?token={token}"


def _html_template(reset_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0fdfa;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#134e4a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#ffffff;border-radius:16px;padding:28px 24px;border:1px solid #99f6e4;">
        <tr><td>
          <p style="margin:0 0 8px;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:#0f766e;font-weight:700;">Brasaland OPS</p>
          <h1 style="margin:0 0 12px;font-size:22px;line-height:1.3;color:#134e4a;">Restablece tu contraseña</h1>
          <p style="margin:0 0 20px;font-size:15px;line-height:1.5;color:#115e59;">
            Has solicitado restablecer tu contraseña. El enlace caduca en poco tiempo y solo se puede usar una vez.
          </p>
          <p style="margin:0 0 24px;">
            <a href="{reset_link}" style="display:inline-block;background:#0f766e;color:#ecfeff;text-decoration:none;padding:12px 18px;border-radius:10px;font-weight:700;">
              Elegir nueva contraseña
            </a>
          </p>
          <p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:#5eead4;">
            Si el botón no funciona, copia y pega este enlace en el navegador:
          </p>
          <p style="margin:0;font-size:12px;word-break:break-all;color:#0f766e;">{reset_link}</p>
          <p style="margin:20px 0 0;font-size:12px;color:#64748b;">
            Si no pediste este cambio, puedes ignorar este correo.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _text_body(reset_link: str) -> str:
    return (
        "Brasaland OPS — Restablece tu contraseña\n\n"
        "Has solicitado restablecer tu contraseña. "
        "El enlace caduca pronto y solo se puede usar una vez.\n\n"
        f"{reset_link}\n\n"
        "Si no pediste este cambio, ignora este correo.\n"
    )


def send_password_reset_email(*, to_email: str, reset_link: str) -> dict[str, Any]:
    """Send via Resend when RESEND_API_KEY is set; otherwise log the link."""
    settings = get_settings()
    api_key = str(settings.get("RESEND_API_KEY") or "").strip()
    from_email = str(settings.get("RESEND_FROM_EMAIL") or "Brasaland OPS <onboarding@resend.dev>")
    subject = "Restablece tu contraseña — Brasaland OPS"
    html = _html_template(reset_link)
    text = _text_body(reset_link)

    if not api_key:
        logger.warning(
            "RESEND_API_KEY no configurada; enlace en consola → %s | %s",
            to_email,
            reset_link,
        )
        print(f"[brasaland-email] Reset link for {to_email}: {reset_link}", flush=True)
        return {"provider": "console", "to": to_email}

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
        if response.status_code >= 400:
            logger.error("Resend error %s: %s", response.status_code, response.text)
            # Still log link so demos are not blocked by email provider issues
            print(f"[brasaland-email] Resend failed; link for {to_email}: {reset_link}", flush=True)
            return {"provider": "resend", "ok": False, "status": response.status_code}
        data = response.json()
        logger.info("Resend accepted email id=%s to=%s", data.get("id"), to_email)
        return {"provider": "resend", "ok": True, "id": data.get("id")}
    except httpx.HTTPError as exc:
        logger.exception("Resend request failed: %s", exc)
        print(f"[brasaland-email] Resend failed; link for {to_email}: {reset_link}", flush=True)
        return {"provider": "resend", "ok": False, "error": str(exc)}
