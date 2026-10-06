"""State and country aggregation services for Indian regions."""

from __future__ import annotations

import json
import os
from typing import Any

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.errors import NotFoundError
from app.models.schemas import (
    CityItem,
    CityOverviewItem,
    CountryOverviewResponse,
    DailyTrendPoint,
    StateOverviewResponse,
    StateSummary,
    WeatherMetadata,
)
from app.services.open_meteo import fetch_batch_forecast, get_condition_label

settings = get_settings()

_regions_data: list[dict[str, Any]] | None = None


def load_regions_data() -> list[dict[str, Any]]:
    """Load pre-generated Indian regions dataset from app/data/regions/in.json."""
    global _regions_data
    if _regions_data is None:
        path = os.path.join("app", "data", "regions", "in.json")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            _regions_data = json.load(f)
    return _regions_data or []


def get_all_states() -> list[StateSummary]:
    """Return summary list of all 36 Indian states and union territories."""
    data = load_regions_data()
    output: list[StateSummary] = []
    for s in data:
        cities = [CityItem(**c) for c in s.get("cities", [])]
        output.append(
            StateSummary(
                name=s["name"],
                slug=s["slug"],
                type=s["type"],
                capital=s["capital"],
                lat=s["lat"],
                lon=s["lon"],
                cities=cities,
            )
        )
    return output


def get_state_by_slug(slug: str) -> StateSummary:
    """Find a state by kebab-case slug or raise NotFoundError."""
    states = get_all_states()
    for s in states:
        if s.slug.lower() == slug.lower():
            return s
    raise NotFoundError(f"State or Union Territory '{slug}' not found.")


async def compute_state_overview(slug: str) -> StateOverviewResponse:
    """
    Compute batched overview for all cities in a state + 15-day averaged trend.
    Cached for 15 minutes.
    """
    state = get_state_by_slug(slug)
    cache_key = f"state:{slug}"

    async def _fetch() -> dict[str, Any]:
        coords = [(c.lat, c.lon) for c in state.cities]
        batch_results = await fetch_batch_forecast(coords)

        cities_weather: list[dict[str, Any]] = []
        date_counts: dict[str, int] = {}
        date_max_sum: dict[str, float] = {}
        date_min_sum: dict[str, float] = {}
        date_precip_sum: dict[str, float] = {}

        ref_local_date = ""

        for idx, city in enumerate(state.cities):
            res = batch_results[idx] if idx < len(batch_results) else {}
            curr = res.get("current", {})
            daily = res.get("daily", {})

            if not ref_local_date and curr.get("time"):
                ref_local_date = str(curr["time"])[:10]

            temp = float(curr.get("temperature_2m", 0.0))
            code = int(curr.get("weather_code", 0))

            daily_times = daily.get("time", [])
            max_t = temp
            min_t = temp
            precip_prob = None

            if daily_times:
                try:
                    today_idx = 0
                    if ref_local_date in daily_times:
                        today_idx = daily_times.index(ref_local_date)

                    if (
                        "temperature_2m_max" in daily
                        and len(daily["temperature_2m_max"]) > today_idx
                    ):
                        max_t = float(daily["temperature_2m_max"][today_idx] or temp)
                    if (
                        "temperature_2m_min" in daily
                        and len(daily["temperature_2m_min"]) > today_idx
                    ):
                        min_t = float(daily["temperature_2m_min"][today_idx] or temp)
                    if (
                        "precipitation_probability_max" in daily
                        and len(daily["precipitation_probability_max"]) > today_idx
                    ):
                        val = daily["precipitation_probability_max"][today_idx]
                        precip_prob = float(val) if val is not None else None
                except Exception:
                    pass

            cities_weather.append({
                "name": city.name,
                "lat": city.lat,
                "lon": city.lon,
                "is_capital": city.is_capital,
                "current_temp": temp,
                "weather_code": code,
                "condition_label": get_condition_label(code),
                "temp_max": max_t,
                "temp_min": min_t,
                "precipitation_probability": precip_prob,
                "wind_speed": float(curr.get("wind_speed_10m", 0.0)),
            })

            times = daily.get("time", [])
            d_maxes = daily.get("temperature_2m_max", [])
            d_mins = daily.get("temperature_2m_min", [])
            d_precips = daily.get("precipitation_sum", [])

            for d_idx, date_str in enumerate(times):
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
                if len(d_maxes) > d_idx and d_maxes[d_idx] is not None:
                    date_max_sum[date_str] = date_max_sum.get(date_str, 0.0) + float(d_maxes[d_idx])
                if len(d_mins) > d_idx and d_mins[d_idx] is not None:
                    date_min_sum[date_str] = date_min_sum.get(date_str, 0.0) + float(d_mins[d_idx])
                if len(d_precips) > d_idx and d_precips[d_idx] is not None:
                    date_precip_sum[date_str] = date_precip_sum.get(date_str, 0.0) + float(
                        d_precips[d_idx]
                    )

        trend: list[dict[str, Any]] = []
        for date_str in sorted(date_counts.keys()):
            count = max(date_counts[date_str], 1)
            kind = "forecast"
            if ref_local_date:
                if date_str < ref_local_date:
                    kind = "past"
                elif date_str == ref_local_date:
                    kind = "today"

            trend.append({
                "date": date_str,
                "kind": kind,
                "avg_temp_max": round(date_max_sum.get(date_str, 0.0) / count, 1),
                "avg_temp_min": round(date_min_sum.get(date_str, 0.0) / count, 1),
                "avg_precipitation": round(date_precip_sum.get(date_str, 0.0) / count, 1),
            })

        return {
            "cities_weather": cities_weather,
            "trend": trend,
        }

    raw_data, is_stale = await cache_manager.get_or_set_coalesced(
        "state_overview", cache_key, _fetch
    )

    cities_models = [CityOverviewItem(**cw) for cw in raw_data.get("cities_weather", [])]
    trend_models = [DailyTrendPoint(**tp) for tp in raw_data.get("trend", [])]

    return StateOverviewResponse(
        state=state,
        cities_weather=cities_models,
        trend=trend_models,
        meta=WeatherMetadata(fetched_at="", stale=is_stale, cached=False),
    )


