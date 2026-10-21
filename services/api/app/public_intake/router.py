"""Public intake routes (website) + admin list (JWT)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.auth.deps import get_current_user
from app.public_intake.models import (
    CareerCreate,
    CareerPublic,
    ReservationCreate,
    ReservationPublic,
)
from app.public_intake.repository import PublicIntakeRepository
from app.rate_limit import SlidingWindowRateLimiter, enforce_rate_limit
from app.users.models import UserInDB

api_router = APIRouter(tags=["public-intake"])

_repo = PublicIntakeRepository()
_public_limiter = SlidingWindowRateLimiter(max_calls=20, window_seconds=60)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@api_router.post(
    "/reservations",
    response_model=ReservationPublic,
    status_code=201,
    summary="Registrar solicitud de reserva (pública)",
)
def create_reservation(
    payload: ReservationCreate,
    request: Request,
) -> ReservationPublic:
    enforce_rate_limit(
        _public_limiter,
        f"reservations:{_client_key(request)}",
        detail="Demasiadas solicitudes de reserva. Espera un minuto.",
    )
    return _repo.create_reservation(payload)


@api_router.get(
    "/reservations",
    response_model=list[ReservationPublic],
    summary="Listar reservas (JWT)",
)
def list_reservations(_user: UserInDB = Depends(get_current_user)) -> list[ReservationPublic]:
    return _repo.list_reservations()


@api_router.post(
    "/careers",
    response_model=CareerPublic,
    status_code=201,
    summary="Registrar candidatura (pública)",
)
def create_career(payload: CareerCreate, request: Request) -> CareerPublic:
    enforce_rate_limit(
        _public_limiter,
        f"careers:{_client_key(request)}",
        detail="Demasiadas candidaturas. Espera un minuto.",
    )
    return _repo.create_career(payload)


@api_router.get(
    "/careers",
    response_model=list[CareerPublic],
    summary="Listar candidaturas (JWT)",
)
def list_careers(_user: UserInDB = Depends(get_current_user)) -> list[CareerPublic]:
    return _repo.list_careers()
