"""Tests for Open-Meteo forecast service."""

from __future__ import annotations

from typing import cast

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.open_meteo import (
    fetch_batch_forecast,
    fetch_raw_forecast,
    get_condition_label,
    get_uv_category,
    parse_current_weather,
    parse_daily_timeline,
    parse_hourly_forecast,
)
from tests.conftest import MOCK_FORECAST_DATA

settings = get_settings()


def test_wmo_code_mapping() -> None:
    assert get_condition_label(0) == "Clear sky"
    assert get_condition_label(65) == "Heavy rain"
    assert get_condition_label(95) == "Thunderstorm"
    assert get_condition_label(999) == "Unknown"


def test_uv_categories() -> None:
    assert get_uv_category(None) is None
    assert get_uv_category(1.5) == "Low"
    assert get_uv_category(4.0) == "Moderate"
    assert get_uv_category(6.8) == "High"
    assert get_uv_category(9.5) == "Very High"
    assert get_uv_category(12.0) == "Extreme"


def test_parse_current_weather() -> None:
    current = parse_current_weather(
        cast(dict, MOCK_FORECAST_DATA["current"]), cast(dict, MOCK_FORECAST_DATA["daily"])
    )
    assert current.temperature == 32.5
    assert current.apparent_temperature == 35.0
    assert current.relative_humidity == 55.0
    assert current.condition_label == "Mainly clear"
    assert current.temp_max_today == 36.0
    assert current.temp_min_today == 25.0
    assert current.sunrise == "2026-10-06T06:15"


def test_parse_daily_timeline_15_days() -> None:
    daily_items = parse_daily_timeline(cast(dict, MOCK_FORECAST_DATA["daily"]), "2026-10-06T12:00")
    assert len(daily_items) == 15

    # Exactly 7 past days
    past_items = [d for d in daily_items if d.kind == "past"]
    assert len(past_items) == 7
    assert past_items[0].date == "2026-09-29"
    assert past_items[-1].date == "2026-10-05"

    # Exactly 1 today
    today_items = [d for d in daily_items if d.kind == "today"]
    assert len(today_items) == 1
    assert today_items[0].date == "2026-10-06"
    assert today_items[0].temp_max == 36.0

    # Exactly 7 forecast days
    forecast_items = [d for d in daily_items if d.kind == "forecast"]
    assert len(forecast_items) == 7
    assert forecast_items[0].date == "2026-10-07"
    assert forecast_items[-1].date == "2026-10-13"


def test_parse_hourly_forecast_48_hours() -> None:
    hourly_items = parse_hourly_forecast(
        cast(dict, MOCK_FORECAST_DATA["hourly"]), "2026-10-06T12:00"
    )
    assert len(hourly_items) == 48
    assert hourly_items[0].time == "2026-10-06T12:00"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_raw_forecast_with_cache() -> None:
    lat, lon = 28.6139, 77.2090
    route = respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=MOCK_FORECAST_DATA)
    )

    # First call - hits upstream
    data1, is_stale1 = await fetch_raw_forecast(lat, lon)
    assert not is_stale1
    assert data1["current"]["temperature_2m"] == 32.5
    assert route.call_count == 1

    # Second call with same coordinates (or rounded) - hits memory cache
    data2, is_stale2 = await fetch_raw_forecast(lat, lon)
    assert not is_stale2
    assert data2["current"]["temperature_2m"] == 32.5
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_fetch_batch_forecast_deduplication() -> None:
    # Chandigarh is queried for 3 different items (Punjab, Haryana, UT)
    coords = [(30.7333, 76.7794), (30.7333, 76.7794), (28.6139, 77.2090)]

    mock_batch_resp = [
        {"latitude": 30.73, "current": {"temperature_2m": 31.0, "weather_code": 1}},
        {"latitude": 28.61, "current": {"temperature_2m": 33.0, "weather_code": 0}},
    ]

    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=mock_batch_resp)
    )

    results = await fetch_batch_forecast(coords)
    assert len(results) == 3
    # Both identical coordinates receive the same result
    assert results[0]["current"]["temperature_2m"] == 31.0
    assert results[1]["current"]["temperature_2m"] == 31.0
    assert results[2]["current"]["temperature_2m"] == 33.0
