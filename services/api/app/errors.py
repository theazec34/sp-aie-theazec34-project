"""HTTP exception handlers for clear 400/500 responses (no stack traces)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for item in exc.errors():
            loc = [str(part) for part in item.get("loc", ()) if part != "body"]
            field = loc[-1] if loc else "body"
            msg = item.get("msg", "Valor inválido")
            # Spanish-friendly messages for common cases
            if "String should have at least 1 character" in msg or "at least 1" in msg:
                msg = "Este campo es obligatorio"
            elif "Input should be a valid" in msg or "Input should be" in msg:
                msg = f"Valor no permitido ({msg})"
            errors.append({"field": field, "message": msg})
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
        _request: Request, _exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor. Inténtalo de nuevo más tarde."
            },
        )
