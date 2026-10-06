"""Tests for state and country aggregation services."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.aggregate import (
    compute_country_overview,
    compute_state_overview,
    get_all_states,
    get_state_by_slug,
)

settings = get_settings()


def test_get_all_states() -> None:
    states = get_all_states()
    assert len(states) == 36
    delhi = next((s for s in states if s.slug == "delhi"), None)
    assert delhi is not None
    assert delhi.capital == "New Delhi"
    assert len(delhi.cities) >= 1
    assert delhi.cities[0].is_capital is True


def test_get_state_by_slug() -> None:
    rajasthan = get_state_by_slug("rajasthan")
    assert rajasthan.name == "Rajasthan"
    assert rajasthan.capital == "Jaipur"


@pytest.mark.asyncio
@respx.mock
async def test_compute_state_overview() -> None:
    state = get_state_by_slug("delhi")
    mock_batch = [
        {
            "latitude": c.lat,
            "current": {"time": "2026-10-06T12:00", "temperature_2m": 33.0, "weather_code": 1},
            "daily": {
                "time": ["2026-10-05", "2026-10-06", "2026-10-07"],
                "temperature_2m_max": [34.0, 35.0, 34.0],
                "temperature_2m_min": [24.0, 25.0, 23.0],
                "precipitation_sum": [0.0, 0.0, 2.0],
            },
        }
        for c in state.cities
    ]

    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=mock_batch)
    )

    overview = await compute_state_overview("delhi")
    assert overview.state.name == "Delhi"
    assert len(overview.cities_weather) == len(state.cities)
    assert len(overview.trend) == 3
    assert overview.trend[1].kind == "today"


@pytest.mark.asyncio
@respx.mock
async def test_compute_country_overview() -> None:
    states = get_all_states()
    mock_batch = [
        {
            "latitude": s.lat,
            "current": {
                "time": "2026-10-06T12:00",
                "temperature_2m": 25.0 + (i % 15),
                "weather_code": 0,
            },
            "daily": {
                "temperature_2m_max": [30.0],
                "temperature_2m_min": [20.0],
                "precipitation_probability_max": [i % 50],
            },
        }
        for i, s in enumerate(states)
    ]

    respx.get(settings.open_meteo_forecast_url).mock(
        return_value=Response(200, json=mock_batch)
    )

    country = await compute_country_overview()
    assert len(country.capitals_weather) == 36
    assert country.hottest is not None
    assert country.coldest is not None
