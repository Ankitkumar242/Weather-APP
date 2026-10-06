"""Rule-based smart weather insights and carry/wear tips."""

from __future__ import annotations

from app.config import get_settings
from app.models.schemas import AirQualityData, CurrentWeather, DailyWeatherItem, SmartInsights

settings = get_settings()


def generate_insights(
    current: CurrentWeather,
    daily_items: list[DailyWeatherItem],
    aqi_data: AirQualityData | None = None,
) -> SmartInsights:
    """
    Generate rule-based weather insights and practical tips.
    Label: Auto-generated, not official warnings.
    """
    alerts: list[str] = []
    tips: list[str] = []

    # 1. Temperature checks
    today_max = (
        current.temp_max_today if current.temp_max_today is not None else current.temperature
    )
    today_min = (
        current.temp_min_today if current.temp_min_today is not None else current.temperature
    )

    if (
        current.temperature >= settings.threshold_heat_temp
        or today_max >= settings.threshold_heat_temp
    ):
        alerts.append(
            f"Extreme Heat Advisory: Highs reaching {today_max:.1f}°C. Stay hydrated and avoid peak afternoon sun."
        )
        tips.append(
            "Carry water, wear breathable light cotton fabrics and UV-protective sunglasses."
        )
    elif (
        current.temperature <= settings.threshold_cold_temp
        or today_min <= settings.threshold_cold_temp
    ):
        alerts.append(
            f"Chilly Weather Advisory: Temperatures dipping to {today_min:.1f}°C. Layer up appropriately."
        )
        tips.append("Wear a warm jacket or thermal inner layers.")

    # 2. Rain & Precipitation
    has_rain_today = current.precipitation > 0 or (
        current.weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]
    )
    today_precip_sum = 0.0
    for d in daily_items:
        if d.kind == "today" and d.precipitation_sum:
            today_precip_sum = d.precipitation_sum
            break

    if today_precip_sum >= settings.threshold_heavy_rain or current.weather_code in [
        65,
        82,
        95,
        96,
        99,
    ]:
        alerts.append(
            "Heavy Rain & Thunderstorm Alert: Significant rainfall expected. Expect waterlogging or travel delays."
        )
        tips.append("Carry a sturdy umbrella, waterproof gear, and drive cautiously.")
    elif has_rain_today or today_precip_sum > 1.0:
        alerts.append("Rain Expected: Showers likely during the day.")
        tips.append("Keep an umbrella or raincoat handy.")

    # 3. Wind & Gusts
    if current.wind_speed >= settings.threshold_strong_gust or (
        current.wind_gusts and current.wind_gusts >= settings.threshold_strong_gust
    ):
        gust_val = current.wind_gusts or current.wind_speed
        alerts.append(
            f"Strong Gusts Alert: Wind gusts reaching up to {gust_val:.1f} km/h. Secure loose outdoor objects."
        )

    # 4. UV Index
    if current.uv_index and current.uv_index >= settings.threshold_high_uv:
        alerts.append(
            f"High UV Alert: Index is {current.uv_index:.1f} ({current.uv_category}). Sun protection required."
        )
        tips.append("Apply SPF 30+ sunscreen, wear a wide-brim hat or use an umbrella.")

    # 5. Air Quality
    if aqi_data and aqi_data.us_aqi and aqi_data.us_aqi >= settings.threshold_poor_aqi:
        alerts.append(
            f"Poor Air Quality Alert: AQI is {aqi_data.us_aqi} ({aqi_data.aqi_category}). Sensitive groups should avoid prolonged outdoor exposure."
        )
        tips.append("Wear an N95 mask outdoors and use an indoor air purifier if available.")

    # Summary narrative
    condition = current.condition_label.lower()
    summary_parts = [f"Currently {current.temperature:.1f}°C and {condition}"]
    if today_max and today_min:
        summary_parts.append(f"with expected range {today_min:.0f}°C to {today_max:.0f}°C")
    summary = ", ".join(summary_parts) + "."

    chosen_tip = (
        tips[0] if tips else "Pleasant conditions ahead. Perfect time for outdoor activities!"
    )

    return SmartInsights(
        alerts=alerts,
        tip=chosen_tip,
        summary=summary,
    )
