"""Integration tests for /api/v1/locate endpoints and /healthz."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_healthz_endpoint(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
@respx.mock
async def test_reverse_endpoint(async_client: AsyncClient) -> None:
    respx.get(settings.nominatim_reverse_url).mock(
        return_value=Response(
            200,
            json={
                "display_name": "Mumbai, Maharashtra, India",
                "name": "Mumbai",
                "address": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                },
            },
        )
    )

    resp = await async_client.get("/api/v1/reverse", params={"lat": 19.0760, "lon": 72.8777})
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Mumbai"
    assert data["state"] == "Maharashtra"


@pytest.mark.asyncio
@respx.mock
async def test_locate_ip_endpoint(async_client: AsyncClient) -> None:
    respx.get(settings.ipwhois_url).mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "city": "Shimla",
                "region": "Himachal Pradesh",
                "country": "India",
                "latitude": 31.1048,
                "longitude": 77.1734,
            },
        )
    )

    resp = await async_client.get("/api/v1/locate/ip")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Shimla"
    assert data["state"] == "Himachal Pradesh"
    assert data["is_approximate"] is True
