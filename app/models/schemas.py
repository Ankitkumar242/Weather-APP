"""Pydantic v2 schemas for API requests and responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    name: str = Field(description="City or place name")
    state: str | None = Field(default=None, description="State, province, or region name")
    country: str = Field(default="India", description="Country name")
    country_code: str | None = Field(default=None, description="ISO country code")
    latitude: float = Field(ge=-90.0, le=90.0, description="Latitude")
    longitude: float = Field(ge=-180.0, le=180.0, description="Longitude")
    timezone: str = Field(default="auto", description="Timezone name")
    is_approximate: bool = Field(default=False, description="True if derived from IP geolocation")


class CurrentWeather(BaseModel):
    time: str = Field(description="Local observation timestamp")
    temperature: float = Field(description="Current temperature in Celsius")
    apparent_temperature: float = Field(description="Feels-like temperature in Celsius")
    relative_humidity: float = Field(description="Relative humidity in percentage")
    is_day: int = Field(description="1 for day, 0 for night")
    precipitation: float = Field(default=0.0, description="Precipitation in mm")
    weather_code: int = Field(description="WMO weather interpretation code")
    condition_label: str = Field(description="Human readable weather condition")
    cloud_cover: float = Field(default=0.0, description="Cloud cover percentage")
    pressure: float = Field(description="Atmospheric pressure in hPa")
    wind_speed: float = Field(description="Wind speed in km/h")
    wind_direction: float = Field(description="Wind direction in degrees")
    wind_gusts: float | None = Field(default=None, description="Wind gusts in km/h")
    dew_point: float | None = Field(default=None, description="Dew point in Celsius")
    visibility: float | None = Field(default=None, description="Visibility in meters")
    uv_index: float | None = Field(default=None, description="Current UV index")
    uv_category: str | None = Field(default=None, description="UV risk category")
    temp_max_today: float | None = Field(default=None, description="Today maximum temperature")
    temp_min_today: float | None = Field(default=None, description="Today minimum temperature")
    sunrise: str | None = Field(default=None, description="Sunrise local time")
    sunset: str | None = Field(default=None, description="Sunset local time")


class HourlyWeatherItem(BaseModel):
    time: str = Field(description="ISO local time string")
    temperature: float = Field(description="Temperature in Celsius")
    apparent_temperature: float | None = Field(default=None, description="Feels-like temperature")
    precipitation_probability: float | None = Field(default=None, description="Rain chance 0-100%")
    precipitation: float | None = Field(default=None, description="Rainfall in mm")
    weather_code: int = Field(description="WMO code")
    condition_label: str = Field(description="Weather condition label")
    wind_speed: float | None = Field(default=None, description="Wind speed in km/h")
    uv_index: float | None = Field(default=None, description="UV index")
    is_day: int | None = Field(default=None, description="1 for day, 0 for night")


class DailyWeatherItem(BaseModel):
    date: str = Field(description="ISO local date string YYYY-MM-DD")
    kind: Literal["past", "today", "forecast"] = Field(
        description="Temporal classification relative to local date"
    )
    weather_code: int = Field(description="WMO code")
    condition_label: str = Field(description="Condition label")
    temp_max: float = Field(description="Maximum daily temperature in Celsius")
    temp_min: float = Field(description="Minimum daily temperature in Celsius")
    apparent_temp_max: float | None = Field(default=None)
    apparent_temp_min: float | None = Field(default=None)
    precipitation_sum: float | None = Field(default=None, description="Total rain in mm")
    precipitation_probability_max: float | None = Field(
        default=None, description="Peak rain chance %"
    )
    wind_speed_max: float | None = Field(default=None, description="Max wind speed km/h")
    wind_gusts_max: float | None = Field(default=None, description="Peak gust speed km/h")
    wind_direction_dominant: float | None = Field(
        default=None, description="Dominant wind direction"
    )
    uv_index_max: float | None = Field(default=None, description="Peak UV index")
    sunrise: str | None = Field(default=None, description="Local sunrise")
    sunset: str | None = Field(default=None, description="Local sunset")
    daylight_duration: float | None = Field(
        default=None, description="Daylight duration in seconds"
    )


class AirQualityData(BaseModel):
    us_aqi: int | None = Field(default=None, description="US AQI value")
    aqi_category: str | None = Field(default=None, description="AQI Category")
    pm2_5: float | None = Field(default=None, description="PM2.5 concentration µg/m³")
    pm10: float | None = Field(default=None, description="PM10 concentration µg/m³")
    ozone: float | None = Field(default=None, description="Ozone concentration µg/m³")
    hourly_aqi: list[dict[str, Any]] | None = Field(default=None, description="Hourly AQI trend")


class SmartInsights(BaseModel):
    alerts: list[str] = Field(
        default_factory=list, description="Rule-based weather advisory alerts"
    )
    tip: str | None = Field(default=None, description="Practical carry/wear tip")
    summary: str | None = Field(default=None, description="Brief narrative weather takeaway")


class WeatherMetadata(BaseModel):
    fetched_at: str = Field(description="ISO UTC fetch timestamp")
    stale: bool = Field(default=False, description="True if returned from expired cache on failure")
    cached: bool = Field(default=False, description="True if fulfilled from memory cache")


class WeatherResponse(BaseModel):
    location: LocationInfo
    current: CurrentWeather
    hourly: list[HourlyWeatherItem] = Field(description="Next 48 hours from current local hour")
    daily: list[DailyWeatherItem] = Field(
        description="15 days timeline: exactly 7 past, 1 today, 7 forecast"
    )
    air_quality: AirQualityData | None = None
    insights: SmartInsights
    meta: WeatherMetadata


class CityItem(BaseModel):
    name: str
    lat: float
    lon: float
    population: int | None = None
    is_capital: bool = False


class StateSummary(BaseModel):
    name: str
    slug: str
    type: Literal["state", "ut"]
    capital: str
    lat: float
    lon: float
    cities: list[CityItem] = Field(default_factory=list)


class CityOverviewItem(BaseModel):
    name: str
    lat: float
    lon: float
    is_capital: bool = False
    current_temp: float
    weather_code: int
    condition_label: str
    temp_max: float
    temp_min: float
    precipitation_probability: float | None = None
    wind_speed: float | None = None


class DailyTrendPoint(BaseModel):
    date: str
    kind: Literal["past", "today", "forecast"]
    avg_temp_max: float
    avg_temp_min: float
    avg_precipitation: float


class StateOverviewResponse(BaseModel):
    state: StateSummary
    cities_weather: list[CityOverviewItem]
    trend: list[DailyTrendPoint]
    meta: WeatherMetadata


class CountryOverviewResponse(BaseModel):
    capitals_weather: list[CityOverviewItem]
    hottest: CityOverviewItem | None = None
    coldest: CityOverviewItem | None = None
    wettest: CityOverviewItem | None = None
    meta: WeatherMetadata


class PlaceSearchResult(BaseModel):
    id: int | None = None
    name: str
    admin1: str | None = None
    country: str
    country_code: str | None = None
    latitude: float
    longitude: float
    population: int | None = None
    timezone: str | None = None


class ReverseGeoResponse(BaseModel):
    name: str
    city: str | None = None
    state: str | None = None
    country: str
    country_code: str | None = None
    display_name: str
    latitude: float
    longitude: float


class IPLocationResponse(BaseModel):
    city: str
    state: str | None = None
    country: str
    latitude: float
    longitude: float
    is_approximate: bool = True


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str
    version: str = "0.1.0"
