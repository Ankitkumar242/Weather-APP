"""Tests for Smart Insights rule engine."""

from __future__ import annotations

from app.models.schemas import AirQualityData, CurrentWeather, DailyWeatherItem
from app.services.insights import generate_insights


def test_heat_advisory_and_tip() -> None:
    current = CurrentWeather(
        time="2026-10-06T14:00",
        temperature=41.5,
        apparent_temperature=44.0,
        relative_humidity=30.0,
        is_day=1,
        precipitation=0.0,
        weather_code=0,
        condition_label="Clear sky",
        cloud_cover=0.0,
        pressure=1008.0,
        wind_speed=15.0,
        wind_direction=200.0,
        temp_max_today=42.0,
        temp_min_today=28.0,
        uv_index=8.5,
        uv_category="Very High",
    )
    daily = [
        DailyWeatherItem(
            date="2026-10-06",
            kind="today",
            weather_code=0,
            condition_label="Clear sky",
            temp_max=42.0,
            temp_min=28.0,
            precipitation_sum=0.0,
        )
    ]

    insights = generate_insights(current, daily, None)
    assert any("Extreme Heat" in a for a in insights.alerts)
    assert any("High UV" in a for a in insights.alerts)
    assert "Carry water" in (insights.tip or "")


def test_heavy_rain_advisory() -> None:
    current = CurrentWeather(
        time="2026-10-06T14:00",
        temperature=24.0,
        apparent_temperature=24.0,
        relative_humidity=95.0,
        is_day=1,
        precipitation=18.0,
        weather_code=65,
        condition_label="Heavy rain",
        cloud_cover=100.0,
        pressure=1002.0,
        wind_speed=30.0,
        wind_direction=90.0,
    )
    daily = [
        DailyWeatherItem(
            date="2026-10-06",
            kind="today",
            weather_code=65,
            condition_label="Heavy rain",
            temp_max=26.0,
            temp_min=22.0,
            precipitation_sum=25.0,
        )
    ]

    insights = generate_insights(current, daily, None)
    assert any("Heavy Rain" in a for a in insights.alerts)
    assert "umbrella" in (insights.tip or "").lower()


def test_poor_aqi_alert() -> None:
    current = CurrentWeather(
        time="2026-10-06T14:00",
        temperature=25.0,
        apparent_temperature=25.0,
        relative_humidity=50.0,
        is_day=1,
        precipitation=0.0,
        weather_code=1,
        condition_label="Mainly clear",
        cloud_cover=100.0,
        pressure=1012.0,
        wind_speed=5.0,
        wind_direction=180.0,
    )
    daily = [
        DailyWeatherItem(
            date="2026-10-06",
            kind="today",
            weather_code=1,
            condition_label="Mainly clear",
            temp_max=27.0,
            temp_min=20.0,
            precipitation_sum=0.0,
        )
    ]
    aqi = AirQualityData(
        us_aqi=210,
        aqi_category="Very Unhealthy",
        pm2_5=120.0,
        pm10=250.0,
    )

    insights = generate_insights(current, daily, aqi)
    assert any("Poor Air Quality" in a for a in insights.alerts)
    assert "N95 mask" in (insights.tip or "")
