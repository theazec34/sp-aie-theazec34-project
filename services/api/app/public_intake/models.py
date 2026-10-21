"""Public website intake — reservations & career applications."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class ReservationStatus(str, Enum):
    RECEIVED = "received"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class ReservationCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=9, max_length=32)
    email: EmailStr
    date: date
    time: time
    guests: int = Field(ge=1, le=20)
    notes: str = Field(default="", max_length=500)

    @field_validator("full_name", "phone", "notes")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ReservationPublic(BaseModel):
    id: int
    full_name: str
    phone: str
    email: EmailStr
    date: date
    time: time
    guests: int
    notes: str
    status: ReservationStatus
    created_at: datetime
    message: str = (
        "Solicitud registrada. La mesa no está confirmada hasta que el "
        "restaurante la revise."
    )


class CareerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=9, max_length=32)
    department: str = Field(min_length=2, max_length=80)
    experience_years: int = Field(ge=0, le=50)
    message: str = Field(min_length=10, max_length=500)
    cv_filename: str = Field(default="", max_length=255)
    privacy_accepted: bool

    @field_validator("privacy_accepted")
    @classmethod
    def must_accept_privacy(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar la política de privacidad.")
        return value


class CareerPublic(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    department: str
    experience_years: int
    message: str
    cv_filename: str
    created_at: datetime
    status_message: str = (
        "Candidatura registrada. El equipo de RR. HH. la revisará; "
        "no implica contratación."
    )
