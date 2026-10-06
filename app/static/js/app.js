/**
 * SkyPulse Main Application Orchestrator
 * Bootstraps state, routing, DOM events, charts, search, and resilience mechanisms.
 */

import { UI_ICONS } from "../icons/weather-icons.js";
import { api } from "./api.js";
import { render15DayChart, renderHourlyChart, renderStateTrendChart } from "./charts.js";
import { getFallbackLocation, requestBrowserLocation } from "./geolocation.js";
import { initI18n, t } from "./i18n.js";
import { store } from "./state.js";
import { ui } from "./ui.js";
import { UNITS } from "./units.js";

class App {
  constructor() {
    this.allStates = [];
    this.searchDebounceTimer = null;
    this.refreshIntervalTimer = null;
    this.timeAgoTimer = null;
    this.lastFetchedTimestamp = null;
  }

  async init() {
    await initI18n();
    this.applyTheme(store.get("theme"));

    // Check debug mode
    const urlParams = new URLSearchParams(window.location.search);
    this.isDebug = urlParams.get("debug") === "1";

    // Setup DOM containers
    this.renderLayoutSkeleton();
    this.bindGlobalEvents();

    // Load states metadata
    try {
      this.allStates = await api.getStates();
    } catch (e) {
      console.warn("Failed to load states metadata:", e);
    }

    // Subscribe to state changes for reactive rendering
    store.subscribe((state) => this.onStateChange(state));

    // Handle deep links or initial location
    await this.handleInitialRoute(urlParams);

    // Setup periodic refresh
    this.setupAutoRefresh();

    // If debug mode is active, show drawer
    if (this.isDebug) {
      this.initDebugDrawer();
    }
  }

  applyTheme(theme) {
    if (theme === "auto") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute("data-theme", prefersDark ? "dark" : "light");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
  }

