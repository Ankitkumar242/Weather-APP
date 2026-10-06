/**
 * SkyPulse UI Renderer
 * Renders glassmorphic cards, hero, tiles, 15-day timeline, state dashboard, and modals.
 * Supports multi-language translation (English & Hindi).
 */

import { UI_ICONS, getWeatherIconSvg } from "../icons/weather-icons.js";
import { render15DayChart, renderHourlyChart, renderStateTrendChart } from "./charts.js";
import { t, tCondition } from "./i18n.js";
import { store } from "./state.js";
import {
  formatDistance,
  formatPrecip,
  formatPressure,
  formatTemp,
  formatWind,
} from "./units.js";

export class UIRenderer {
  constructor() {
    this.container = document.getElementById("app");
  }

  // Update dynamic background attribute based on weather and day/night
  updateBackground(weatherCode, isDay) {
    let bg = isDay ? "clear-day" : "clear-night";

    if (weatherCode >= 1 && weatherCode <= 3) {
      bg = isDay ? "cloudy-day" : "cloudy-night";
    } else if (weatherCode === 45 || weatherCode === 48) {
      bg = "fog";
    } else if ((weatherCode >= 51 && weatherCode <= 67) || (weatherCode >= 80 && weatherCode <= 82)) {
      bg = isDay ? "rain-day" : "rain-night";
    } else if ((weatherCode >= 71 && weatherCode <= 77) || weatherCode === 85 || weatherCode === 86) {
      bg = "snow";
    } else if (weatherCode >= 95) {
      bg = "thunderstorm";
    }

    document.documentElement.setAttribute("data-weather", bg);
  }

  renderStatusBanner(location, meta) {
    if (!location) return "";
    const isStale = meta?.stale || false;
    const isApprox = location.isApproximate || location.source === "ip";

    let badgeHtml = "";
    if (isStale) {
      badgeHtml = `<span class="badge badge-stale">${t("staleBadge")}</span>`;
    } else if (isApprox) {
      badgeHtml = `<span class="badge badge-approx">${t("approxBadge")}</span>`;
    } else {
      badgeHtml = `<span class="badge badge-live"><span class="pulse-badge"></span> ${t("liveBadge")}</span>`;
    }

    return `
      <div class="status-banner" role="region" aria-label="Location status">
        <div class="banner-left">
          <span style="display:flex;align-items:center;gap:4px;color:var(--text-secondary);">
            ${UI_ICONS.mapPin}
            <strong>${location.name}${location.state ? `, ${location.state}` : ""}</strong> (${location.country})
          </span>
          ${badgeHtml}
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <button class="btn-secondary" id="btn-request-location" style="padding:4px 12px;font-size:var(--font-xs);">
            ${UI_ICONS.mapPin} ${t("useMyLocation")}
          </button>
        </div>
      </div>
    `;
  }

  renderHero(data, location) {
    if (!data) return "";
    const { current } = data;
    const units = store.get("units");
    const isFav = store.isFavorite(location.lat, location.lon);

    this.updateBackground(current.weather_code, current.is_day);

    const localTimeStr = current.time ? current.time.replace("T", " ") : "";
    const sunriseStr = current.sunrise ? current.sunrise.split("T")[1] : "–";
    const sunsetStr = current.sunset ? current.sunset.split("T")[1] : "–";
    const conditionTranslated = tCondition(current.condition_label);

    return `
      <section class="glass-card hero-card" aria-label="Current conditions">
        <div class="hero-header">
          <div>
            <h1 class="hero-location-title">${location.name}${location.state ? `, ${location.state}` : ""}</h1>
            <p class="hero-location-sub">${t("localTime")}: ${localTimeStr} • ${location.country}</p>
          </div>
          <button class="btn-icon" id="btn-toggle-favorite" title="Favorite location" aria-label="Toggle favorite">
            ${isFav ? UI_ICONS.starFilled : UI_ICONS.star}
          </button>
        </div>

        <div class="hero-main-content">
          <div class="hero-temp-wrapper">
            <span class="hero-temp-big">${formatTemp(current.temperature, units.temp, false)}</span>
            <span class="hero-temp-unit">°${units.temp}</span>
          </div>

          <div class="hero-condition-col">
            <div class="hero-condition-icon">
              ${getWeatherIconSvg(current.weather_code, current.is_day, 72)}
            </div>
            <span class="hero-condition-label">${conditionTranslated}</span>
            <span class="hero-feels-like">${t("feelsLike")} ${formatTemp(current.apparent_temperature, units.temp)}</span>
          </div>
        </div>

        <div class="hero-stats-row">
          <div class="hero-stat-item">
            <span style="color:var(--temp-hot);font-weight:bold;">↑ ${t("high")}</span>
            <span>${formatTemp(current.temp_max_today, units.temp)}</span>
          </div>
          <div class="hero-stat-item">
            <span style="color:var(--temp-cold);font-weight:bold;">↓ ${t("low")}</span>
            <span>${formatTemp(current.temp_min_today, units.temp)}</span>
          </div>
          <div class="hero-stat-item">
            ${UI_ICONS.sunrise}
            <span>${sunriseStr}</span>
          </div>
          <div class="hero-stat-item">
            ${UI_ICONS.sunset}
            <span>${sunsetStr}</span>
          </div>
        </div>
      </section>
    `;
  }

