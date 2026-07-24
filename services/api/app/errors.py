"""HTTP exception handlers for clear 400/500 responses (no stack traces)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("brasaland.api")


def _friendly_validation_message(raw: str) -> str:
    msg = raw or "Valor inválido"
    if "String should have at least 1 character" in msg or "at least 1" in msg:
        return "Este campo es obligatorio"
    if "Input should be a valid" in msg or "Input should be" in msg:
        return "Valor no permitido para este campo"
    if "value is not a valid email" in msg.lower():
        return "Email no válido"
    if "Field required" in msg or "missing" in msg.lower():
        return "Este campo es obligatorio"
    return "Valor inválido"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for item in exc.errors():
            loc = [str(part) for part in item.get("loc", ()) if part != "body"]
            field = loc[-1] if loc else "body"
            errors.append(
                {
                    "field": field,
                    "message": _friendly_validation_message(str(item.get("msg", ""))),
                }
            )
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Revisa los campos marcados",
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Log completo solo en servidor; el cliente recibe mensaje genérico.
        logger.exception(
            "Unhandled error on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor. Inténtalo de nuevo más tarde."
            },
        )