  renderLayoutSkeleton() {
    const appEl = document.getElementById("app");
    if (!appEl) return;

    appEl.innerHTML = `
      <div class="ambient-bg">
        <div class="cloud-drift"></div>
        <div class="night-stars"></div>
        <div class="rain-streaks"></div>
      </div>

      <div class="app-container">
        <!-- Top Bar -->
        <header class="top-bar">
          <div class="brand-section" id="brand-home" tabindex="0" role="button" aria-label="SkyPulse Home">
            <svg class="brand-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
            </svg>
            <span class="brand-title">SkyPulse</span>
          </div>

          <!-- Desktop Navigation -->
          <nav class="desktop-nav" aria-label="Desktop navigation">
            <button class="desktop-tab-btn active" data-tab="today">${t("tabToday")}</button>
            <button class="desktop-tab-btn" data-tab="timeline">${t("tab15Days")}</button>
            <button class="desktop-tab-btn" data-tab="states">${t("tabStates")}</button>
          </nav>

          <!-- Search Box -->
          <div class="search-wrapper">
            <div class="search-input-box">
              <span class="search-icon">${UI_ICONS.search}</span>
              <input
                type="text"
                id="search-input"
                class="search-input"
                placeholder="${t("searchPlaceholder")}"
                autocomplete="off"
                aria-label="Search city or place"
              />
              <span id="search-spinner" style="display:none;font-size:12px;">⏳</span>
            </div>
            <div class="search-dropdown" id="search-dropdown" role="listbox"></div>
          </div>

          <!-- Header Actions -->
          <div class="header-actions">
            <span id="time-ago-badge" style="font-size:var(--font-xs);color:var(--text-muted);display:none;"></span>
            <button class="btn-icon" id="btn-manual-refresh" title="Refresh weather" aria-label="Refresh">
              ${UI_ICONS.refresh}
            </button>
            <button class="btn-icon" id="btn-open-settings" title="Settings" aria-label="Settings">
              ${UI_ICONS.settings}
            </button>
          </div>
        </header>

        <!-- Dynamic Main Views -->
        <main id="main-content">
          <div id="pre-permission-area"></div>
          <div id="status-banner-area"></div>
          <div id="tab-today-view"></div>
          <div id="tab-timeline-view" style="display:none;"></div>
          <div id="tab-states-view" style="display:none;"></div>
        </main>

        <!-- Footer Attribution -->
        <footer class="app-footer">
          <div>Weather data by <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo.com</a></div>
          <div>Location geocoding © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a></div>
          <div style="margin-top:4px;">
            <a href="?debug=1" id="link-toggle-debug" style="color:var(--text-muted);font-size:11px;">[Debug Telemetry]</a>
          </div>
        </footer>
      </div>

      <!-- Mobile Bottom Navigation -->
      <nav class="bottom-nav" aria-label="Mobile navigation">
        <button class="nav-tab-btn active" data-tab="today">
          ${UI_ICONS.sunRays}
          <span>${t("tabToday")}</span>
        </button>
        <button class="nav-tab-btn" data-tab="timeline">
          ${UI_ICONS.calendar}
          <span>${t("tab15Days")}</span>
        </button>
        <button class="nav-tab-btn" data-tab="states">
          ${UI_ICONS.map}
          <span>${t("tabStates")}</span>
        </button>
      </nav>

      <!-- Settings Modal -->
      <div class="modal-overlay" id="settings-modal" role="dialog" aria-modal="true" aria-label="Settings">
        <div class="modal-content">
          <div class="modal-header">
            <h3 style="font-size:var(--font-lg);font-weight:bold;">${t("settings")}</h3>
            <button class="btn-icon" id="btn-close-settings" aria-label="Close settings">${UI_ICONS.close}</button>
          </div>

          <div style="display:flex;flex-direction:column;gap:16px;">
            <!-- Units: Temperature -->
            <div>
              <label style="font-size:var(--font-sm);font-weight:bold;display:block;margin-bottom:6px;">Temperature Unit</label>
              <div class="segmented-control" id="settings-unit-temp">
                <button class="segmented-btn" data-unit="C">Celsius (°C)</button>
                <button class="segmented-btn" data-unit="F">Fahrenheit (°F)</button>
              </div>
            </div>

            <!-- Units: Wind -->
            <div>
              <label style="font-size:var(--font-sm);font-weight:bold;display:block;margin-bottom:6px;">Wind Speed</label>
              <div class="segmented-control" id="settings-unit-wind">
                <button class="segmented-btn" data-unit="km/h">km/h</button>
                <button class="segmented-btn" data-unit="mph">mph</button>
                <button class="segmented-btn" data-unit="m/s">m/s</button>
              </div>
            </div>

            <!-- Units: Precipitation -->
            <div>
              <label style="font-size:var(--font-sm);font-weight:bold;display:block;margin-bottom:6px;">Precipitation</label>
              <div class="segmented-control" id="settings-unit-precip">
                <button class="segmented-btn" data-unit="mm">Millimeters (mm)</button>
                <button class="segmented-btn" data-unit="in">Inches (in)</button>
              </div>
            </div>

            <!-- Theme Switcher -->
            <div>
              <label style="font-size:var(--font-sm);font-weight:bold;display:block;margin-bottom:6px;">Appearance</label>
              <div class="segmented-control" id="settings-theme">
                <button class="segmented-btn" data-theme="auto">${t("auto")}</button>
                <button class="segmented-btn" data-theme="light">${t("light")}</button>
                <button class="segmented-btn" data-theme="dark">${t("dark")}</button>
              </div>
            </div>

            <!-- Favorites List -->
            <div>
              <label style="font-size:var(--font-sm);font-weight:bold;display:block;margin-bottom:6px;">Favorite Locations</label>
              <div id="favorites-list-container" style="display:flex;flex-direction:column;gap:6px;max-height:160px;overflow-y:auto;"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Debug Drawer -->
      <div class="debug-drawer" id="debug-drawer">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <strong>⚡ SkyPulse Telemetry & Upstream Inspector (?debug=1)</strong>
          <button id="btn-close-debug" style="background:transparent;border:none;color:#94a3b8;cursor:pointer;">✕</button>
        </div>
        <div id="debug-stats-bar" style="color:#38bdf8;">Loading telemetry...</div>
        <table class="debug-logs-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Endpoint / Resource</th>
              <th>Status</th>
              <th>Latency</th>
              <th>Cache</th>
            </tr>
          </thead>
          <tbody id="debug-logs-tbody"></tbody>
        </table>
      </div>
    `;
  }

