"""Main FastAPI application entry point."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import api_v1_router
from app.config import get_settings
from app.core.cache import cache_manager
from app.core.errors import register_error_handlers
from app.core.http import close_http_client
from app.core.ratelimit import register_rate_limit_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    yield
    # Clean up HTTP client
    await close_http_client()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register rate limiter and RFC 7807 error handlers
register_rate_limit_handler(app)
register_error_handlers(app)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable[[Request], Any]) -> Response:
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Content Security Policy allowing local assets and OpenStreetMap tiles/attributions
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response


# Same-origin CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Same-origin enforced via headers in production
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# API v1 routes
app.include_router(api_v1_router)

# Mount static and templates
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/api/v1/debug")
async def get_debug_info() -> dict[str, Any]:
    """Return upstream call statistics and cache hit ratio for ?debug=1."""
    return cache_manager.get_debug_stats()


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request) -> Response:
    """Render the single-page application shell."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "default_lat": settings.default_latitude,
            "default_lon": settings.default_longitude,
            "default_city": settings.default_city_name,
        },
    )
