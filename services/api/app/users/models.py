"""User credential models (no visible name/contact — those live in Profile)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class UserCreate(BaseModel):
    """Public registration payload. Optional profile fields create a linked Profile."""

    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def role_allowed(cls, value: UserRole | None) -> UserRole | None:
        if value is None:
            return value
        if value not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.USER}:
            raise ValueError("role must be admin, manager, or user")
        return value


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: datetime


class UserInDB(UserPublic):
    hashed_password: str