  renderInsights(insights) {
    if (!insights || (!insights.alerts?.length && !insights.tip)) return "";

    const alertsHtml = insights.alerts
      .map(
        (a) => `
        <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
          <span style="color:#F59E0B;font-size:16px;">⚠️</span>
          <span style="font-size:var(--font-sm);">${a}</span>
        </div>`
      )
      .join("");

    return `
      <section class="glass-card insights-card" aria-label="Weather Insights">
        <div class="insights-header">
          <h2 style="font-size:var(--font-base);font-weight:var(--fw-bold);">${t("advisoryTitle")}</h2>
          <span class="insights-tag">${t("advisoryTag")}</span>
        </div>
        ${alertsHtml}
        ${
          insights.tip
            ? `
          <div class="insights-tip">
            <span>💡 <strong>${t("tipPrefix")}</strong> ${insights.tip}</span>
          </div>`
            : ""
        }
      </section>
    `;
  }

  renderTiles(current, airQuality) {
    if (!current) return "";
    const units = store.get("units");

    // UV color helper
    let uvColor = "var(--uv-low)";
    if (current.uv_index >= 3) uvColor = "var(--uv-moderate)";
    if (current.uv_index >= 6) uvColor = "var(--uv-high)";
    if (current.uv_index >= 8) uvColor = "var(--uv-very-high)";
    if (current.uv_index >= 11) uvColor = "var(--uv-extreme)";

    // AQI color helper
    let aqiColor = "var(--aqi-good)";
    let aqiVal = airQuality?.us_aqi || "–";
    let aqiCat = airQuality?.aqi_category || "Unavailable";
    if (airQuality?.us_aqi) {
      const a = airQuality.us_aqi;
      if (a > 50) aqiColor = "var(--aqi-moderate)";
      if (a > 100) aqiColor = "var(--aqi-sensitive)";
      if (a > 150) aqiColor = "var(--aqi-unhealthy)";
      if (a > 200) aqiColor = "var(--aqi-very-unhealthy)";
      if (a > 300) aqiColor = "var(--aqi-hazardous)";
    }

    return `
      <div class="tiles-grid" aria-label="Detailed conditions">
        <!-- Humidity -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("humidity")}</span>
            <span class="tile-icon">${UI_ICONS.droplet}</span>
          </div>
          <div class="tile-value">${Math.round(current.relative_humidity)}%</div>
          <div class="tile-sub">${t("dewPointSub")}: ${formatTemp(current.dew_point, units.temp)}</div>
        </div>

        <!-- Wind -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("wind")}</span>
            <span class="tile-icon">${UI_ICONS.wind}</span>
          </div>
          <div class="tile-value">${formatWind(current.wind_speed, units.wind)}</div>
          <div class="tile-sub">
            <span style="display:inline-block;transform:rotate(${current.wind_direction}deg);">↑</span>
            ${t("gustsSub")}: ${formatWind(current.wind_gusts || current.wind_speed, units.wind)}
          </div>
        </div>

        <!-- Air Quality -->
        <div class="glass-card tile-card" style="border-left:4px solid ${aqiColor};">
          <div class="tile-header">
            <span>${t("airQuality")}</span>
            <span class="tile-icon" style="color:${aqiColor};">●</span>
          </div>
          <div class="tile-value" style="color:${aqiColor};">${aqiVal}</div>
          <div class="tile-sub">${aqiCat} ${airQuality?.pm2_5 ? `• PM2.5: ${airQuality.pm2_5}` : ""}</div>
        </div>

        <!-- UV Index -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("uvIndex")}</span>
            <span class="tile-icon">${UI_ICONS.sunRays}</span>
          </div>
          <div class="tile-value" style="color:${uvColor};">${current.uv_index !== null ? current.uv_index.toFixed(1) : "–"}</div>
          <div class="tile-sub">${current.uv_category || "Low"} risk</div>
        </div>

        <!-- Rain / Precip -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("precipitation")}</span>
            <span class="tile-icon">${UI_ICONS.droplet}</span>
          </div>
          <div class="tile-value">${formatPrecip(current.precipitation, units.precip)}</div>
          <div class="tile-sub">${t("cloudCover")}: ${Math.round(current.cloud_cover)}%</div>
        </div>

        <!-- Pressure -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("pressure")}</span>
            <span class="tile-icon">${UI_ICONS.gauge}</span>
          </div>
          <div class="tile-value">${formatPressure(current.pressure, units.pressure)}</div>
          <div class="tile-sub">${t("mslPressure")}</div>
        </div>

        <!-- Visibility -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("visibility")}</span>
            <span class="tile-icon">${UI_ICONS.eye}</span>
          </div>
          <div class="tile-value">${formatDistance(current.visibility)}</div>
          <div class="tile-sub">${current.visibility && current.visibility > 9000 ? t("clearHorizon") : t("hazy")}</div>
        </div>

        <!-- Cloud Cover -->
        <div class="glass-card tile-card">
          <div class="tile-header">
            <span>${t("cloudCover")}</span>
            <span class="tile-icon">${UI_ICONS.sunRays}</span>
          </div>
          <div class="tile-value">${Math.round(current.cloud_cover)}%</div>
          <div class="tile-sub">${current.cloud_cover < 20 ? "Clear" : current.cloud_cover < 70 ? "Partly cloudy" : "Overcast"}</div>
        </div>
      </div>
    `;
  }

