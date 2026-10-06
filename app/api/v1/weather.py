"""Weather API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Query, Request

from app.core.ratelimit import limiter
from app.models.schemas import (
    LocationInfo,
    WeatherMetadata,
    WeatherResponse,
)
from app.services.air_quality import fetch_air_quality
from app.services.insights import generate_insights
from app.services.open_meteo import (
    fetch_raw_forecast,
    parse_current_weather,
    parse_daily_timeline,
    parse_hourly_forecast,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherResponse)
@limiter.limit("60/minute")
async def get_weather(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    name: str | None = Query(None, description="Location name if known"),
    state: str | None = Query(None, description="State name if known"),
    country: str = Query("India", description="Country name"),
    is_approximate: bool = Query(False, description="Whether location is IP approximate"),
) -> WeatherResponse:
    """
    Get full weather report for a coordinate:
    - Current conditions
    - Next 48h hourly
    - 15-day timeline (7 past + today + 7 forecast)
    - Air quality (US AQI, PM2.5, PM10)
    - Smart rule-based insights and carry tips
    - Stale cache flag and timestamps
    """
    # 1. Fetch raw forecast
    forecast_raw, is_stale_forecast = await fetch_raw_forecast(lat, lon)

    # 2. Extract current, daily, and hourly components
    current_raw = forecast_raw.get("current", {})
    daily_raw = forecast_raw.get("daily", {})
    hourly_raw = forecast_raw.get("hourly", {})

    local_time = str(current_raw.get("time", datetime.now(UTC).isoformat()))

    current = parse_current_weather(current_raw, daily_raw)
    daily = parse_daily_timeline(daily_raw, local_time)
    hourly = parse_hourly_forecast(hourly_raw, local_time)

    # 3. Fetch air quality
    air_quality, is_stale_aqi = await fetch_air_quality(lat, lon)

    # 4. Generate rule insights
    insights = generate_insights(current, daily, air_quality)

    # 5. Build location information
    location = LocationInfo(
        name=name or f"{lat:.2f}, {lon:.2f}",
        state=state,
        country=country,
        latitude=lat,
        longitude=lon,
        timezone=str(forecast_raw.get("timezone", "auto")),
        is_approximate=is_approximate,
    )

    metadata = WeatherMetadata(
        fetched_at=datetime.now(UTC).isoformat(),
        stale=is_stale_forecast or is_stale_aqi,
        cached=False,  # Set based on retrieval
    )

    return WeatherResponse(
        location=location,
        current=current,
        hourly=hourly,
        daily=daily,
        air_quality=air_quality,
        insights=insights,
        meta=metadata,
    )
