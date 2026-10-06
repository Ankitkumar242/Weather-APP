"""Main FastAPI application entry point."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
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
    # Content Security Policy allowing local assets, service worker, and OpenStreetMap tiles
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "worker-src 'self'; "
        "manifest-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response


# Locked CORS configuration (strict origin whitelist, never '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Healthcheck endpoint (used by Docker & hosting providers)
@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Production healthcheck probe."""
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "app": settings.app_name,
        "version": "0.1.0",
    }


# Root-scope PWA Service Worker & Manifest endpoints
@app.get("/sw.js")
async def serve_service_worker() -> FileResponse:
    """Serve service worker with root scope and bypass-cache headers."""
    return FileResponse(
        "app/static/sw.js",
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@app.get("/manifest.webmanifest")
async def serve_manifest() -> FileResponse:
    """Serve PWA manifest with correct MIME type."""
    return FileResponse(
        "app/static/manifest.webmanifest",
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/offline.html", response_class=HTMLResponse)
async def serve_offline_fallback() -> FileResponse:
    """Serve PWA offline fallback shell."""
    return FileResponse("app/static/offline.html", media_type="text/html")


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
@app.get("/download", response_class=FileResponse)
@app.get("/apk", response_class=FileResponse)
async def download_apk() -> Response:
    """Directly download the native Android APK."""
    apk_path = "app/static/SkyPulse.apk"
    if os.path.exists(apk_path):
        return FileResponse(
            apk_path,
            filename="SkyPulse.apk",
            media_type="application/vnd.android.package-archive",
        )
    return Response(content="APK not found", status_code=404)


@app.get("/get", response_class=HTMLResponse)
async def serve_download_page() -> str:
    """Serve a dedicated direct APK download landing page."""
    return """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Download SkyPulse Android App</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
    .card { background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 32px 24px; max-width: 400px; width: 100%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
    h1 { margin: 0 0 8px; font-size: 26px; }
    p { color: #94a3b8; font-size: 15px; margin: 0 0 24px; }
    .btn { display: block; background: #2563eb; color: #fff; text-decoration: none; padding: 16px 20px; border-radius: 12px; font-weight: 600; font-size: 18px; box-shadow: 0 10px 20px rgba(37,99,235,0.3); transition: transform 0.2s; }
    .btn:active { transform: scale(0.98); }
    .steps { text-align: left; background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; margin-top: 24px; font-size: 14px; line-height: 1.6; color: #cbd5e1; }
    .steps ol { margin: 8px 0 0; padding-left: 20px; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 48px; margin-bottom: 12px;">⚡</div>
    <h1>SkyPulse App</h1>
    <p>Official Android Native APK (4.2 MB)</p>
    <a href="/download" class="btn">⬇️ Download APK Now</a>
    <div class="steps">
      <b>इंस्टॉल करने के निर्देश:</b>
      <ol>
        <li>ऊपर दिए गए बटन पर टैप करें।</li>
        <li>डाउनलोड होने के बाद फ़ाइल पर क्लिक करें।</li>
        <li>"Settings" में जाकर "Allow from this source" चालू करें।</li>
        <li>"Install" दबाएं और ऐप खोलें!</li>
      </ol>
    </div>
  </div>
</body>
</html>"""
