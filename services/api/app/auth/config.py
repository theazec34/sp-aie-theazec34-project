"""Auth configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load services/api/.env when running from that directory or monorepo root
_API_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_API_DIR / ".env")
load_dotenv()


@lru_cache
def get_settings() -> dict[str, str | int]:
    secret = os.getenv("SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError(
            "SECRET_KEY no está definida. Copia services/api/.env.example a .env"
        )
    return {
        "SECRET_KEY": secret,
        "ALGORITHM": os.getenv("ALGORITHM", "HS256"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
        # Password reset tokens: 15–60 min window (default 30)
        "RESET_TOKEN_EXPIRE_MINUTES": int(
            os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30")
        ),
        # Backoffice base URL used in reset email links
        "FRONTEND_URL": os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
        "RESEND_API_KEY": os.getenv("RESEND_API_KEY", "").strip(),
        "RESEND_FROM_EMAIL": os.getenv(
            "RESEND_FROM_EMAIL", "Brasaland OPS <onboarding@resend.dev>"
        ).strip(),
    }