  renderHourly(hourlyItems) {
    if (!hourlyItems || !hourlyItems.length) return "";
    const units = store.get("units");

    const cardsHtml = hourlyItems
      .slice(0, 24)
      .map((h) => {
        const timePart = h.time.split("T")[1]?.slice(0, 5) || "";
        return `
        <div style="flex:0 0 76px;text-align:center;padding:8px 4px;background:rgba(255,255,255,0.25);border-radius:var(--radius-md);scroll-snap-align:start;">
          <div style="font-size:var(--font-xs);color:var(--text-muted);">${timePart}</div>
          <div style="margin:4px 0;">${getWeatherIconSvg(h.weather_code, h.is_day !== undefined ? h.is_day : 1, 32)}</div>
          <div style="font-weight:bold;font-size:var(--font-sm);">${formatTemp(h.temperature, units.temp)}</div>
          <div style="font-size:10px;color:#0284C7;">${h.precipitation_probability ? `${h.precipitation_probability}%` : "–"}</div>
        </div>`;
      })
      .join("");

    return `
      <section class="glass-card" style="margin-bottom:var(--space-6);" aria-label="Hourly 48-Hour Forecast">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-3);">
          <h2 style="font-size:var(--font-lg);font-weight:var(--fw-bold);">${t("hourlyTitle")}</h2>
          <span style="font-size:var(--font-xs);color:var(--text-muted);">${t("hourlySub")}</span>
        </div>

        <div class="chart-container" style="height:220px;">
          <canvas id="chart-hourly"></canvas>
        </div>

        <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x mandatory;margin-top:12px;">
          ${cardsHtml}
        </div>
      </section>
    `;
  }

