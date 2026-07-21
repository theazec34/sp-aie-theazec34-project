"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
