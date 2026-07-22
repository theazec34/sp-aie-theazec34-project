"""Password hashing and JWT helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
RESET_TOKEN_TYPE = "password_reset"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str | int, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_delta = expires_minutes or int(settings["ACCESS_TOKEN_EXPIRE_MINUTES"])
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_delta)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        str(settings["SECRET_KEY"]),
        algorithm=str(settings["ALGORITHM"]),
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            str(settings["SECRET_KEY"]),
            algorithms=[str(settings["ALGORITHM"])],
        )
    except JWTError as exc:
        raise ValueError("Token inválido o expirado") from exc


def create_password_reset_token(*, user_id: int) -> tuple[str, str, datetime]:
    """Return (jwt, jti, expires_at) for a short-lived single-use reset token."""
    settings = get_settings()
    minutes = int(settings["RESET_TOKEN_EXPIRE_MINUTES"])
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "type": RESET_TOKEN_TYPE,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(
        payload,
        str(settings["SECRET_KEY"]),
        algorithm=str(settings["ALGORITHM"]),
    )
    return token, jti, expire


def decode_password_reset_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            str(settings["SECRET_KEY"]),
            algorithms=[str(settings["ALGORITHM"])],
        )
    except JWTError as exc:
        raise ValueError("Token de restablecimiento inválido o expirado") from exc
    if payload.get("type") != RESET_TOKEN_TYPE:
        raise ValueError("Token de restablecimiento inválido o expirado")
    if not payload.get("jti") or not payload.get("sub"):
        raise ValueError("Token de restablecimiento inválido o expirado")
    return payload
