"""Reusable FastAPI dependencies for JWT auth."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_access_token
from app.users.models import UserInDB
from app.users.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (ValueError, TypeError):
        raise credentials_exception from None

    repo = UserRepository()
    try:
        user = repo.get(user_id)
    finally:
        repo.close()

    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_admin(user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Acciones irreversibles (BRIEFING §5): solo rol admin."""
    from app.users.models import UserRole

    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol admin y confirmación humana explícita.",
        )
    return user
