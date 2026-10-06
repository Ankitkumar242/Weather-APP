# SkyPulse ⚡

> **World-Class Precision Weather Intelligence Web Application**  
> Modern glassmorphism UI, 15-day timeline analysis (7 past + today + 7 forecast), resilient state-level India weather dashboards, zero runtime CDN dependencies, and keyless upstream APIs.

---

## 🌟 Key Features

1. **My Location Flow (F1)**
   - Pre-permission card with smooth transition to `navigator.geolocation`.
   - Fallback hierarchy: IP Geolocation (`ipwho.is` → `ipapi.co`) with `"approximate"` badge → Last saved localStorage place → Default city (New Delhi).
   - Auto-refreshes every 10 minutes and on browser tab focus.

2. **Current Conditions Hero & Detailed Tiles (F2)**
   - Hero card with big temperature, dynamic condition-mapped inline SVGs, feels-like, today's high/low, location-local time, sunrise, and sunset.
   - 8 condition tiles: Humidity, Wind (speed, compass arrow, gusts), Air Quality (US AQI with WHO categories, PM2.5, PM10), UV Index, Rain, Pressure, Visibility, and Cloud Cover.

3. **15-Day Timeline Analysis (F3)**
   - Previous 7 days model analysis + Today + Next 7 days forecast.
   - Dual-axis Chart.js temperature band (past days in neutral tone, forecast in accent tone) + rainfall bars with a vertical dashed "Today" line marker.
   - Segmented control: `Past 7` | `Today` | `Next 7` | `All 15`.
   - Cards View and sortable Data Table View toggles.
   - Summary statistics: Average high, total rainfall, hottest/coldest day for past 7 days; rainy day count, peak temp, and "best outdoor day" for next 7 days.

4. **48-Hour Hourly Scrubbing (F4)**
   - Hourly temperature curve + precipitation probability bars for the next 48 hours sliced starting from the location's local hour.

5. **State-Wise Filter & Regional Dashboard (F5)**
   - All 36 Indian States and Union Territories with major cities pre-compiled in `app/data/regions/in.json`.
   - Single batched Open-Meteo call for all cities in a state with coordinate deduplication (e.g., Chandigarh serving Punjab, Haryana, and the UT).
   - Sortable city cards: Hottest, Coldest, Rainiest, A–Z.
   - 15-day averaged state trend line.
   - "All-India Overview" featuring national temperature highlights (hottest, coldest, and wettest capitals).
   - Shareable deep links (`?state=rajasthan&city=jaipur`) with HTML5 History API support.

6. **Smart Weather Insights (F7)**
   - Rule-based advisories for extreme heat, heavy rainfall/thunderstorms, strong wind gusts, high UV, and poor air quality.
   - Practical carry/wear suggestions (e.g. umbrella, sunscreen, N95 mask, warm jacket).

7. **Personalization & Settings (F6)**
   - Saved favorites (up to 12 starred locations).
   - Real-time client-side unit conversions: °C/°F, km/h/mph/m/s, mm/in, hPa/inHg. Zero refetch required.
   - Appearance mode: Auto (system), Light, or Dark.
   - English / Hindi language toggle (`i18n`).

8. **Resilience & Caching (F8)**
   - Coordinate rounding to 2 decimals for high cache hit rates.
   - In-memory `cachetools.TTLCache` + single-flight request coalescing (locks duplicate concurrent calls).
   - Stale cache retention: on upstream outage or 5xx error, serves last cached snapshot with a `"stale"` badge.
   - OpenStreetMap Nominatim token bucket rate limiter strictly enforcing ≤ 1.0 req/s.

---

## 🛠️ Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, httpx (async), Pydantic v2 + pydantic-settings, cachetools, slowapi.
- **Frontend**: Jinja2 shell, Vanilla ES Modules, Hand-written CSS design tokens with glassmorphism, Vendored local Chart.js (v4.4.1), System Font Stack, Zero runtime CDN.
- **Testing & Quality**: pytest, pytest-asyncio, respx, ruff, mypy.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/Weather-APP.git
cd Weather-APP

# Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(No API keys required. All data sources are free and keyless.)*

### 4. Running the Application
```bash
# Using Makefile
make dev

# Or directly with Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at **http://localhost:8000**.

### 5. Running Tests & Quality Checks
```bash
# Run pytest with service coverage
make test
# or: pytest --cov=app.services -v

# Run linters and typecheckers
make lint
# or: ruff check app tests && mypy app tests
```

---

## 🐳 Docker Deployment

```bash
# Build the container image
docker build -t skypulse:latest .

# Run container
docker run -p 8000:8000 --name skypulse skypulse:latest
```
Visit http://localhost:8000 to access the application.

---

## 📊 Telemetry & Debug Mode

Append `?debug=1` to the URL or click **[Debug Telemetry]** in the footer to open the live upstream inspector drawer. It reports:
- Memory cache hits vs. misses.
- Total outbound upstream calls.
- Live logs of endpoints, HTTP status codes, and roundtrip latency in milliseconds.

---

## ⚖️ Legal & Terms of Use

- **Open-Meteo**: Weather forecast, historical analysis, and air quality data are provided by [Open-Meteo.com](https://open-meteo.com/). Open-Meteo's free tier is strictly for **non-commercial use** under their API terms. Any commercial use requires purchasing an official Open-Meteo commercial subscription plan.
- **OpenStreetMap**: Reverse geocoding data is provided by © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) via the Nominatim API in accordance with the Nominatim Usage Policy.

