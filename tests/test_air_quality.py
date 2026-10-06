"""Tests for Air Quality service."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.air_quality import fetch_air_quality, get_aqi_category
from tests.conftest import MOCK_AIR_QUALITY_DATA

settings = get_settings()


def test_aqi_categories() -> None:
    assert get_aqi_category(None) is None
    assert get_aqi_category(35) == "Good"
    assert get_aqi_category(75) == "Moderate"
    assert get_aqi_category(125) == "Unhealthy for Sensitive Groups"
    assert get_aqi_category(175) == "Unhealthy"
    assert get_aqi_category(250) == "Very Unhealthy"
    assert get_aqi_category(350) == "Hazardous"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_air_quality_success() -> None:
    respx.get(settings.open_meteo_air_quality_url).mock(
        return_value=Response(200, json=MOCK_AIR_QUALITY_DATA)
    )

    aqi, is_stale = await fetch_air_quality(28.6139, 77.2090)
    assert not is_stale
    assert aqi is not None
    assert aqi.us_aqi == 125
    assert aqi.aqi_category == "Unhealthy for Sensitive Groups"
    assert aqi.pm2_5 == 45.2
    assert aqi.pm10 == 110.0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_air_quality_graceful_degradation() -> None:
    # If air quality endpoint fails (500 or timeout), returns None without throwing error
    respx.get(settings.open_meteo_air_quality_url).mock(
        return_value=Response(500, json={"error": "service down"})
    )

    aqi, is_stale = await fetch_air_quality(28.6139, 77.2090)
    assert aqi is None
    assert not is_stale