  render15DayTimeline(dailyItems) {
    if (!dailyItems || !dailyItems.length) return "";
    const units = store.get("units");
    const activeSegment = store.get("timelineSegment") || "all";
    const activeView = store.get("timelineView") || "cards";

    // Filter items based on segment
    let filtered = dailyItems;
    if (activeSegment === "past") filtered = dailyItems.filter((d) => d.kind === "past");
    else if (activeSegment === "forecast") filtered = dailyItems.filter((d) => d.kind === "forecast");

    // Summary statistics calculation
    const past7 = dailyItems.filter((d) => d.kind === "past");
    const next7 = dailyItems.filter((d) => d.kind === "forecast");

    const pastAvgMax = past7.length ? (past7.reduce((acc, d) => acc + d.temp_max, 0) / past7.length).toFixed(1) : "–";
    const pastTotalRain = past7.reduce((acc, d) => acc + (d.precipitation_sum || 0), 0).toFixed(1);
    const pastHottest = past7.length ? Math.max(...past7.map((d) => d.temp_max)).toFixed(1) : "–";
    const pastColdest = past7.length ? Math.min(...past7.map((d) => d.temp_min)).toFixed(1) : "–";

    const nextRainyDays = next7.filter((d) => (d.precipitation_probability_max || 0) > 40 || (d.precipitation_sum || 0) > 1.0).length;
    const nextPeakTemp = next7.length ? Math.max(...next7.map((d) => d.temp_max)).toFixed(1) : "–";

    let bestDay = "–";
    const candidates = next7.filter((d) => d.temp_max >= 20 && d.temp_max <= 32 && (d.precipitation_probability_max || 0) < 25);
    if (candidates.length) {
      bestDay = candidates[0].date;
    } else if (next7.length) {
      bestDay = next7[0].date;
    }

    // Cards view HTML
    const cardsHtml = filtered
      .map((d) => {
        const parts = d.date.split("-");
        const formattedDate = `${parts[2]}/${parts[1]}`;
        const dayClass = d.kind === "today" ? "today" : "";
        const labelText = d.kind === "past" ? t("past") : d.kind === "today" ? t("today") : t("forecast");

        return `
        <div class="glass-card day-card ${dayClass}" role="button" tabindex="0" aria-label="${d.date} ${d.kind} weather">
          <span class="day-card-label ${d.kind}">${labelText}</span>
          <span class="day-card-date">${formattedDate}</span>
          <div class="day-card-icon">
            ${getWeatherIconSvg(d.weather_code, 1, 40)}
          </div>
          <div class="day-card-temps">
            <span class="day-card-max">${formatTemp(d.temp_max, units.temp, false)}°</span>
            <span class="day-card-min">${formatTemp(d.temp_min, units.temp, false)}°</span>
          </div>
          <div style="font-size:10px;color:#0284C7;margin-top:4px;">
            💧 ${d.precipitation_sum ? `${d.precipitation_sum.toFixed(1)}mm` : "0mm"}
          </div>
        </div>`;
      })
      .join("");

    // Table view HTML
    const tableRows = filtered
      .map((d) => {
        const labelText = d.kind === "past" ? t("past") : d.kind === "today" ? t("today") : t("forecast");
        const condTranslated = tCondition(d.condition_label);
        return `
        <tr>
          <td><span class="day-card-label ${d.kind}">${labelText}</span></td>
          <td><strong>${d.date}</strong></td>
          <td style="display:flex;align-items:center;gap:6px;">
            ${getWeatherIconSvg(d.weather_code, 1, 24)}
            ${condTranslated}
          </td>
          <td><strong style="color:var(--temp-hot);">${formatTemp(d.temp_max, units.temp)}</strong></td>
          <td><span style="color:var(--temp-cold);">${formatTemp(d.temp_min, units.temp)}</span></td>
          <td>${d.precipitation_sum ? `${d.precipitation_sum.toFixed(1)} mm` : "–"}</td>
          <td>${d.precipitation_probability_max !== null ? `${d.precipitation_probability_max}%` : "–"}</td>
          <td>${formatWind(d.wind_speed_max, units.wind)}</td>
        </tr>
      `;
      })
      .join("");

    return `
      <section class="timeline-section" aria-label="15-Day Historical and Forecast Timeline">
        <div class="glass-card">
          <div class="timeline-header">
            <div>
              <h2 style="font-size:var(--font-xl);font-weight:var(--fw-bold);">${t("timelineTitle")}</h2>
              <p style="font-size:var(--font-xs);color:var(--text-muted);">${t("timelineSub")}</p>
            </div>

            <!-- Segmented Control -->
            <div class="timeline-actions">
              <div class="segmented-control" role="tablist">
                <button class="segmented-btn ${activeSegment === "past" ? "active" : ""}" data-segment="past">${t("past7Days")}</button>
                <button class="segmented-btn ${activeSegment === "all" ? "active" : ""}" data-segment="all">${t("all15Days")}</button>
                <button class="segmented-btn ${activeSegment === "forecast" ? "active" : ""}" data-segment="forecast">${t("next7Days")}</button>
              </div>

              <!-- View toggle -->
              <div class="segmented-control">
                <button class="segmented-btn ${activeView === "cards" ? "active" : ""}" data-view="cards">${t("cards")}</button>
                <button class="segmented-btn ${activeView === "table" ? "active" : ""}" data-view="table">${t("table")}</button>
              </div>
            </div>
          </div>

          <!-- Chart container -->
          <div class="chart-container">
            <canvas id="chart-15day"></canvas>
          </div>

          <!-- Cards strip or Table -->
          ${
            activeView === "cards"
              ? `<div class="timeline-strip" style="margin-top:16px;">${cardsHtml}</div>`
              : `
              <div class="data-table-wrapper">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>${t("period")}</th>
                      <th>${t("date")}</th>
                      <th>${t("condition")}</th>
                      <th>${t("max")}</th>
                      <th>${t("min")}</th>
                      <th>${t("rain")}</th>
                      <th>${t("rainChance")}</th>
                      <th>${t("maxWind")}</th>
                    </tr>
                  </thead>
                  <tbody>${tableRows}</tbody>
                </table>
              </div>`
          }

          <!-- Summary Stats -->
          <div class="summary-stats-grid">
            <div class="stat-box">
              <div style="font-size:var(--font-xs);color:var(--text-muted);font-weight:bold;text-transform:uppercase;">
                ${t("past7Summary")}
              </div>
              <div style="margin-top:6px;font-size:var(--font-sm);">
                <div>${t("avgHigh")}: <strong>${pastAvgMax}°C</strong></div>
                <div>${t("totalRain")}: <strong>${pastTotalRain} mm</strong></div>
                <div>${t("hottest")} / ${t("coldest")}: <strong>${pastHottest}°C / ${pastColdest}°C</strong></div>
              </div>
            </div>

            <div class="stat-box">
              <div style="font-size:var(--font-xs);color:var(--text-muted);font-weight:bold;text-transform:uppercase;">
                ${t("next7Summary")}
              </div>
              <div style="margin-top:6px;font-size:var(--font-sm);">
                <div>${t("rainyDays")}: <strong>${nextRainyDays}</strong></div>
                <div>${t("peakHigh")}: <strong>${nextPeakTemp}°C</strong></div>
                <div>${t("bestOutdoors")}: <strong>${bestDay}</strong></div>
              </div>
            </div>
          </div>

          <p style="font-size:11px;color:var(--text-muted);margin-top:12px;font-style:italic;">
            ${t("footnote")}
          </p>
        </div>
      </section>
    `;
  }

