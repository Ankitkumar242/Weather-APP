"""IP Geolocation service using ipwho.is with ipapi.co fallback."""

from __future__ import annotations

import hashlib
from typing import Any

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.http import resilient_request
from app.models.schemas import IPLocationResponse
from app.services.geocoding import normalize_state_name

settings = get_settings()


def _hash_ip(ip: str | None) -> str:
    """Hash client IP to preserve privacy while supporting per-IP caching."""
    if not ip or ip in ("127.0.0.1", "::1", "testclient"):
        return "loopback"
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


async def locate_by_ip(client_ip: str | None = None) -> IPLocationResponse:
    """
    Locate client by IP using ipwho.is, falling back to ipapi.co.
    If both fail, returns default location (New Delhi).
    Raw IP is never logged.
    """
    hashed_key = _hash_ip(client_ip)

    async def _fetch() -> dict[str, Any]:
        # 1. Primary: ipwho.is
        try:
            url = f"{settings.ipwhois_url.rstrip('/')}/{client_ip}" if client_ip and client_ip not in ("127.0.0.1", "::1", "testclient") else settings.ipwhois_url
            res = await resilient_request("GET", url, max_retries=1)
            if res.status_code == 200:
                data = res.json()
                if data.get("success") is not False and data.get("latitude") and data.get("longitude"):
                    return {
                        "city": data.get("city") or settings.default_city_name,
                        "region": data.get("region") or settings.default_state_name,
                        "country": data.get("country") or settings.default_country_name,
                        "latitude": float(data["latitude"]),
                        "longitude": float(data["longitude"]),
                    }
        except Exception:
            pass

        # 2. Secondary backup: ipapi.co
        try:
            url2 = f"https://ipapi.co/{client_ip}/json/" if client_ip and client_ip not in ("127.0.0.1", "::1", "testclient") else settings.ipapi_url
            res2 = await resilient_request("GET", url2, headers={"User-Agent": settings.nominatim_user_agent}, max_retries=1)
            if res2.status_code == 200:
                data2 = res2.json()
                if data2.get("latitude") and data2.get("longitude"):
                    return {
                        "city": data2.get("city") or settings.default_city_name,
                        "region": data2.get("region") or settings.default_state_name,
                        "country": data2.get("country_name") or settings.default_country_name,
                        "latitude": float(data2["latitude"]),
                        "longitude": float(data2["longitude"]),
                    }
        except Exception:
            pass

        # 3. Fallback to default configured city
        return {
            "city": settings.default_city_name,
            "region": settings.default_state_name,
            "country": settings.default_country_name,
            "latitude": settings.default_latitude,
            "longitude": settings.default_longitude,
        }

    loc_dict, _ = await cache_manager.get_or_set_coalesced("ip_locate", hashed_key, _fetch)

    return IPLocationResponse(
        city=str(loc_dict.get("city", settings.default_city_name)),
        state=normalize_state_name(loc_dict.get("region", settings.default_state_name)),
        country=str(loc_dict.get("country", settings.default_country_name)),
        latitude=float(loc_dict.get("latitude", settings.default_latitude)),
        longitude=float(loc_dict.get("longitude", settings.default_longitude)),
        is_approximate=True,
    )