  async handleInitialRoute(urlParams) {
    const stateSlug = urlParams.get("state");
    const cityName = urlParams.get("city");

    if (stateSlug) {
      store.set({ activeTab: "states", activeStateSlug: stateSlug });
      this.loadStateOverview(stateSlug);

      if (cityName) {
        // Also load city weather
        try {
          const results = await api.search(cityName, stateSlug);
          if (results.length) {
            const place = results[0];
            await this.loadWeatherForCoords(place.latitude, place.longitude, place.name, place.admin1);
            return;
          }
        } catch {
          // Continue
        }
      }
    }

    // Default flow: Start with IP fallback or default city immediately so user sees zero delay
    const initialLocation = await getFallbackLocation();
    await this.loadWeatherForCoords(
      initialLocation.lat,
      initialLocation.lon,
      initialLocation.name,
      initialLocation.state,
      initialLocation.isApproximate,
      initialLocation.source
    );

    // If browser location hasn't been granted yet, show friendly pre-permission card
    if (initialLocation.source === "ip" || initialLocation.source === "default") {
      this.renderPrePermissionCard();
    }
  }

  renderPrePermissionCard() {
    const area = document.getElementById("pre-permission-area");
    if (!area) return;

    area.innerHTML = `
      <div class="pre-permission-card" id="card-pre-perm" role="alert">
        <div>
          <strong style="font-size:var(--font-base);">Enable location for hyper-local forecasts</strong>
          <p style="font-size:var(--font-sm);color:var(--text-secondary);">
            Get minute-by-minute updates for your exact neighborhood.
          </p>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn-primary" id="btn-grant-location">${UI_ICONS.mapPin} ${t("useMyLocation")}</button>
          <button class="btn-secondary" id="btn-dismiss-perm">Not Now</button>
        </div>
      </div>
    `;

    document.getElementById("btn-grant-location")?.addEventListener("click", async () => {
      area.innerHTML = "";
      await this.triggerBrowserLocation();
    });

    document.getElementById("btn-dismiss-perm")?.addEventListener("click", () => {
      area.innerHTML = "";
    });
  }

  async triggerBrowserLocation() {
    try {
      const loc = await requestBrowserLocation();
      await this.loadWeatherForCoords(loc.lat, loc.lon, loc.name, loc.state, false, "geo");
    } catch (err) {
      console.warn("Browser geolocation denied or timed out:", err);
      // Fall back to IP location
      const fallback = await getFallbackLocation();
      await this.loadWeatherForCoords(
        fallback.lat,
        fallback.lon,
        fallback.name,
        fallback.state,
        true,
        "ip"
      );
    }
  }

  async loadWeatherForCoords(lat, lon, name, state = null, isApprox = false, source = "default") {
    store.set({ isLoading: true });
    try {
      const weatherData = await api.getWeather(lat, lon, name, state);
      this.lastFetchedTimestamp = Date.now();

      store.set({
        currentWeather: weatherData,
        activeLocation: {
          name: name || weatherData.location.name,
          state: state || weatherData.location.state,
          country: weatherData.location.country,
          lat,
          lon,
          isApproximate: isApprox,
          source,
        },
        isLoading: false,
        error: null,
      });

      // Update deep link URL without page reload
      this.updateUrl(lat, lon, name, state);
      this.updateTimeAgoBadge();
    } catch (err) {
      console.error("Failed to load weather:", err);
      store.set({ isLoading: false, error: err.message });
      alert(`Could not load weather: ${err.message}`);
    }
  }

