"""Reverse geocoding service using OpenStreetMap Nominatim with rate limiting and 30-day cache."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.http import resilient_request
from app.models.schemas import ReverseGeoResponse
from app.services.geocoding import normalize_state_name

settings = get_settings()

# Nominatim rate limiter: enforce strictly >= 1.0 second between requests
_nominatim_lock = asyncio.Lock()
_last_nominatim_request_time = 0.0


async def _rate_limit_nominatim() -> None:
    """Enforce maximum 1 request per second for Nominatim API."""
    global _last_nominatim_request_time
    async with _nominatim_lock:
        now = time.monotonic()
        elapsed = now - _last_nominatim_request_time
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _last_nominatim_request_time = time.monotonic()


def _extract_city_name(address: dict[str, Any], raw_name: str | None = None) -> str:
    """Extract best candidate city or locality name."""
    candidates = ["city", "town", "village", "municipality", "suburb", "county", "state_district"]
    for key in candidates:
        if address.get(key):
            return str(address[key])
    return raw_name or "Unknown Location"


async def reverse_geocode(lat: float, lon: float) -> ReverseGeoResponse:
    """
    Reverse geocode coordinates using OSM Nominatim.
    Strictly rate limited to 1 req/s and cached for 30 days.
    Degrades gracefully to coordinate fallback on any error.
    """
    coord_key = cache_manager.coord_key(lat, lon)

    async def _fetch() -> dict[str, Any]:
        await _rate_limit_nominatim()
        params = {
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "format": "jsonv2",
            "zoom": 10,
            "addressdetails": 1,
        }
        try:
            res = await resilient_request(
                "GET",
                settings.nominatim_reverse_url,
                params=params,
                headers={"User-Agent": settings.nominatim_user_agent},
                max_retries=1,
            )
            if res.status_code != 200:
                return {}
            return res.json()
        except Exception:
            return {}

    raw_data, _ = await cache_manager.get_or_set_coalesced("reverse_geo", coord_key, _fetch)

    if not raw_data:
        return ReverseGeoResponse(
            name=f"{lat:.2f}, {lon:.2f}",
            city=None,
            state=None,
            country="India",
            country_code=None,
            display_name=f"{lat:.2f}, {lon:.2f}",
            latitude=lat,
            longitude=lon,
        )

    address = raw_data.get("address", {})
    city = _extract_city_name(address, raw_data.get("name"))
    raw_state = address.get("state")
    normalized_state = normalize_state_name(raw_state)
    country = str(address.get("country", "India"))
    country_code = address.get("country_code")
    display_name = str(raw_data.get("display_name", f"{city}, {normalized_state or country}"))

    return ReverseGeoResponse(
        name=city,
        city=city,
        state=normalized_state,
        country=country,
        country_code=country_code,
        display_name=display_name,
        latitude=lat,
        longitude=lon,
    )
