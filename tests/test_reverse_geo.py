"""Tests for reverse geocoding via OpenStreetMap Nominatim."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.reverse_geo import reverse_geocode

settings = get_settings()


@pytest.mark.asyncio
@respx.mock
async def test_reverse_geocode_success() -> None:
    mock_nominatim = {
        "display_name": "New Delhi, Delhi, India",
        "name": "New Delhi",
        "address": {
            "city": "New Delhi",
            "state": "National Capital Territory of Delhi",
            "country": "India",
            "country_code": "in",
        },
    }

    respx.get(settings.nominatim_reverse_url).mock(
        return_value=Response(200, json=mock_nominatim)
    )

    result = await reverse_geocode(28.6139, 77.2090)
    assert result.city == "New Delhi"
    assert result.state == "Delhi"  # normalized
    assert result.country == "India"
    assert result.country_code == "in"


@pytest.mark.asyncio
@respx.mock
async def test_reverse_geocode_failure_fallback() -> None:
    respx.get(settings.nominatim_reverse_url).mock(
        return_value=Response(500, json={"error": "service down"})
    )

    result = await reverse_geocode(28.6139, 77.2090)
    # Should not crash, returns coordinate fallback
    assert result.latitude == 28.6139
    assert result.longitude == 77.2090
    assert result.country == "India"