  async loadStateOverview(slug) {
    store.set({ activeStateSlug: slug, isLoading: true });
    try {
      const [overview, country] = await Promise.all([
        api.getStateOverview(slug),
        api.getCountryOverview(),
      ]);
      store.set({
        stateOverview: overview,
        countryOverview: country,
        isLoading: false,
      });
    } catch (err) {
      console.error("Failed to load state overview:", err);
      store.set({ isLoading: false });
    }
  }

  updateUrl(lat, lon, name, state) {
    const url = new URL(window.location);
    if (state) {
      const matched = this.allStates.find(
        (s) => s.name.toLowerCase() === state.toLowerCase() || s.slug === state.toLowerCase()
      );
      if (matched) {
        url.searchParams.set("state", matched.slug);
      }
    }
    if (name) {
      url.searchParams.set("city", name.toLowerCase());
    }
    window.history.pushState({}, "", url);
  }

  onStateChange(state) {
    const { currentWeather, activeLocation, activeTab, stateOverview, countryOverview } = state;

    // 1. Render Status Banner
    const bannerArea = document.getElementById("status-banner-area");
    if (bannerArea && activeLocation) {
      bannerArea.innerHTML = ui.renderStatusBanner(activeLocation, currentWeather?.meta);
      document
        .getElementById("btn-request-location")
        ?.addEventListener("click", () => this.triggerBrowserLocation());
    }

    // 2. Render Today View
    const todayView = document.getElementById("tab-today-view");
    if (todayView && currentWeather && activeLocation) {
      todayView.innerHTML = `
        ${ui.renderHero(currentWeather, activeLocation)}
        ${ui.renderInsights(currentWeather.insights)}
        ${ui.renderTiles(currentWeather.current, currentWeather.air_quality)}
        ${ui.renderHourly(currentWeather.hourly)}
      `;

      // Render 48-hour hourly Chart.js
      renderHourlyChart("chart-hourly", currentWeather.hourly, state.units.temp);

      // Bind Favorite toggle
      document.getElementById("btn-toggle-favorite")?.addEventListener("click", () => {
        if (store.isFavorite(activeLocation.lat, activeLocation.lon)) {
          store.removeFavorite(activeLocation);
        } else {
          store.addFavorite(activeLocation);
        }
        this.onStateChange(store.state);
      });
    }

    // 3. Render 15-Day Timeline View
    const timelineView = document.getElementById("tab-timeline-view");
    if (timelineView && currentWeather) {
      timelineView.innerHTML = ui.render15DayTimeline(currentWeather.daily);
      render15DayChart("chart-15day", currentWeather.daily, state.units.temp);
      this.bindTimelineEvents();
    }

    // 4. Render State Dashboard View
    const statesView = document.getElementById("tab-states-view");
    if (statesView) {
      statesView.innerHTML = ui.renderStateDashboard(
        this.allStates,
        stateOverview,
        countryOverview,
        state.activeStateSlug
      );
      if (stateOverview?.trend?.length) {
        renderStateTrendChart("chart-state-trend", stateOverview.trend, state.units.temp);
      }
      this.bindStateDashboardEvents();
    }

    // Switch active tab view visibility
    this.switchTabDisplay(activeTab);
  }

