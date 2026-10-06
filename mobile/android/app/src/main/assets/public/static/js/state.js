/**
 * SkyPulse State Store
 * Reactive in-memory state with resilient localStorage persistence and subscriber notifications.
 */

import { UNITS } from "./units.js";

const STORAGE_KEY = "skypulse_store_v1";

const DEFAULT_STATE = {
  currentWeather: null,
  activeLocation: null,
  activeTab: "today", // 'today' | 'timeline' | 'states'
  timelineSegment: "all", // 'past' | 'today' | 'forecast' | 'all'
  timelineView: "cards", // 'cards' | 'table'
  activeStateSlug: null,
  stateOverview: null,
  countryOverview: null,
  favorites: [],
  recentSearches: [],
  units: {
    temp: UNITS.TEMP_C,
    wind: UNITS.WIND_KMH,
    precip: UNITS.PRECIP_MM,
    pressure: UNITS.PRESSURE_HPA,
  },
  theme: "auto", // 'auto' | 'light' | 'dark'
  lang: "en", // 'en' | 'hi'
  lastUpdated: null,
  isLoading: false,
  error: null,
};

class Store {
  constructor() {
    this.state = this._loadInitialState();
    this.listeners = new Set();
  }

  _loadInitialState() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          ...DEFAULT_STATE,
          favorites: parsed.favorites || [],
          recentSearches: parsed.recentSearches || [],
          units: { ...DEFAULT_STATE.units, ...(parsed.units || {}) },
          theme: parsed.theme || "auto",
          lang: parsed.lang || "en",
          activeLocation: parsed.lastLocation || null,
          currentWeather: parsed.lastWeather || null,
        };
      }
    } catch {
      // Ignore localStorage errors (e.g. private browsing quota)
    }
    return { ...DEFAULT_STATE };
  }

  _persist() {
    try {
      const payload = {
        favorites: this.state.favorites.slice(0, 12),
        recentSearches: this.state.recentSearches.slice(0, 10),
        units: this.state.units,
        theme: this.state.theme,
        lang: this.state.lang,
        lastLocation: this.state.activeLocation,
        lastWeather: this.state.currentWeather,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // Safe fallback
    }
  }

  get(key) {
    return this.state[key];
  }

  set(updates) {
    this.state = { ...this.state, ...updates };
    this._persist();
    this._notify();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  _notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state);
      } catch (e) {
        console.error("Subscriber notification error:", e);
      }
    }
  }

  addFavorite(loc) {
    const exists = this.state.favorites.some(
      (f) => Math.abs(f.lat - loc.lat) < 0.05 && Math.abs(f.lon - loc.lon) < 0.05
    );
    if (!exists) {
      const updated = [loc, ...this.state.favorites].slice(0, 12);
      this.set({ favorites: updated });
    }
  }

  removeFavorite(loc) {
    const updated = this.state.favorites.filter(
      (f) => !(Math.abs(f.lat - loc.lat) < 0.05 && Math.abs(f.lon - loc.lon) < 0.05)
    );
    this.set({ favorites: updated });
  }

  isFavorite(lat, lon) {
    return this.state.favorites.some(
      (f) => Math.abs(f.lat - lat) < 0.05 && Math.abs(f.lon - lon) < 0.05
    );
  }

  addRecentSearch(place) {
    const filtered = this.state.recentSearches.filter(
      (p) => !(Math.abs(p.latitude - place.latitude) < 0.05 && Math.abs(p.longitude - place.longitude) < 0.05)
    );
    const updated = [place, ...filtered].slice(0, 8);
    this.set({ recentSearches: updated });
  }
}

export const store = new Store();
