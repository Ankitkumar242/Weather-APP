"""Tests for IP geolocation service."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.ip_locate import locate_by_ip

settings = get_settings()


@pytest.mark.asyncio
@respx.mock
async def test_locate_by_ip_primary_success() -> None:
    mock_ipwhois = {
        "success": True,
        "city": "Bengaluru",
        "region": "Karnataka",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
    }

    respx.get(settings.ipwhois_url).mock(
        return_value=Response(200, json=mock_ipwhois)
    )

    result = await locate_by_ip("127.0.0.1")
    assert result.city == "Bengaluru"
    assert result.state == "Karnataka"
    assert result.latitude == 12.9716
    assert result.is_approximate is True


@pytest.mark.asyncio
@respx.mock
async def test_locate_by_ip_fallback_to_default_on_failure() -> None:
    # Primary fails
    respx.get(settings.ipwhois_url).mock(
        return_value=Response(500, json={"error": "failed"})
    )
    # Secondary fails
    respx.get(settings.ipapi_url).mock(
        return_value=Response(500, json={"error": "failed"})
    )

    result = await locate_by_ip("8.8.8.8")
    # Falls back gracefully to configured default (New Delhi)
    assert result.city == settings.default_city_name
    assert result.latitude == settings.default_latitude
    assert result.is_approximate is True
