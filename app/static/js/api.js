/**
 * SkyPulse Frontend API Client
 * Wraps fetch calls with timing, error extraction, and debug logging.
 */

export class ApiClient {
  constructor() {
    this.debugLogs = [];
    this.cacheHits = 0;
  }

  async fetch(url, options = {}) {
    const start = performance.now();
    try {
      const response = await fetch(url, {
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

        this._recordDebug(url, response.status, elapsed, false);
        const error = new Error(problem.detail || `Request failed with status ${response.status}`);
        error.problem = problem;
        error.status = response.status;
        throw error;
      }

      const data = await response.json();
      const isCached = data?.meta?.cached || false;
      if (isCached) this.cacheHits++;

      this._recordDebug(url, response.status, elapsed, isCached);
      return data;
    } catch (err) {
      if (!err.problem) {
        const elapsed = Math.round(performance.now() - start);
        this._recordDebug(url, 0, elapsed, false);
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

  getWeather(lat, lon, name = null, state = null) {
    const params = new URLSearchParams({
      lat: Number(lat).toFixed(4),
      lon: Number(lon).toFixed(4),
    });
    if (name) params.append("name", name);
    if (state) params.append("state", state);
    return this.fetch(`/api/v1/weather?${params.toString()}`);
  }

  search(query, state = null) {
    const params = new URLSearchParams({ q: query });
    if (state) params.append("state", state);
    return this.fetch(`/api/v1/search?${params.toString()}`);
  }

  reverseGeocode(lat, lon) {
    const params = new URLSearchParams({
      lat: Number(lat).toFixed(4),
      lon: Number(lon).toFixed(4),
    });
    return this.fetch(`/api/v1/reverse?${params.toString()}`);
  }

  locateByIp() {
    return this.fetch(`/api/v1/locate/ip`);
  }

  getStates() {
    return this.fetch(`/api/v1/states`);
  }

  getStateOverview(slug) {
    return this.fetch(`/api/v1/states/${slug}/overview`);
  }

  getCountryOverview() {
    return this.fetch(`/api/v1/overview/country/in`);
  }

  getDebugStats() {
    return this.fetch(`/api/v1/debug`);
  }
}

export const api = new ApiClient();
