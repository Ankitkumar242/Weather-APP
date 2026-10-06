"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="SkyPulse")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Upstream URLs
    open_meteo_forecast_url: str = Field(default="https://api.open-meteo.com/v1/forecast")
    open_meteo_air_quality_url: str = Field(
        default="https://air-quality-api.open-meteo.com/v1/air-quality"
    )
    open_meteo_geocoding_url: str = Field(default="https://geocoding-api.open-meteo.com/v1/search")
    nominatim_reverse_url: str = Field(default="https://nominatim.openstreetmap.org/reverse")
    nominatim_user_agent: str = Field(
        default="SkyPulseWeatherApp/1.0 (contact: support@skypulse.local)"
    )
    ipwhois_url: str = Field(default="https://ipwho.is/")
    ipapi_url: str = Field(default="https://ipapi.co/json/")

    # HTTP Client
    http_timeout_seconds: float = Field(default=8.0)
    http_max_retries: int = Field(default=2)
    http_backoff_factor: float = Field(default=0.5)

    # Cache TTLs (seconds)
    cache_ttl_forecast: int = Field(default=600)  # 10 min
    cache_ttl_air_quality: int = Field(default=1800)  # 30 min
    cache_ttl_state_overview: int = Field(default=900)  # 15 min
    cache_ttl_search: int = Field(default=86400)  # 24 h
    cache_ttl_reverse_geo: int = Field(default=2592000)  # 30 days
    cache_ttl_ip_locate: int = Field(default=86400)  # 24 h

    # Rate Limiting
    rate_limit_default: str = Field(default="60/minute")

    # Default location
    default_city_name: str = Field(default="New Delhi")
    default_state_name: str = Field(default="Delhi")
    default_country_name: str = Field(default="India")
    default_latitude: float = Field(default=28.6139)
    default_longitude: float = Field(default=77.2090)

    # Allowed CORS Origins
    allowed_origins: list[str] | str = Field(
        default_factory=lambda: [
            "https://localhost",
            "capacitor://localhost",
            "http://localhost",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

    # Smart Insights Thresholds
    threshold_heat_temp: float = Field(default=38.0)
    threshold_cold_temp: float = Field(default=8.0)
    threshold_high_uv: float = Field(default=7.0)
    threshold_poor_aqi: int = Field(default=150)
    threshold_strong_gust: float = Field(default=45.0)
    threshold_heavy_rain: float = Field(default=15.0)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(o).strip() for o in v if str(o).strip()]
        return [
            "https://localhost",
            "capacitor://localhost",
            "http://localhost",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on", "debug")
        return bool(v)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
