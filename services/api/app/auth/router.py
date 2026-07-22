"""Authentication routes under /auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth.deps import get_current_user
from app.auth.email import (
    ResetEmailRateLimiter,
    build_reset_link,
    send_password_reset_email,
)
from app.auth.reset_tokens import PasswordResetTokenRepository
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
)
from app.auth.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.profiles.models import Profile
from app.profiles.repository import ProfileRepository
from app.users.models import UserInDB, UserRole
from app.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

GENERIC_FORGOT_MESSAGE = (
    "Si esa dirección está en nuestro sistema, recibirás un enlace de restablecimiento."
)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    email: str
    role: UserRole
    profile: Profile | None = None


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """OAuth2 form: use `username` field for email (Swagger Authorize compatible)."""
    repo = UserRepository()
    try:
        user = repo.get_by_email(form_data.username)
        if user is None or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo",
            )
        token = create_access_token(subject=user.id)
        return TokenResponse(access_token=token)
    finally:
        repo.close()


@router.get("/me", response_model=AuthMeResponse)
def auth_me(current_user: UserInDB = Depends(get_current_user)) -> AuthMeResponse:
    profiles = ProfileRepository()
    try:
        profile = profiles.get_by_user_id(current_user.id)
        return AuthMeResponse(
            email=str(current_user.email),
            role=current_user.role,
            profile=profile,
        )
    finally:
        profiles.close()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Always 200 — never reveal whether the email is registered."""
    users = UserRepository()
    tokens = PasswordResetTokenRepository()
    limiter = ResetEmailRateLimiter()
    try:
        user = users.get_by_email(str(payload.email))
        if user is not None and user.is_active:
            # Rate-limit quietly: still return the generic 200 message.
            if limiter.allow(str(user.email)):
                reset_jwt, jti, expires_at = create_password_reset_token(user_id=user.id)
                tokens.create(jti=jti, user_id=user.id, expires_at=expires_at)
                send_password_reset_email(
                    to_email=str(user.email),
                    reset_link=build_reset_link(reset_jwt),
                )
        return ForgotPasswordResponse(message=GENERIC_FORGOT_MESSAGE)
    finally:
        users.close()
        tokens.close()
        limiter.close()


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    users = UserRepository()
    tokens = PasswordResetTokenRepository()
    try:
        try:
            claims = decode_password_reset_token(payload.token)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de restablecimiento inválido o expirado",
            ) from exc

        jti = str(claims["jti"])
        if not tokens.is_usable(jti):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de restablecimiento inválido o expirado",
            )

        user_id = int(claims["sub"])
        user = users.get(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de restablecimiento inválido o expirado",
            )

        users.update_password(user_id, hash_password(payload.new_password))
        if not tokens.mark_used(jti):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de restablecimiento inválido o expirado",
            )
        return MessageResponse(message="Contraseña actualizada. Ya puedes iniciar sesión.")
    finally:
        users.close()
        tokens.close()


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_user),
) -> MessageResponse:
    users = UserRepository()
    try:
        if not verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña actual no es correcta",
            )
        if payload.current_password == payload.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe ser distinta de la actual",
            )
        users.update_password(current_user.id, hash_password(payload.new_password))
        return MessageResponse(message="Contraseña cambiada correctamente.")
    finally:
        users.close()
