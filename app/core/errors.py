"""RFC 7807 Problem Details error handling."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application exception."""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        error_type: str = "internal-error",
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.title = title
        self.error_type = error_type
        self.extra = extra or {}


class NotFoundError(AppError):
    def __init__(
        self, detail: str = "Resource not found", extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            error_type="not-found",
            extra=extra,
        )


class UpstreamServiceError(AppError):
    def __init__(
        self, detail: str = "Upstream weather provider failed", extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_502_BAD_GATEWAY,
            title="Bad Gateway",
            error_type="upstream-error",
            extra=extra,
        )


class ValidationProblemError(AppError):
    def __init__(
        self, detail: str = "Invalid request parameters", extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Validation Error",
            error_type="validation-error",
            extra=extra,
        )


def make_problem_response(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    error_type: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Construct RFC 7807 Problem Details JSON response."""
    payload: dict[str, Any] = {
        "type": f"https://skypulse.local/errors/{error_type}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
    }
    if extra:
        payload["errors"] = extra
    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register RFC 7807 problem handlers onto the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return make_problem_response(
            request=request,
            status_code=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            error_type=exc.error_type,
            extra=exc.extra,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        error_details = [
            {"loc": list(err.get("loc", [])), "msg": str(err.get("msg"))} for err in errors
        ]
        return make_problem_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Request Validation Failed",
            detail="The parameters in the request failed validation checks.",
            error_type="validation-error",
            extra={"validation_errors": error_details},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return make_problem_response(
            request=request,
            status_code=exc.status_code,
            title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            detail=str(exc.detail),
            error_type="http-error",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return make_problem_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred while processing the request.",
            error_type="internal-server-error",
        )
