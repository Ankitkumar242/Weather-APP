"""Integration tests for /api/v1/weather endpoint."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from app.config import get_settings
from tests.conftest import MOCK_AIR_QUALITY_DATA, MOCK_FORECAST_DATA

settings = get_settings()


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_success(async_client: AsyncClient) -> None:
    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=MOCK_FORECAST_DATA)
    )
    respx.get(settings.open_meteo_air_quality_url).mock(
        return_value=Response(200, json=MOCK_AIR_QUALITY_DATA)
    )

    resp = await async_client.get(
        "/api/v1/weather",
        params={"lat": 28.6139, "lon": 77.2090, "name": "New Delhi", "state": "Delhi"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["location"]["name"] == "New Delhi"
    assert data["location"]["state"] == "Delhi"
    assert data["current"]["temperature"] == 32.5
    assert len(data["daily"]) == 15
    assert len(data["hourly"]) == 48
    assert data["air_quality"]["us_aqi"] == 125
    assert "alerts" in data["insights"]
    assert data["meta"]["stale"] is False


@pytest.mark.asyncio
async def test_get_weather_validation_error(async_client: AsyncClient) -> None:
    # Invalid latitude > 90
    resp = await async_client.get("/api/v1/weather", params={"lat": 105.0, "lon": 77.2090})
    assert resp.status_code == 422
    problem = resp.json()
    assert problem["type"] == "https://skypulse.local/errors/validation-error"
    assert problem["status"] == 422
    assert "validation_errors" in problem.get("errors", {})


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_stale_fallback_on_upstream_failure(async_client: AsyncClient) -> None:
    # First, populate cache with successful response
    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=MOCK_FORECAST_DATA)
    )
    respx.get(settings.open_meteo_air_quality_url).mock(
        return_value=Response(200, json=MOCK_AIR_QUALITY_DATA)
    )

    resp1 = await async_client.get("/api/v1/weather", params={"lat": 28.61, "lon": 77.21})
    assert resp1.status_code == 200

    # Clear fresh TTL cache so it has to refetch, but keep stale store intact
    from app.core.cache import cache_manager

    cache_manager.forecast_cache.clear()
    cache_manager.air_quality_cache.clear()

    # Now simulate upstream failure
    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(500, json={"error": "Open-Meteo downtime"})
    )

    resp2 = await async_client.get("/api/v1/weather", params={"lat": 28.61, "lon": 77.21})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["meta"]["stale"] is True
    assert data2["current"]["temperature"] == 32.5
