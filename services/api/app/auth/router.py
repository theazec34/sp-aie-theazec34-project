"""Authentication routes under /auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, verify_password
from app.profiles.models import Profile
from app.profiles.repository import ProfileRepository
from app.users.models import UserInDB, UserPublic, UserRole
from app.users.repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


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
