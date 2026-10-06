"""Air quality service using Open-Meteo Air Quality API."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.http import resilient_request
from app.models.schemas import AirQualityData

settings = get_settings()


def get_aqi_category(aqi: int | None) -> str | None:
    """Classify US AQI into standard categories."""
    if aqi is None:
        return None
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


async def fetch_air_quality(lat: float, lon: float) -> tuple[AirQualityData | None, bool]:
    """
    Fetch air quality data. Degrades gracefully to None on failure.
    Uses caching and request coalescing.
    """
    coord_key = cache_manager.coord_key(lat, lon)

    async def _fetch() -> dict[str, Any] | None:
        try:
            params = {
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "current": "us_aqi,pm2_5,pm10,ozone",
                "hourly": "us_aqi",
                "timezone": "auto",
            }
            res = await resilient_request(
                "GET", settings.open_meteo_air_quality_url, params=params, max_retries=1
            )
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            # Gracefully degrade if air quality upstream fails
            return None

    raw_data, is_stale = await cache_manager.get_or_set_coalesced("air_quality", coord_key, _fetch)

    if not raw_data:
        return None, False

    curr = raw_data.get("current", {})
    aqi_val = curr.get("us_aqi")
    us_aqi = int(aqi_val) if aqi_val is not None else None

    # Parse next 24-48 hours of hourly AQI if available
    hourly_raw = raw_data.get("hourly", {})
    hourly_times = hourly_raw.get("time", [])
    hourly_aqis = hourly_raw.get("us_aqi", [])

    hourly_list: list[dict[str, Any]] = []
    for i in range(min(len(hourly_times), 48)):
        val = hourly_aqis[i] if i < len(hourly_aqis) else None
        hourly_list.append({"time": hourly_times[i], "us_aqi": val})

    return (
        AirQualityData(
            us_aqi=us_aqi,
            aqi_category=get_aqi_category(us_aqi),
            pm2_5=float(curr["pm2_5"]) if curr.get("pm2_5") is not None else None,
            pm10=float(curr["pm10"]) if curr.get("pm10") is not None else None,
            ozone=float(curr["ozone"]) if curr.get("ozone") is not None else None,
            hourly_aqi=hourly_list if hourly_list else None,
        ),
        is_stale,
    )
