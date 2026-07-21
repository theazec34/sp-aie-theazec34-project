"""Profile routes under /profiles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_user
from app.profiles.models import Profile, ProfileUpdate
from app.profiles.repository import ProfileRepository
from app.users.models import UserInDB

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=Profile)
def get_my_profile(current: UserInDB = Depends(get_current_user)) -> Profile:
    profiles = ProfileRepository()
    try:
        profile = profiles.get_by_user_id(current.id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        return profile
    finally:
        profiles.close()


@router.put("/me", response_model=Profile)
def update_my_profile(
    payload: ProfileUpdate,
    current: UserInDB = Depends(get_current_user),
) -> Profile:
    profiles = ProfileRepository()
    try:
        profile = profiles.update_for_user(current.id, payload)
        if profile is None:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        return profile
    finally:
        profiles.close()
