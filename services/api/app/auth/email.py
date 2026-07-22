"""Transactional email helpers for password recovery.

Commit 1 ships a safe console fallback so the API flow works without keys.
Resend (real delivery) is wired in the following commit.
"""

from __future__ import annotations

import logging

from app.auth.config import get_settings

logger = logging.getLogger("brasaland.email")


def build_reset_link(token: str) -> str:
    settings = get_settings()
    base = str(settings["FRONTEND_URL"]).rstrip("/")
    return f"{base}/reset-password?token={token}"


def send_password_reset_email(*, to_email: str, reset_link: str) -> None:
    """Deliver (or log) the password-reset link."""
    # Real Resend delivery is added in the email-integration commit.
    logger.warning(
        "Password reset email (console fallback) → %s | link=%s",
        to_email,
        reset_link,
    )
    print(f"[brasaland-email] Reset link for {to_email}: {reset_link}", flush=True)
