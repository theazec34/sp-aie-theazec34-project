"""User credential CRUD under /users."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.auth.security import hash_password
from app.profiles.repository import ProfileRepository
from app.users.models import UserCreate, UserInDB, UserPublic, UserRole, UserUpdate
from app.users.repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def _require_self_or_admin(current: UserInDB, user_id: int) -> None:
    if current.role != UserRole.ADMIN and current.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este recurso",
        )


@router.post("", response_model=UserPublic, status_code=201)
def register_user(payload: UserCreate) -> UserPublic:
    users = UserRepository()
    profiles = ProfileRepository()
    try:
        if users.email_exists(str(payload.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese email",
            )
        user = users.create(
            email=str(payload.email),
            hashed_password=hash_password(payload.password),
            role=UserRole.USER,
        )
        profiles.create(
            user_id=user.id,
            name=payload.name or "",
            phone=payload.phone,
            address=payload.address,
        )
        return UserPublic.model_validate(user.model_dump(exclude={"hashed_password"}))
    finally:
        users.close()
        profiles.close()


@router.get("", response_model=list[UserPublic])
def list_users(_current: UserInDB = Depends(get_current_user)) -> list[UserPublic]:
    users = UserRepository()
    try:
        return users.list()
    finally:
        users.close()


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int, _current: UserInDB = Depends(get_current_user)
) -> UserPublic:
    users = UserRepository()
    try:
        user = users.get(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UserPublic.model_validate(user.model_dump(exclude={"hashed_password"}))
    finally:
        users.close()


@router.put("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current: UserInDB = Depends(get_current_user),
) -> UserPublic:
    _require_self_or_admin(current, user_id)
    if payload.role is not None and current.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un admin puede cambiar el rol",
        )

    users = UserRepository()
    try:
        if users.get(user_id) is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if payload.email and users.email_exists(str(payload.email), exclude_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese email",
            )
        updated = users.update(user_id, payload)
        assert updated is not None
        return UserPublic.model_validate(updated.model_dump(exclude={"hashed_password"}))
    finally:
        users.close()


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int, current: UserInDB = Depends(get_current_user)
) -> None:
    _require_self_or_admin(current, user_id)
    users = UserRepository()
    profiles = ProfileRepository()
    try:
        if users.get(user_id) is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        profiles.delete_by_user_id(user_id)
        users.delete(user_id)
    finally:
        users.close()
        profiles.close()
