"""Open-Meteo forecast service: single & batch requests, normalization, 15-day timeline, 48h hourly."""

from __future__ import annotations

from typing import Any, Literal

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.errors import UpstreamServiceError
from app.core.http import resilient_request
from app.models.schemas import CurrentWeather, DailyWeatherItem, HourlyWeatherItem

settings = get_settings()

WMO_CODE_MAP: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_condition_label(code: int) -> str:
    """Return friendly description for WMO code."""
    return WMO_CODE_MAP.get(code, "Unknown")


def get_uv_category(uv: float | None) -> str | None:
    """Classify UV index into WHO category."""
    if uv is None:
        return None
    if uv <= 2.0:
        return "Low"
    if uv <= 5.0:
        return "Moderate"
    if uv <= 7.0:
        return "High"
    if uv <= 10.0:
        return "Very High"
    return "Extreme"


def normalize_multi_response(raw_data: Any) -> list[dict[str, Any]]:
    """Normalize single object or array response into a list of objects."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        return [raw_data]
    return []


def parse_current_weather(
    current_raw: dict[str, Any], daily_raw: dict[str, Any] | None = None
) -> CurrentWeather:
    """Parse raw current block and supplement with today's high/low and sunrise/sunset."""
    temp = float(current_raw.get("temperature_2m", 0.0))
    apparent_temp = float(current_raw.get("apparent_temperature", temp))
    humidity = float(current_raw.get("relative_humidity_2m", 0.0))
    is_day = int(current_raw.get("is_day", 1))
    precip = float(current_raw.get("precipitation", 0.0))
    code = int(current_raw.get("weather_code", 0))
    cloud_cover = float(current_raw.get("cloud_cover", 0.0))
    pressure = float(current_raw.get("pressure_msl", 1013.25))
    wind_speed = float(current_raw.get("wind_speed_10m", 0.0))
    wind_direction = float(current_raw.get("wind_direction_10m", 0.0))
    wind_gusts = current_raw.get("wind_gusts_10m")
    dew_point = current_raw.get("dew_point_2m")
    visibility = current_raw.get("visibility")
    uv = current_raw.get("uv_index")

    # Today's high/low, sunrise, sunset from daily if available
    temp_max_today = None
    temp_min_today = None
    sunrise = None
    sunset = None

    if daily_raw and "time" in daily_raw:
        times = daily_raw["time"]
        local_date = str(current_raw.get("time", ""))[:10]
        try:
            today_idx = times.index(local_date)
            if (
                "temperature_2m_max" in daily_raw
                and len(daily_raw["temperature_2m_max"]) > today_idx
            ):
                temp_max_today = daily_raw["temperature_2m_max"][today_idx]
            if (
                "temperature_2m_min" in daily_raw
                and len(daily_raw["temperature_2m_min"]) > today_idx
            ):
                temp_min_today = daily_raw["temperature_2m_min"][today_idx]
            if "sunrise" in daily_raw and len(daily_raw["sunrise"]) > today_idx:
                sunrise = daily_raw["sunrise"][today_idx]
            if "sunset" in daily_raw and len(daily_raw["sunset"]) > today_idx:
                sunset = daily_raw["sunset"][today_idx]
        except ValueError:
            pass

    return CurrentWeather(
        time=str(current_raw.get("time", "")),
        temperature=temp,
        apparent_temperature=apparent_temp,
        relative_humidity=humidity,
        is_day=is_day,
        precipitation=precip,
        weather_code=code,
        condition_label=get_condition_label(code),
        cloud_cover=cloud_cover,
        pressure=pressure,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        wind_gusts=float(wind_gusts) if wind_gusts is not None else None,
        dew_point=float(dew_point) if dew_point is not None else None,
        visibility=float(visibility) if visibility is not None else None,
        uv_index=float(uv) if uv is not None else None,
        uv_category=get_uv_category(float(uv) if uv is not None else None),
        temp_max_today=float(temp_max_today) if temp_max_today is not None else None,
        temp_min_today=float(temp_min_today) if temp_min_today is not None else None,
        sunrise=sunrise,
        sunset=sunset,
    )


def _get_daily_opt(daily_raw: dict[str, Any], field: str, idx: int) -> float | None:
    arr = daily_raw.get(field)
    if arr is not None and len(arr) > idx and arr[idx] is not None:
        return float(arr[idx])
    return None


def _get_daily_opt_str(daily_raw: dict[str, Any], field: str, idx: int) -> str | None:
    arr = daily_raw.get(field)
    if arr is not None and len(arr) > idx and arr[idx] is not None:
        return str(arr[idx])
    return None


def parse_daily_timeline(daily_raw: dict[str, Any], local_time: str) -> list[DailyWeatherItem]:
    """
    Parse daily arrays into 15 items: exactly 7 past, 1 today, and 7 forecast.
    Classified strictly by the location's local date (from local_time).
    """
    times = daily_raw.get("time", [])
    local_date = local_time[:10]
    items: list[DailyWeatherItem] = []

    for i, date_str in enumerate(times):
        kind: Literal["past", "today", "forecast"]
        if date_str < local_date:
            kind = "past"
        elif date_str == local_date:
            kind = "today"
        else:
            kind = "forecast"

        code = int(daily_raw.get("weather_code", [0])[i])
        max_t = float(daily_raw.get("temperature_2m_max", [0.0])[i])
        min_t = float(daily_raw.get("temperature_2m_min", [0.0])[i])

        items.append(
            DailyWeatherItem(
                date=date_str,
                kind=kind,
                weather_code=code,
                condition_label=get_condition_label(code),
                temp_max=max_t,
                temp_min=min_t,
                apparent_temp_max=_get_daily_opt(daily_raw, "apparent_temperature_max", i),
                apparent_temp_min=_get_daily_opt(daily_raw, "apparent_temperature_min", i),
                precipitation_sum=_get_daily_opt(daily_raw, "precipitation_sum", i),
                precipitation_probability_max=_get_daily_opt(
                    daily_raw, "precipitation_probability_max", i
                ),
                wind_speed_max=_get_daily_opt(daily_raw, "wind_speed_10m_max", i),
                wind_gusts_max=_get_daily_opt(daily_raw, "wind_gusts_10m_max", i),
                wind_direction_dominant=_get_daily_opt(daily_raw, "wind_direction_10m_dominant", i),
                uv_index_max=_get_daily_opt(daily_raw, "uv_index_max", i),
                sunrise=_get_daily_opt_str(daily_raw, "sunrise", i),
                sunset=_get_daily_opt_str(daily_raw, "sunset", i),
                daylight_duration=_get_daily_opt(daily_raw, "daylight_duration", i),
            )
        )

    return items


