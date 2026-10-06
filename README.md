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

## 🐳 Production Deployment

### 1. Dockerfile
SkyPulse includes a hardened multi-process production container using Gunicorn process management with async Uvicorn workers and a dedicated non-root user (`appuser`):
```bash
# Build the production image
docker build -t skypulse:latest .

# Run container with custom PORT support
docker run -e PORT=8000 -e ALLOWED_ORIGINS="https://localhost,capacitor://localhost" -p 8000:8000 --name skypulse skypulse:latest
```
Container healthiness is monitored automatically via `HEALTHCHECK` hitting `http://localhost:${PORT}/healthz`.

### 2. Render (`render.yaml`)
A turnkey `render.yaml` configuration is included for deploying to Render's free Web Service tier:
1. Push your repository to GitHub or GitLab.
2. Link your repository in Render and create a **Blueprint Instance**.
3. Render automatically picks up `render.yaml`, configures the Docker runtime, sets `/healthz` as the health check path, and provisions the service.

### 3. Railway Deployment
1. Install the Railway CLI or use the web dashboard at [railway.app](https://railway.app):
   ```bash
   railway login
   railway init
   railway up
   ```
2. In the Railway dashboard under **Variables**, set:
   - `PORT=8000`
   - `APP_ENV=production`
   - `ALLOWED_ORIGINS=https://localhost,capacitor://localhost,https://<your-railway-domain>.up.railway.app`
3. Railway automatically detects the production `Dockerfile` and builds the image.

### 4. Fly.io Deployment
1. Install `flyctl` and launch the app:
   ```bash
   fly launch --no-deploy
   ```
2. Configure `fly.toml` internal port to `8000`:
   ```toml
   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
   ```
3. Set environment secrets:
   ```bash
   fly secrets set ALLOWED_ORIGINS="https://localhost,capacitor://localhost,https://<app>.fly.dev"
   ```
4. Deploy:
   ```bash
   fly deploy
   ```

### 5. Strict CORS Security
CORS is strictly locked via the `ALLOWED_ORIGINS` environment variable in `app/config.py`. Wildcard (`*`) origins are forbidden. Native mobile apps connect via `capacitor://localhost` and `https://localhost`.

---

## 📱 Progressive Web App (PWA)

SkyPulse is a certified, installable Progressive Web App:
- **Web App Manifest**: Root-accessible `manifest.webmanifest` defining `name`, `short_name`, `standalone` display mode, `#2563EB` theme color, `#0F172A` background color, standard 192/512px icons, and circular safe-zone maskable icons.
- **Service Worker (`/sw.js`)**:
  - Registered at root scope `/` with `Service-Worker-Allowed: /` header.
  - Pre-caches the application shell (HTML, stylesheets, scripts, local Chart.js, i18n JSONs, icons).
  - **Stale-While-Revalidate Strategy**: Applied to weather forecasts (`/api/v1/weather`) and state trends (`/api/v1/states/*`). Cached data is displayed instantly while revalidating in the background.
  - **Offline Resilience**: When internet access is disconnected, previously loaded locations remain fully viewable with an **"⚠️ Offline / Stale"** badge. If navigating while offline without cache, `/offline.html` is served.
- **Install Prompt Handling**:
  - Desktop & Android: Catches `beforeinstallprompt` to display an inline **"📲 Install App"** button in the header bar.
  - iOS Safari: Detects Safari on iPhone/iPad and displays an interactive instruction banner: *"Tap Share (⎋) then 'Add to Home Screen' (⊞)"*.

---

## 🤖 Android Native App (Capacitor)

### 📲 Direct Phone Download (One-Click APK Install)
You can download and install SkyPulse directly on your Android phone without setting up a development environment:

- ⬇️ **[Download SkyPulse-v1.0-debug.apk](https://github.com/Ankitkumar242/Weather-APP/releases/latest/download/SkyPulse-v1.0-debug.apk)** (Direct APK Download)
- 📦 **[View Latest GitHub Release](https://github.com/Ankitkumar242/Weather-APP/releases)**

**Quick Phone Installation Steps:**
1. Tap the download link above on your phone's browser.
2. Once downloaded, open your notifications or **Downloads** folder and tap `SkyPulse-v1.0-debug.apk`.
3. If prompted by Android with *"Install unknown apps"*, tap **Settings** and toggle **"Allow from this source"**.
4. Tap **Install** and then **Open**! Enjoy native weather on your phone.


### 1. Architecture
- The native wrapper lives in `/mobile`.
- The build script (`node scripts/build-mobile.js`) compiles `app/static` and outputs `mobile/dist/index.html` configured with `API_BASE_URL`.
- Native Geolocation is orchestrated by `@capacitor/geolocation` in `app/static/js/geolocation.js` (with seamless fallback to `navigator.geolocation` on web).

### 2. Prerequisites
- **Node.js**: v18.0.0 or higher (`node -v`)
- **Android Studio**: Ladybug / Hedgehog or newer with Android SDK Platform 34 and Android Build Tools.
- **Java Development Kit**: JDK 17 or 21 (`JAVA_HOME` set).

### 3. Quick Start & Build

```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# 1. Build web distribution & sync with Android native project
npm run android:sync

# 2. Build Debug APK (outputs to mobile/android/app/build/outputs/apk/debug/app-debug.apk)
npm run android:build
```

### 4. Installing on Phone / Emulator
- **Physical Device**: Connect phone via USB with *USB Debugging* enabled, then run:
  ```bash
  adb install android/app/build/outputs/apk/debug/app-debug.apk
  ```
- **Android Studio Emulator**: Drag and drop `app-debug.apk` directly into your running Android emulator, or open `/mobile/android` in Android Studio and click **Run (Shift + F10)**.

### 5. Google Play Console Release (Signed AAB)
To generate a release Android App Bundle (`.aab`) for Google Play Store submission:

1. Create a release signing keystore (if you don't already have one):
   ```bash
   keytool -genkey -v -keystore skypulse-release.keystore -alias skypulse -keyalg RSA -keysize 2048 -validity 10000
   ```
2. Export signing credentials in your environment (never commit these secrets):
   ```bash
   export KEYSTORE_PATH="/path/to/skypulse-release.keystore"
   export KEYSTORE_PASSWORD="your-keystore-password"
   export KEYSTORE_ALIAS="skypulse"
   export KEY_PASSWORD="your-key-password"
   ```
3. Run the release build script:
   ```bash
   npm run android:release
   ```
4. Upload `mobile/android/app/build/outputs/bundle/release/app-release.aab` directly to Google Play Console under **Production** or **Internal testing**.

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

