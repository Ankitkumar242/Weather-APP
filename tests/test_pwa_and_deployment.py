"""Integration tests for PWA and Deployment endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_healthz(async_client: AsyncClient) -> None:
    resp = await async_client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["app"] == "SkyPulse"


@pytest.mark.asyncio
async def test_service_worker_endpoint(async_client: AsyncClient) -> None:
    resp = await async_client.get("/sw.js")
    assert resp.status_code == 200
    assert "application/javascript" in resp.headers["content-type"]
    assert resp.headers.get("service-worker-allowed") == "/"
    assert "no-cache" in resp.headers.get("cache-control", "")
    assert "SHELL_CACHE_NAME" in resp.text


@pytest.mark.asyncio
async def test_manifest_webmanifest_endpoint(async_client: AsyncClient) -> None:
    resp = await async_client.get("/manifest.webmanifest")
    assert resp.status_code == 200
    assert "application/manifest+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["name"] == "SkyPulse Weather"
    assert data["short_name"] == "SkyPulse"
    assert data["display"] == "standalone"
    assert len(data["icons"]) >= 2
    # Verify maskable icon is declared
    assert any(i.get("purpose") == "maskable" for i in data["icons"])


@pytest.mark.asyncio
async def test_offline_fallback_page(async_client: AsyncClient) -> None:
    resp = await async_client.get("/offline.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "offline" in resp.text.lower()


@pytest.mark.asyncio
async def test_cors_locked_configuration(async_client: AsyncClient) -> None:
    # Test preflight from allowed origin
    resp = await async_client.options(
        "/api/v1/weather?lat=28.61&lon=77.20",
        headers={
            "Origin": "https://localhost",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "https://localhost"

    # Test preflight from Capacitor origin
    resp_cap = await async_client.options(
        "/api/v1/weather?lat=28.61&lon=77.20",
        headers={
            "Origin": "capacitor://localhost",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp_cap.headers.get("access-control-allow-origin") == "capacitor://localhost"

    # Test preflight from unauthorized origin
    resp_unauth = await async_client.options(
        "/api/v1/weather?lat=28.61&lon=77.20",
        headers={
            "Origin": "https://malicious-site.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp_unauth.headers.get("access-control-allow-origin") is None

