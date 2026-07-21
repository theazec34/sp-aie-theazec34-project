"""Profile models — one-to-one with User (name/contact live here)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    name: str = Field(default="", max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)


class ProfileUpdate(ProfileBase):
    """Owner updates their own profile via PUT /profiles/me."""


class Profile(ProfileBase):
    id: int
    user_id: int