async def compute_country_overview() -> CountryOverviewResponse:
    """
    Fetch current conditions for all 36 Indian state and UT capitals in one batched request.
    Calculates national highlights (hottest, coldest, wettest capital).
    Cached for 15 minutes.
    """
    states = get_all_states()
    cache_key = "country:in"

    async def _fetch() -> dict[str, Any]:
        coords = [(s.lat, s.lon) for s in states]
        batch_results = await fetch_batch_forecast(coords)

        capitals_weather: list[dict[str, Any]] = []
        for idx, state in enumerate(states):
            res = batch_results[idx] if idx < len(batch_results) else {}
            curr = res.get("current", {})
            daily = res.get("daily", {})

            temp = float(curr.get("temperature_2m", 0.0))
            code = int(curr.get("weather_code", 0))

            max_t = temp
            min_t = temp
            precip_prob = None
            if "temperature_2m_max" in daily and len(daily["temperature_2m_max"]) > 0:
                max_t = float(daily["temperature_2m_max"][0] or temp)
            if "temperature_2m_min" in daily and len(daily["temperature_2m_min"]) > 0:
                min_t = float(daily["temperature_2m_min"][0] or temp)
            if (
                "precipitation_probability_max" in daily
                and len(daily["precipitation_probability_max"]) > 0
            ):
                precip_prob = daily["precipitation_probability_max"][0]

            capitals_weather.append({
                "name": f"{state.capital} ({state.name})",
                "lat": state.lat,
                "lon": state.lon,
                "is_capital": True,
                "current_temp": temp,
                "weather_code": code,
                "condition_label": get_condition_label(code),
                "temp_max": max_t,
                "temp_min": min_t,
                "precipitation_probability": float(precip_prob) if precip_prob is not None else None,
                "wind_speed": float(curr.get("wind_speed_10m", 0.0)),
            })

        hottest = (
            max(capitals_weather, key=lambda c: c["current_temp"]) if capitals_weather else None
        )
        coldest = (
            min(capitals_weather, key=lambda c: c["current_temp"]) if capitals_weather else None
        )
        wettest = (
            max(
                capitals_weather,
                key=lambda c: (c["precipitation_probability"] or 0),
            )
            if capitals_weather
            else None
        )

        return {
            "capitals_weather": capitals_weather,
            "hottest": hottest,
            "coldest": coldest,
            "wettest": wettest,
        }

    raw_data, is_stale = await cache_manager.get_or_set_coalesced(
        "state_overview", cache_key, _fetch
    )

    cap_models = [CityOverviewItem(**cw) for cw in raw_data.get("capitals_weather", [])]
    hottest_m = (
        CityOverviewItem(**raw_data["hottest"]) if raw_data.get("hottest") else None
    )
    coldest_m = (
        CityOverviewItem(**raw_data["coldest"]) if raw_data.get("coldest") else None
    )
    wettest_m = (
        CityOverviewItem(**raw_data["wettest"]) if raw_data.get("wettest") else None
    )

    return CountryOverviewResponse(
        capitals_weather=cap_models,
        hottest=hottest_m,
        coldest=coldest_m,
        wettest=wettest_m,
        meta=WeatherMetadata(fetched_at="", stale=is_stale, cached=False),
    )