def _get_hourly_val(
    hourly_raw: dict[str, Any], field: str, idx: int, default: float = 0.0
) -> float:
    arr = hourly_raw.get(field, [])
    if len(arr) > idx and arr[idx] is not None:
        return float(arr[idx])
    return default


def _get_hourly_opt_val(hourly_raw: dict[str, Any], field: str, idx: int) -> float | None:
    arr = hourly_raw.get(field, [])
    if len(arr) > idx and arr[idx] is not None:
        return float(arr[idx])
    return None


def parse_hourly_forecast(hourly_raw: dict[str, Any], local_time: str) -> list[HourlyWeatherItem]:
    """Slice next 48 hours starting from the current local hour."""
    times = hourly_raw.get("time", [])
    current_hour_prefix = local_time[:13] + ":00"

    start_idx = 0
    for i, t in enumerate(times):
        if t >= current_hour_prefix:
            start_idx = i
            break

    slice_times = times[start_idx : start_idx + 48]
    items: list[HourlyWeatherItem] = []

    for offset, t in enumerate(slice_times):
        idx = start_idx + offset
        code = int(_get_hourly_val(hourly_raw, "weather_code", idx, 0.0))

        items.append(
            HourlyWeatherItem(
                time=t,
                temperature=_get_hourly_val(hourly_raw, "temperature_2m", idx),
                apparent_temperature=_get_hourly_opt_val(hourly_raw, "apparent_temperature", idx),
                precipitation_probability=_get_hourly_opt_val(
                    hourly_raw, "precipitation_probability", idx
                ),
                precipitation=_get_hourly_opt_val(hourly_raw, "precipitation", idx),
                weather_code=code,
                condition_label=get_condition_label(code),
                wind_speed=_get_hourly_opt_val(hourly_raw, "wind_speed_10m", idx),
                uv_index=_get_hourly_opt_val(hourly_raw, "uv_index", idx),
                is_day=int(_get_hourly_opt_val(hourly_raw, "is_day", idx) or 1)
                if "is_day" in hourly_raw
                else None,
            )
        )

    return items


async def fetch_raw_forecast(lat: float, lon: float) -> tuple[dict[str, Any], bool]:
    """Fetch raw forecast data for a single location using cache and coalescing."""
    coord_key = cache_manager.coord_key(lat, lon)

    async def _fetch() -> dict[str, Any]:
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "timezone": "auto",
            "past_days": 7,
            "forecast_days": 8,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,dew_point_2m,visibility,uv_index",
            "hourly": "temperature_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m,uv_index",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant",
        }
        res = await resilient_request("GET", settings.open_meteo_forecast_url, params=params)
        if res.status_code != 200:
            raise UpstreamServiceError(
                f"Open-Meteo forecast failed with status {res.status_code}: {res.text}"
            )
        return res.json()

    data, is_stale = await cache_manager.get_or_set_coalesced("forecast", coord_key, _fetch)
    return data, is_stale


async def fetch_batch_forecast(coords: list[tuple[float, float]]) -> list[dict[str, Any]]:
    """
    Fetch forecasts for multiple coordinates in ONE batched request.
    Deduplicates identical coordinates (e.g. Chandigarh), queries Open-Meteo once,
    and fans results back out to match the input order.
    """
    if not coords:
        return []

    # Deduplicate unique coordinates (rounded to 2 decimals)
    unique_coords: list[tuple[float, float]] = []
    coord_to_idx: dict[str, int] = {}

    for lat, lon in coords:
        key = cache_manager.coord_key(lat, lon)
        if key not in coord_to_idx:
            coord_to_idx[key] = len(unique_coords)
            unique_coords.append((lat, lon))

    lats_str = ",".join(f"{round(c[0], 4)}" for c in unique_coords)
    lons_str = ",".join(f"{round(c[1], 4)}" for c in unique_coords)

    params = {
        "latitude": lats_str,
        "longitude": lons_str,
        "timezone": "auto",
        "past_days": 7,
        "forecast_days": 8,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
    }

    res = await resilient_request("GET", settings.open_meteo_forecast_url, params=params)
    if res.status_code != 200:
        raise UpstreamServiceError(
            f"Open-Meteo batch forecast failed with status {res.status_code}: {res.text}"
        )

    raw_items = normalize_multi_response(res.json())

    # Map results by unique coordinate key
    results_by_key: dict[str, dict[str, Any]] = {}
    for idx, (lat, lon) in enumerate(unique_coords):
        key = cache_manager.coord_key(lat, lon)
        if idx < len(raw_items):
            results_by_key[key] = raw_items[idx]
        else:
            results_by_key[key] = {}

    # Fan back out according to input coords
    output: list[dict[str, Any]] = []
    for lat, lon in coords:
        key = cache_manager.coord_key(lat, lon)
        output.append(results_by_key.get(key, {}))

    return output
