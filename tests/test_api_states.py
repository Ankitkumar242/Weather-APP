"""Integration tests for /api/v1/states and overview endpoints."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_list_states(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/states")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 36
    assert any(s["slug"] == "maharashtra" for s in data)


@pytest.mark.asyncio
async def test_list_state_cities(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/states/karnataka/cities")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["is_capital"] is True
    assert data[0]["name"] == "Bengaluru"


@pytest.mark.asyncio
@respx.mock
async def test_state_overview_endpoint(async_client: AsyncClient) -> None:
    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(
            200,
            json=[
                {
                    "latitude": 19.076,
                    "current": {"time": "2026-10-06T12:00", "temperature_2m": 31.0, "weather_code": 1},
                    "daily": {
                        "time": ["2026-10-06"],
                        "temperature_2m_max": [33.0],
                        "temperature_2m_min": [24.0],
                        "precipitation_sum": [0.0],
                    },
                }
            ]
            * 5,
        )
    )

    resp = await async_client.get("/api/v1/states/maharashtra/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["slug"] == "maharashtra"
    assert len(data["cities_weather"]) > 0
    assert len(data["trend"]) > 0


@pytest.mark.asyncio
async def test_state_not_found(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/states/non-existent-state/cities")
    assert resp.status_code == 404
    problem = resp.json()
    assert problem["type"] == "https://skypulse.local/errors/not-found"