  renderStateDashboard(statesList, stateOverview, countryOverview, activeSlug, sortOrder = "capital") {
    const units = store.get("units");

    // Options for State dropdown
    const stateOptions = statesList
      .map(
        (s) => `
        <option value="${s.slug}" ${s.slug === activeSlug ? "selected" : ""}>
          ${s.name} (${s.type.toUpperCase()})
        </option>`
      )
      .join("");

    let citiesCardsHtml = "";
    if (stateOverview?.cities_weather) {
      let sortedCities = [...stateOverview.cities_weather];
      if (sortOrder === "hottest") sortedCities.sort((a, b) => b.current_temp - a.current_temp);
      else if (sortOrder === "coldest") sortedCities.sort((a, b) => a.current_temp - b.current_temp);
      else if (sortOrder === "rainiest")
        sortedCities.sort((a, b) => (b.precipitation_probability || 0) - (a.precipitation_probability || 0));
      else if (sortOrder === "az") sortedCities.sort((a, b) => a.name.localeCompare(b.name));

      citiesCardsHtml = sortedCities
        .map(
          (c) => `
        <div class="glass-card city-card" data-lat="${c.lat}" data-lon="${c.lon}" data-name="${c.name}" role="button" tabindex="0">
          <div class="city-card-header">
            <span class="city-card-title">${c.name}</span>
            ${c.is_capital ? `<span class="capital-badge">${t("capitalBadge")}</span>` : ""}
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin:8px 0;">
            <div style="font-size:var(--font-3xl);font-weight:bold;">
              ${formatTemp(c.current_temp, units.temp)}
            </div>
            <div>${getWeatherIconSvg(c.weather_code, 1, 40)}</div>
          </div>
          <div style="font-size:var(--font-xs);color:var(--text-secondary);display:flex;justify-content:space-between;">
            <span>${tCondition(c.condition_label)}</span>
            <span>H: ${formatTemp(c.temp_max, units.temp, false)}° • L: ${formatTemp(c.temp_min, units.temp, false)}°</span>
          </div>
          <div style="font-size:11px;color:#0284C7;margin-top:4px;">
            ${t("rainChance")}: ${c.precipitation_probability !== null ? `${c.precipitation_probability}%` : "–"}
          </div>
        </div>`
        )
        .join("");
    }

    // Country Overview Highlights
    let countryHighlightsHtml = "";
    if (countryOverview) {
      countryHighlightsHtml = `
        <div class="summary-stats-grid" style="margin-bottom:16px;">
          <div class="stat-box" style="border-left:4px solid var(--temp-hot);">
            <div style="font-size:11px;color:var(--text-muted);font-weight:bold;">${t("hottestCapital")}</div>
            <div style="font-size:var(--font-lg);font-weight:bold;margin-top:2px;">
              ${countryOverview.hottest?.name || "–"}: ${formatTemp(countryOverview.hottest?.current_temp, units.temp)}
            </div>
          </div>
          <div class="stat-box" style="border-left:4px solid var(--temp-cold);">
            <div style="font-size:11px;color:var(--text-muted);font-weight:bold;">${t("coldestCapital")}</div>
            <div style="font-size:var(--font-lg);font-weight:bold;margin-top:2px;">
              ${countryOverview.coldest?.name || "–"}: ${formatTemp(countryOverview.coldest?.current_temp, units.temp)}
            </div>
          </div>
          <div class="stat-box" style="border-left:4px solid var(--accent-primary);">
            <div style="font-size:11px;color:var(--text-muted);font-weight:bold;">${t("rainiestCapital")}</div>
            <div style="font-size:var(--font-lg);font-weight:bold;margin-top:2px;">
              ${countryOverview.wettest?.name || "–"}: ${countryOverview.wettest?.precipitation_probability || 0}% ${t("rainChance")}
            </div>
          </div>
        </div>
      `;
    }

    return `
      <section class="state-section" aria-label="State-Wise Weather Dashboard">
        <div class="glass-card" style="margin-bottom:var(--space-4);">
          <div class="state-controls">
            <div>
              <h2 style="font-size:var(--font-xl);font-weight:var(--fw-bold);">${t("stateTitle")}</h2>
              <p style="font-size:var(--font-xs);color:var(--text-muted);">${t("stateSub")}</p>
            </div>

            <div class="state-controls-actions">
              <select id="select-state" class="select-control" aria-label="Select state">
                <option value="">${t("chooseState")}</option>
                ${stateOptions}
              </select>

              <select id="select-city-sort" class="select-control" aria-label="Sort cities">
                <option value="capital" ${sortOrder === "capital" ? "selected" : ""}>${t("capitalFirst")}</option>
                <option value="hottest" ${sortOrder === "hottest" ? "selected" : ""}>${t("hottest")}</option>
                <option value="coldest" ${sortOrder === "coldest" ? "selected" : ""}>${t("coldest")}</option>
                <option value="rainiest" ${sortOrder === "rainiest" ? "selected" : ""}>${t("rainiest")}</option>
                <option value="az" ${sortOrder === "az" ? "selected" : ""}>${t("az")}</option>
              </select>

              <button class="btn-secondary" id="btn-show-all-india" style="padding:6px 14px;font-size:var(--font-xs);">
                ${t("allIndiaBtn")}
              </button>
            </div>
          </div>

          ${countryHighlightsHtml}

          <!-- City cards loaded in one batched call -->
          <div class="city-cards-grid" id="state-cities-grid">
            ${citiesCardsHtml || `<div style="padding:24px;color:var(--text-muted);text-align:center;">${t("selectStatePrompt")}</div>`}
          </div>

          <!-- State trend chart -->
          ${
            stateOverview?.trend?.length
              ? `
            <div style="margin-top:24px;border-top:1px solid var(--glass-border);padding-top:16px;">
              <h3 style="font-size:var(--font-base);font-weight:bold;margin-bottom:8px;">
                ${stateOverview.state.name} ${t("stateTrendTitle")}
              </h3>
              <div class="chart-container" style="height:220px;">
                <canvas id="chart-state-trend"></canvas>
              </div>
            </div>`
              : ""
          }
        </div>
      </section>
    `;
  }
}

export const ui = new UIRenderer();
