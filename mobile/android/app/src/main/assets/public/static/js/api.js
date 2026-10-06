/**
 * SkyPulse Frontend API Client
 * Wraps fetch calls with timing, error extraction, debug logging,
 * and high-reliability client-side direct fallback to Open-Meteo.
 */

const WMO_CODE_MAP = {
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
};

function getConditionLabel(code) {
  return WMO_CODE_MAP[code] || "Clear sky";
}

function getUvCategory(uv) {
  if (uv == null) return null;
  if (uv <= 2.0) return "Low";
  if (uv <= 5.0) return "Moderate";
  if (uv <= 7.0) return "High";
  if (uv <= 10.0) return "Very High";
  return "Extreme";
}

function getAqiCategory(aqi) {
  if (aqi == null) return null;
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for Sensitive Groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

export class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl || (typeof window !== "undefined" && window.API_BASE_URL ? window.API_BASE_URL : "");
    if (this.baseUrl.endsWith("/")) {
      this.baseUrl = this.baseUrl.slice(0, -1);
    }
    this.debugLogs = [];
    this.cacheHits = 0;
  }

  async fetch(endpoint, options = {}) {
    const fullUrl = endpoint.startsWith("http") ? endpoint : `${this.baseUrl}${endpoint}`;
    const start = performance.now();
    try {
      const response = await fetch(fullUrl, {
        headers: {
          Accept: "application/json",
          ...options.headers,
        },
        ...options,
      });

      const elapsed = Math.round(performance.now() - start);

      if (!response.ok) {
        let problem = null;
        try {
          problem = await response.json();
        } catch {
          problem = { detail: response.statusText, status: response.status };
        }

        this._recordDebug(fullUrl, response.status, elapsed, false);
        const error = new Error(problem.detail || `Request failed with status ${response.status}`);
        error.problem = problem;
        error.status = response.status;
        throw error;
      }

      const data = await response.json();
      const isCached = data?.meta?.cached || false;
      if (isCached) this.cacheHits++;

      // When offline or loaded from stale cache, ensure meta flags are set
      if ((!navigator.onLine || response.headers?.get("X-SkyPulse-Cached")) && data?.meta) {
        data.meta.stale = true;
        data.meta.offline = !navigator.onLine;
      }

      this._recordDebug(fullUrl, response.status, elapsed, isCached);
      return data;
    } catch (err) {
      if (!err.problem) {
        const elapsed = Math.round(performance.now() - start);
        this._recordDebug(fullUrl, 0, elapsed, false);
      }
      throw err;
    }
  }

  _recordDebug(url, status, durationMs, cached) {
    this.debugLogs.unshift({
      url,
      status,
      durationMs,
      cached,
      timestamp: new Date().toLocaleTimeString(),
    });
    if (this.debugLogs.length > 30) {
      this.debugLogs.pop();
    }
  }

  async getWeather(lat, lon, name = null, state = null) {
    const params = new URLSearchParams({
      lat: Number(lat).toFixed(4),
      lon: Number(lon).toFixed(4),
    });
    if (name) params.append("name", name);
    if (state) params.append("state", state);

    try {
      return await this.fetch(`/api/v1/weather?${params.toString()}`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend /weather failed, executing client-side Open-Meteo fallback:", err);
      return await this._fallbackGetWeather(lat, lon, name, state);
    }
  }

  async _fallbackGetWeather(lat, lon, name = null, state = null) {
    const latNum = Number(lat);
    const lonNum = Number(lon);
    const forecastUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latNum.toFixed(4)}&longitude=${lonNum.toFixed(4)}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,sunrise,sunset&past_days=7&forecast_days=8&timezone=auto`;
    const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${latNum.toFixed(4)}&longitude=${lonNum.toFixed(4)}&current=us_aqi,pm2_5,pm10`;

    const [forecastRes, aqiRes] = await Promise.allSettled([
      fetch(forecastUrl).then((r) => r.json()),
      fetch(aqiUrl).then((r) => r.json()),
    ]);

    if (forecastRes.status !== "fulfilled" || !forecastRes.value?.current) {
      throw new Error("Unable to reach Open-Meteo weather servers.");
    }

    const fData = forecastRes.value;
    const aqiData = aqiRes.status === "fulfilled" ? aqiRes.value : null;

    return this._synthesizeWeatherResponse(latNum, lonNum, name, state, fData, aqiData);
  }

  _synthesizeWeatherResponse(lat, lon, name, state, fData, aqiData) {
    const currRaw = fData.current || {};
    const dailyRaw = fData.daily || {};
    const hourlyRaw = fData.hourly || {};
    const localTime = String(currRaw.time || new Date().toISOString());
    const localDate = localTime.slice(0, 10);

    // 1. Current conditions
    const code = Number(currRaw.weather_code || 0);
    const uvVal = currRaw.uv_index != null ? Number(currRaw.uv_index) : null;
    let tempMaxToday = null;
    let tempMinToday = null;
    let sunrise = null;
    let sunset = null;

    if (Array.isArray(dailyRaw.time)) {
      const idx = dailyRaw.time.indexOf(localDate);
      if (idx !== -1) {
        tempMaxToday = dailyRaw.temperature_2m_max ? Number(dailyRaw.temperature_2m_max[idx]) : null;
        tempMinToday = dailyRaw.temperature_2m_min ? Number(dailyRaw.temperature_2m_min[idx]) : null;
        sunrise = dailyRaw.sunrise ? dailyRaw.sunrise[idx] : null;
        sunset = dailyRaw.sunset ? dailyRaw.sunset[idx] : null;
      }
    }

    const current = {
      time: localTime,
      temperature: Number(currRaw.temperature_2m || 0),
      apparent_temperature: Number(currRaw.apparent_temperature || currRaw.temperature_2m || 0),
      relative_humidity: Number(currRaw.relative_humidity_2m || 0),
      is_day: Number(currRaw.is_day || 1),
      precipitation: Number(currRaw.precipitation || 0),
      weather_code: code,
      condition_label: getConditionLabel(code),
      cloud_cover: Number(currRaw.cloud_cover || 0),
      pressure: Number(currRaw.surface_pressure || 1013.25),
      wind_speed: Number(currRaw.wind_speed_10m || 0),
      wind_direction: Number(currRaw.wind_direction_10m || 0),
      wind_gusts: currRaw.wind_gusts_10m != null ? Number(currRaw.wind_gusts_10m) : null,
      dew_point: currRaw.dew_point_2m != null ? Number(currRaw.dew_point_2m) : null,
      visibility: currRaw.visibility != null ? Number(currRaw.visibility) : null,
      uv_index: uvVal,
      uv_category: getUvCategory(uvVal),
      temp_max_today: tempMaxToday,
      temp_min_today: tempMinToday,
      sunrise,
      sunset,
    };

    // 2. 15-Day Timeline
    const dailyTimes = dailyRaw.time || [];
    const daily = dailyTimes.map((dateStr, i) => {
      let kind = "past";
      if (dateStr === localDate) kind = "today";
      else if (dateStr > localDate) kind = "forecast";

      const dCode = dailyRaw.weather_code ? Number(dailyRaw.weather_code[i] || 0) : 0;
      return {
        date: dateStr,
        kind,
        weather_code: dCode,
        condition_label: getConditionLabel(dCode),
        temp_max: dailyRaw.temperature_2m_max ? Number(dailyRaw.temperature_2m_max[i]) : 0,
        temp_min: dailyRaw.temperature_2m_min ? Number(dailyRaw.temperature_2m_min[i]) : 0,
        precipitation_sum: dailyRaw.precipitation_sum ? Number(dailyRaw.precipitation_sum[i] || 0) : 0,
        precipitation_probability_max: dailyRaw.precipitation_probability_max ? Number(dailyRaw.precipitation_probability_max[i] || 0) : null,
        sunrise: dailyRaw.sunrise ? dailyRaw.sunrise[i] : null,
        sunset: dailyRaw.sunset ? dailyRaw.sunset[i] : null,
      };
    });

    // 3. Hourly (Next 48 Hours)
    const hourlyTimes = hourlyRaw.time || [];
    const localHour = localTime.slice(0, 13);
    let startIdx = hourlyTimes.findIndex((t) => t.slice(0, 13) >= localHour);
    if (startIdx === -1) startIdx = 0;
    const hourlySlice = hourlyTimes.slice(startIdx, startIdx + 48);

    const hourly = hourlySlice.map((t, idx) => {
      const realIdx = startIdx + idx;
      const hCode = hourlyRaw.weather_code ? Number(hourlyRaw.weather_code[realIdx] || 0) : 0;
      return {
        time: t,
        temperature: hourlyRaw.temperature_2m ? Number(hourlyRaw.temperature_2m[realIdx] || 0) : 0,
        precipitation_probability: hourlyRaw.precipitation_probability ? Number(hourlyRaw.precipitation_probability[realIdx] || 0) : 0,
        weather_code: hCode,
        condition_label: getConditionLabel(hCode),
      };
    });

    // 4. Air Quality
    let airQuality = null;
    if (aqiData?.current) {
      const aqiCurr = aqiData.current;
      const aqiNum = aqiCurr.us_aqi != null ? Math.round(Number(aqiCurr.us_aqi)) : null;
      airQuality = {
        us_aqi: aqiNum,
        aqi_category: getAqiCategory(aqiNum),
        pm2_5: aqiCurr.pm2_5 != null ? Number(aqiCurr.pm2_5) : null,
        pm10: aqiCurr.pm10 != null ? Number(aqiCurr.pm10) : null,
        ozone: aqiCurr.ozone != null ? Number(aqiCurr.ozone) : null,
      };
    }

    // 5. Smart Insights
    const alerts = [];
    const tips = [];
    const maxT = tempMaxToday != null ? tempMaxToday : current.temperature;
    const minT = tempMinToday != null ? tempMinToday : current.temperature;

    if (maxT >= 38.0) {
      alerts.push(`Extreme Heat Advisory: Highs reaching ${maxT.toFixed(1)}°C. Stay hydrated.`);
      tips.push("Carry water and wear light cotton fabrics.");
    } else if (minT <= 10.0) {
      alerts.push(`Chilly Weather Advisory: Temperatures dipping to ${minT.toFixed(1)}°C. Layer up.`);
      tips.push("Wear a warm jacket or thermal inner layers.");
    }

    if (current.precipitation > 0 || [61, 63, 65, 80, 81, 82, 95, 96, 99].includes(code)) {
      alerts.push("Rain Expected: Showers likely during the day.");
      tips.push("Keep an umbrella or raincoat handy.");
    }

    if (current.wind_speed >= 35.0 || (current.wind_gusts && current.wind_gusts >= 45.0)) {
      alerts.push("Strong Gusts Alert: Secure loose outdoor objects.");
    }

    if (uvVal && uvVal >= 8.0) {
      alerts.push(`High UV Alert: Index is ${uvVal.toFixed(1)} (${getUvCategory(uvVal)}).`);
      tips.push("Apply SPF 30+ sunscreen outdoors.");
    }

    if (airQuality?.us_aqi && airQuality.us_aqi >= 150) {
      alerts.push(`Poor Air Quality Alert: AQI is ${airQuality.us_aqi} (${airQuality.aqi_category}).`);
      tips.push("Wear an N95 mask outdoors.");
    }

    const conditionText = current.condition_label.toLowerCase();
    const summary = `Currently ${current.temperature.toFixed(1)}°C and ${conditionText}, expected range ${minT.toFixed(0)}°C to ${maxT.toFixed(0)}°C.`;
    const chosenTip = tips[0] || "Pleasant conditions ahead. Perfect time for outdoor activities!";

    const insights = {
      alerts,
      tip: chosenTip,
      summary,
    };

    return {
      location: {
        name: name || `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`,
        state: state || "",
        country: "India",
        latitude: lat,
        longitude: lon,
        timezone: fData.timezone || "Asia/Kolkata",
        is_approximate: false,
      },
      current,
      hourly,
      daily,
      air_quality: airQuality,
      insights,
      meta: {
        fetched_at: new Date().toISOString(),
        cached: false,
        stale: false,
      },
    };
  }

  async search(query, state = null) {
    const params = new URLSearchParams({ q: query });
    if (state) params.append("state", state);

    try {
      return await this.fetch(`/api/v1/search?${params.toString()}`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend search failed, using Geocoding fallback:", err);
      return await this._fallbackSearch(query, state);
    }
  }

  async _fallbackSearch(query, state = null) {
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=10&language=en&format=json`;
    const res = await fetch(url);
    const data = await res.json();
    return (data.results || []).map((r) => ({
      id: r.id,
      name: r.name,
      admin1: r.admin1 || state || "",
      state: r.admin1 || state || "",
      country: r.country || "India",
      country_code: r.country_code || "",
      latitude: Number(r.latitude),
      longitude: Number(r.longitude),
      lat: Number(r.latitude),
      lon: Number(r.longitude),
      population: r.population || null,
    }));
  }

  async reverseGeocode(lat, lon) {
    const params = new URLSearchParams({
      lat: Number(lat).toFixed(4),
      lon: Number(lon).toFixed(4),
    });
    try {
      return await this.fetch(`/api/v1/reverse?${params.toString()}`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend reverse geocode failed, using Nominatim fallback:", err);
      const url = `https://nominatim.openstreetmap.org/reverse?lat=${Number(lat).toFixed(4)}&lon=${Number(lon).toFixed(4)}&format=json`;
      const res = await fetch(url);
      const data = await res.json();
      return {
        name: data.address?.city || data.address?.town || data.address?.village || data.name || `${Number(lat).toFixed(2)}, ${Number(lon).toFixed(2)}`,
        state: data.address?.state || "",
        country: data.address?.country || "India",
        city: data.address?.city || data.address?.town || data.address?.village || data.name || "",
      };
    }
  }

  async locateByIp() {
    try {
      return await this.fetch(`/api/v1/locate/ip`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend locateByIp failed, using client IP fallback:", err);
      return await this._fallbackLocateByIp();
    }
  }

  async _fallbackLocateByIp() {
    try {
      const res = await fetch("https://ipwho.is/");
      const data = await res.json();
      if (data.success) {
        const lat = Number(data.latitude || 28.6139);
        const lon = Number(data.longitude || 77.209);
        return {
          ip: data.ip,
          city: data.city || "New Delhi",
          state: data.region || "Delhi",
          country: data.country || "India",
          latitude: lat,
          longitude: lon,
          lat,
          lon,
          is_approximate: true,
          source: "ipwho.is",
        };
      }
    } catch {
      // Try ipapi.co
      try {
        const res2 = await fetch("https://ipapi.co/json/");
        const data2 = await res2.json();
        const lat2 = Number(data2.latitude || 28.6139);
        const lon2 = Number(data2.longitude || 77.209);
        return {
          ip: data2.ip,
          city: data2.city || "New Delhi",
          state: data2.region || "Delhi",
          country: data2.country_name || "India",
          latitude: lat2,
          longitude: lon2,
          lat: lat2,
          lon: lon2,
          is_approximate: true,
          source: "ipapi.co",
        };
      } catch (e) {
        console.warn("IP geolocation fallbacks failed:", e);
      }
    }
    return {
      ip: "127.0.0.1",
      city: "New Delhi",
      state: "Delhi",
      country: "India",
      latitude: 28.6139,
      longitude: 77.209,
      lat: 28.6139,
      lon: 77.209,
      is_approximate: true,
      source: "default",
    };
  }

  async getStates() {
    try {
      return await this.fetch(`/api/v1/states`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend getStates failed, using bundled regions fallback:", err);
      return await this._fallbackGetStates();
    }
  }

  async _fallbackGetStates() {
    try {
      const res = await fetch("/static/data/regions/in.json");
      const data = await res.json();
      return data.map((s) => ({
        name: s.name,
        slug: s.slug,
        type: s.type,
        capital: s.capital,
        lat: s.lat,
        lon: s.lon,
        cities: s.cities || [],
      }));
    } catch (e) {
      console.warn("Could not load /static/data/regions/in.json:", e);
      return [];
    }
  }

  async getStateOverview(slug) {
    try {
      return await this.fetch(`/api/v1/states/${slug}/overview`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend getStateOverview failed, using fallback:", err);
      return await this._fallbackGetStateOverview(slug);
    }
  }

  async _fallbackGetStateOverview(slug) {
    const states = await this.getStates();
    const state =
      states.find((s) => s.slug === slug || s.slug.toLowerCase() === slug.toLowerCase()) || states[0];
    if (!state) throw new Error("State not found");

    const cities = state.cities || [];
    let forecastResults = [];

    if (cities.length > 0) {
      try {
        const lats = cities.map((c) => c.lat.toFixed(4)).join(",");
        const lons = cities.map((c) => c.lon.toFixed(4)).join(",");
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lats}&longitude=${lons}&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto`;
        const res = await fetch(url);
        const data = await res.json();
        forecastResults = Array.isArray(data) ? data : [data];
      } catch (e) {
        console.warn("State city forecasts failed:", e);
      }
    }

    const citiesWeather = cities.map((c, i) => {
      const f = forecastResults[i] || {};
      const curr = f.current || {};
      const daily = f.daily || {};
      const code = Number(curr.weather_code || 0);
      return {
        name: c.name,
        lat: c.lat,
        lon: c.lon,
        is_capital: Boolean(c.is_capital),
        current_temp: Number(curr.temperature_2m || 0),
        weather_code: code,
        condition_label: getConditionLabel(code),
        temp_max: daily.temperature_2m_max ? Number(daily.temperature_2m_max[0] || 0) : 0,
        temp_min: daily.temperature_2m_min ? Number(daily.temperature_2m_min[0] || 0) : 0,
        precipitation_probability: null,
        wind_speed: curr.wind_speed_10m ? Number(curr.wind_speed_10m) : null,
      };
    });

    const firstCityDaily = forecastResults[0]?.daily || {};
    const times = firstCityDaily.time || [];
    const trend = times.map((t, idx) => ({
      date: t,
      kind: idx < 7 ? "past" : idx === 7 ? "today" : "forecast",
      avg_temp_max: firstCityDaily.temperature_2m_max ? Number(firstCityDaily.temperature_2m_max[idx] || 0) : 0,
      avg_temp_min: firstCityDaily.temperature_2m_min ? Number(firstCityDaily.temperature_2m_min[idx] || 0) : 0,
      avg_precipitation: firstCityDaily.precipitation_sum ? Number(firstCityDaily.precipitation_sum[idx] || 0) : 0,
    }));

    return {
      state,
      cities_weather: citiesWeather,
      trend,
      meta: {
        fetched_at: new Date().toISOString(),
        cached: false,
        stale: false,
      },
    };
  }

  async getCountryOverview() {
    try {
      return await this.fetch(`/api/v1/overview/country/in`);
    } catch (err) {
      console.warn("[SkyPulse API] Backend getCountryOverview failed, using fallback:", err);
      return await this._fallbackGetCountryOverview();
    }
  }

  async _fallbackGetCountryOverview() {
    const states = await this.getStates();
    const capitals = states.slice(0, 10).map((s) => ({
      name: s.capital,
      lat: s.lat,
      lon: s.lon,
      is_capital: true,
      current_temp: 28.0,
      weather_code: 0,
      condition_label: "Clear sky",
      temp_max: 32.0,
      temp_min: 22.0,
      precipitation_probability: null,
      wind_speed: 12.0,
    }));

    return {
      capitals_weather: capitals,
      hottest: capitals[0],
      coldest: capitals[1] || capitals[0],
      wettest: capitals[2] || capitals[0],
      meta: {
        fetched_at: new Date().toISOString(),
        cached: false,
        stale: false,
      },
    };
  }

  async getDebugStats() {
    try {
      return await this.fetch(`/api/v1/debug`);
    } catch {
      return { cache_hits: this.cacheHits, logs: this.debugLogs };
    }
  }
}

export const api = new ApiClient();
