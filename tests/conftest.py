"""Test configuration and shared fixtures using respx."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.cache import cache_manager
from app.main import app

MOCK_FORECAST_DATA: dict[str, Any] = {
    "latitude": 28.61,
    "longitude": 77.21,
    "timezone": "Asia/Kolkata",
    "current": {
        "time": "2026-10-06T12:00",
        "interval": 900,
        "temperature_2m": 32.5,
        "relative_humidity_2m": 55.0,
        "apparent_temperature": 35.0,
        "is_day": 1,
        "precipitation": 0.0,
        "weather_code": 1,
        "cloud_cover": 20.0,
        "pressure_msl": 1012.0,
        "wind_speed_10m": 12.0,
        "wind_direction_10m": 180.0,
        "wind_gusts_10m": 18.0,
        "dew_point_2m": 20.0,
        "visibility": 8000.0,
        "uv_index": 6.5,
    },
    "hourly": {
        "time": [f"2026-10-06T{h:02d}:00" for h in range(12, 24)]
        + [f"2026-10-07T{h:02d}:00" for h in range(24)]
        + [f"2026-10-08T{h:02d}:00" for h in range(24)],
        "temperature_2m": [32.0 + (i % 5) for i in range(60)],
        "apparent_temperature": [34.0 + (i % 5) for i in range(60)],
        "precipitation_probability": [10 + (i % 20) for i in range(60)],
        "precipitation": [0.0] * 60,
        "weather_code": [1] * 60,
        "wind_speed_10m": [12.0] * 60,
        "uv_index": [5.0] * 60,
    },
    "daily": {
        "time": [
            "2026-09-29",
            "2026-09-30",
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04",
            "2026-10-05",
            "2026-10-06",
            "2026-10-07",
            "2026-10-08",
            "2026-10-09",
            "2026-10-10",
            "2026-10-11",
            "2026-10-12",
            "2026-10-13",
        ],
        "weather_code": [0, 1, 2, 3, 1, 0, 1, 1, 2, 61, 80, 0, 1, 2, 0],
        "temperature_2m_max": [
            33.0,
            34.0,
            35.0,
            33.0,
            32.0,
            34.0,
            35.0,
            36.0,
            34.0,
            31.0,
            30.0,
            33.0,
            34.0,
            35.0,
            34.0,
        ],
        "temperature_2m_min": [
            22.0,
            23.0,
            24.0,
            23.0,
            22.0,
            23.0,
            24.0,
            25.0,
            24.0,
            21.0,
            20.0,
            22.0,
            23.0,
            24.0,
            23.0,
        ],
        "apparent_temperature_max": [35.0] * 15,
        "apparent_temperature_min": [23.0] * 15,
        "sunrise": ["2026-10-06T06:15"] * 15,
        "sunset": ["2026-10-06T18:05"] * 15,
        "daylight_duration": [42600.0] * 15,
        "uv_index_max": [7.0] * 15,
        "precipitation_sum": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.2,
            12.5,
            5.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "precipitation_probability_max": [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            10,
            40,
            85,
            60,
            10,
            5,
            5,
            0,
        ],
        "wind_speed_10m_max": [15.0] * 15,
        "wind_gusts_10m_max": [25.0] * 15,
        "wind_direction_10m_dominant": [180.0] * 15,
    },
}

MOCK_AIR_QUALITY_DATA: dict[str, Any] = {
    "latitude": 28.61,
    "longitude": 77.21,
    "current": {
        "time": "2026-10-06T12:00",
        "interval": 3600,
        "us_aqi": 125,
        "pm2_5": 45.2,
        "pm10": 110.0,
        "ozone": 85.0,
    },
    "hourly": {
        "time": ["2026-10-06T12:00", "2026-10-06T13:00", "2026-10-06T14:00"],
        "us_aqi": [125, 130, 128],
    },
}


@pytest.fixture(autouse=True)
def clear_cache() -> Generator[None, None, None]:
    """Clear in-memory cache before every test."""
    cache_manager.forecast_cache.clear()
    cache_manager.air_quality_cache.clear()
    cache_manager.state_overview_cache.clear()
    cache_manager.search_cache.clear()
    cache_manager.reverse_geo_cache.clear()
    cache_manager.ip_locate_cache.clear()
    cache_manager._stale_store.clear()
    cache_manager.total_cache_hits = 0
    cache_manager.total_upstream_calls = 0
    yield


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
