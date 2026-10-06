"""Rate limiting configuration with slowapi."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.errors import make_problem_response

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    headers_enabled=False,
)


def register_rate_limit_handler(app: FastAPI) -> None:
    """Register RateLimitExceeded RFC 7807 problem handler."""
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return make_problem_response(
            request=request,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            title="Rate Limit Exceeded",
            detail=f"Too many requests. Limit is {exc.detail}.",
            error_type="rate-limit-exceeded",
        )