  switchTabDisplay(activeTab) {
    const todayEl = document.getElementById("tab-today-view");
    const timeEl = document.getElementById("tab-timeline-view");
    const stateEl = document.getElementById("tab-states-view");

    if (todayEl) todayEl.style.display = activeTab === "today" ? "block" : "none";
    if (timeEl) timeEl.style.display = activeTab === "timeline" ? "block" : "none";
    if (stateEl) stateEl.style.display = activeTab === "states" ? "block" : "none";

    // Update active class on tab buttons
    document.querySelectorAll(".nav-tab-btn, .desktop-tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === activeTab);
    });
  }

  bindGlobalEvents() {
    // Brand home click
    document.getElementById("brand-home")?.addEventListener("click", () => {
      store.set({ activeTab: "today" });
    });

    // Tab switching (mobile & desktop)
    document.addEventListener("click", (e) => {
      const tabBtn = e.target.closest("[data-tab]");
      if (tabBtn) {
        const tab = tabBtn.dataset.tab;
        store.set({ activeTab: tab });
        if (tab === "states" && !store.get("stateOverview") && this.allStates.length) {
          const firstSlug = store.get("activeStateSlug") || this.allStates[0].slug;
          this.loadStateOverview(firstSlug);
        }
      }
    });

    // Live search input with debounce
    const searchInput = document.getElementById("search-input");
    const dropdown = document.getElementById("search-dropdown");

    searchInput?.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      clearTimeout(this.searchDebounceTimer);
      if (val.length < 2) {
        if (dropdown) dropdown.classList.remove("active");
        return;
      }

      this.searchDebounceTimer = setTimeout(async () => {
        document.getElementById("search-spinner").style.display = "inline";
        try {
          const results = await api.search(val);
          this.renderSearchResults(results);
        } catch {
          // Handle error
        } finally {
          document.getElementById("search-spinner").style.display = "none";
        }
      }, 300);
    });

    // Close dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".search-wrapper")) {
        dropdown?.classList.remove("active");
      }
    });

    // Refresh button
    document.getElementById("btn-manual-refresh")?.addEventListener("click", () => {
      const loc = store.get("activeLocation");
      if (loc) {
        this.loadWeatherForCoords(loc.lat, loc.lon, loc.name, loc.state, loc.isApproximate, loc.source);
      }
    });

    // Settings Modal
    const modal = document.getElementById("settings-modal");
    document.getElementById("btn-open-settings")?.addEventListener("click", () => {
      this.populateSettingsModal();
      modal?.classList.add("active");
    });
    document.getElementById("btn-close-settings")?.addEventListener("click", () => {
      modal?.classList.remove("active");
    });
    modal?.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });

    // Settings Segmented Buttons: Units
    document.getElementById("settings-unit-temp")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-unit]");
      if (btn) {
        const u = btn.dataset.unit;
        const currentUnits = store.get("units");
        store.set({ units: { ...currentUnits, temp: u } });
        this.populateSettingsModal();
      }
    });

    document.getElementById("settings-unit-wind")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-unit]");
      if (btn) {
        const u = btn.dataset.unit;
        const currentUnits = store.get("units");
        store.set({ units: { ...currentUnits, wind: u } });
        this.populateSettingsModal();
      }
    });

    document.getElementById("settings-unit-precip")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-unit]");
      if (btn) {
        const u = btn.dataset.unit;
        const currentUnits = store.get("units");
        store.set({ units: { ...currentUnits, precip: u } });
        this.populateSettingsModal();
      }
    });

    // Settings Theme
    document.getElementById("settings-theme")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-theme]");
      if (btn) {
        const th = btn.dataset.theme;
        store.set({ theme: th });
        this.applyTheme(th);
        this.populateSettingsModal();
      }
    });

    // Browser back/forward navigation support
    window.addEventListener("popstate", () => {
      const params = new URLSearchParams(window.location.search);
      this.handleInitialRoute(params);
    });

    // Tab focus / visibility change refresh
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        this.checkIfNeedsRefresh();
      }
    });
  }

  renderSearchResults(results) {
    const dropdown = document.getElementById("search-dropdown");
    if (!dropdown) return;

    if (!results || !results.length) {
      dropdown.innerHTML = `<div style="padding:12px;color:var(--text-muted);font-size:var(--font-sm);">No places found.</div>`;
      dropdown.classList.add("active");
      return;
    }

    dropdown.innerHTML = results
      .map(
        (r) => `
      <div class="search-item" data-lat="${r.latitude}" data-lon="${r.longitude}" data-name="${r.name}" data-state="${r.admin1 || ""}">
        <div>
          <div class="search-item-title">${r.name}</div>
          <div class="search-item-sub">${r.admin1 ? `${r.admin1}, ` : ""}${r.country}</div>
        </div>
        <span style="font-size:11px;color:var(--text-muted);">${r.population ? `${(r.population / 1000).toFixed(0)}k pop` : ""}</span>
      </div>`
      )
      .join("");

    dropdown.classList.add("active");

    dropdown.querySelectorAll(".search-item").forEach((item) => {
      item.addEventListener("click", () => {
        const lat = parseFloat(item.dataset.lat);
        const lon = parseFloat(item.dataset.lon);
        const name = item.dataset.name;
        const state = item.dataset.state || null;

        dropdown.classList.remove("active");
        document.getElementById("search-input").value = name;
        this.loadWeatherForCoords(lat, lon, name, state, false, "search");
      });
    });
  }

  bindTimelineEvents() {
    // Segmented control (Past 7 | All 15 | Next 7)
    document.querySelectorAll("[data-segment]").forEach((btn) => {
      btn.addEventListener("click", () => {
        store.set({ timelineSegment: btn.dataset.segment });
      });
    });

    // Cards vs Table view
    document.querySelectorAll("[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        store.set({ timelineView: btn.dataset.view });
      });
    });
  }

  bindStateDashboardEvents() {
    // State dropdown
    const select = document.getElementById("select-state");
    select?.addEventListener("change", (e) => {
      const slug = e.target.value;
      if (slug) {
        this.loadStateOverview(slug);
      }
    });

    // Sort cities
    const sortSelect = document.getElementById("select-city-sort");
    sortSelect?.addEventListener("change", (e) => {
      const order = e.target.value;
      const statesView = document.getElementById("tab-states-view");
      if (statesView) {
        statesView.innerHTML = ui.renderStateDashboard(
          this.allStates,
          store.get("stateOverview"),
          store.get("countryOverview"),
          store.get("activeStateSlug"),
          order
        );
        this.bindStateDashboardEvents();
      }
    });

    // Click city card to drill down
    document.querySelectorAll(".city-card").forEach((card) => {
      card.addEventListener("click", () => {
        const lat = parseFloat(card.dataset.lat);
        const lon = parseFloat(card.dataset.lon);
        const name = card.dataset.name;
        const stateSlug = store.get("activeStateSlug");
        store.set({ activeTab: "today" });
        this.loadWeatherForCoords(lat, lon, name, stateSlug);
      });
    });
  }

  populateSettingsModal() {
    const units = store.get("units");
    const theme = store.get("theme");

    // Highlight active unit buttons
    document.querySelectorAll("#settings-unit-temp .segmented-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.unit === units.temp);
    });
    document.querySelectorAll("#settings-unit-wind .segmented-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.unit === units.wind);
    });
    document.querySelectorAll("#settings-unit-precip .segmented-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.unit === units.precip);
    });
    document.querySelectorAll("#settings-theme .segmented-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.theme === theme);
    });

    // Populate favorites
    const favsContainer = document.getElementById("favorites-list-container");
    if (favsContainer) {
      const favs = store.get("favorites") || [];
      if (!favs.length) {
        favsContainer.innerHTML = `<span style="font-size:var(--font-xs);color:var(--text-muted);">No favorite cities saved yet. Star a city to pin it here.</span>`;
      } else {
        favsContainer.innerHTML = favs
          .map(
            (f) => `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 10px;background:rgba(255,255,255,0.3);border-radius:var(--radius-md);">
            <span class="fav-item-link" data-lat="${f.lat}" data-lon="${f.lon}" data-name="${f.name}" data-state="${f.state || ""}" style="cursor:pointer;font-size:var(--font-sm);font-weight:500;">
              ⭐ ${f.name}${f.state ? `, ${f.state}` : ""}
            </span>
            <button class="btn-icon fav-item-remove" data-lat="${f.lat}" data-lon="${f.lon}" style="color:red;padding:2px;" aria-label="Remove favorite">✕</button>
          </div>`
          )
          .join("");

        favsContainer.querySelectorAll(".fav-item-link").forEach((link) => {
          link.addEventListener("click", () => {
            const lat = parseFloat(link.dataset.lat);
            const lon = parseFloat(link.dataset.lon);
            const name = link.dataset.name;
            const state = link.dataset.state || null;
            document.getElementById("settings-modal")?.classList.remove("active");
            this.loadWeatherForCoords(lat, lon, name, state);
          });
        });

        favsContainer.querySelectorAll(".fav-item-remove").forEach((remBtn) => {
          remBtn.addEventListener("click", () => {
            const lat = parseFloat(remBtn.dataset.lat);
            const lon = parseFloat(remBtn.dataset.lon);
            store.removeFavorite({ lat, lon });
            this.populateSettingsModal();
          });
        });
      }
    }
  }

  setupAutoRefresh() {
    // 10 minutes interval
    this.refreshIntervalTimer = setInterval(() => {
      this.checkIfNeedsRefresh();
    }, 600000);

    // Update 'Updated x min ago' text every minute
    this.timeAgoTimer = setInterval(() => {
      this.updateTimeAgoBadge();
    }, 60000);
  }

  checkIfNeedsRefresh() {
    if (this.lastFetchedTimestamp && Date.now() - this.lastFetchedTimestamp > 600000) {
      const loc = store.get("activeLocation");
      if (loc) {
        this.loadWeatherForCoords(loc.lat, loc.lon, loc.name, loc.state, loc.isApproximate, loc.source);
      }
    }
  }

  updateTimeAgoBadge() {
    const badge = document.getElementById("time-ago-badge");
    if (!badge || !this.lastFetchedTimestamp) return;

    const diffMins = Math.floor((Date.now() - this.lastFetchedTimestamp) / 60000);
    badge.style.display = "inline";
    if (diffMins <= 0) {
      badge.textContent = t("justNow");
    } else {
      badge.textContent = t("updatedAgo", { m: diffMins });
    }
  }

  initDebugDrawer() {
    const drawer = document.getElementById("debug-drawer");
    if (!drawer) return;
    drawer.classList.add("active");

    document.getElementById("btn-close-debug")?.addEventListener("click", () => {
      drawer.classList.remove("active");
    });

    const updateDebug = async () => {
      try {
        const stats = await api.getDebugStats();
        const bar = document.getElementById("debug-stats-bar");
        const tbody = document.getElementById("debug-logs-tbody");

        if (bar) {
          bar.textContent = `Server Hits: ${stats.total_cache_hits} | Upstream Calls: ${stats.total_upstream_calls} | Client Log Count: ${api.debugLogs.length}`;
        }

        if (tbody) {
          tbody.innerHTML = api.debugLogs
            .slice(0, 10)
            .map(
              (l) => `
            <tr>
              <td>${l.timestamp}</td>
              <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${l.url}</td>
              <td style="color:${l.status === 200 ? "#4ade80" : "#f87171"}">${l.status}</td>
              <td>${l.durationMs}ms</td>
              <td>${l.cached ? "HIT" : "MISS"}</td>
            </tr>`
            )
            .join("");
        }
      } catch {
        // Ignore
      }
    };

    updateDebug();
    setInterval(updateDebug, 3000);
  }
}

// Bootstrap application on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  const app = new App();
  app.init();
});
