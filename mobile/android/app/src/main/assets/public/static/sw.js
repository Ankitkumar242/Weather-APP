/**
 * SkyPulse Service Worker (Root Scope)
 * Features:
 * - App Shell Pre-caching
 * - Stale-While-Revalidate for /api/v1/weather and /api/v1/states/*
 * - Offline navigation fallback to /offline.html
 * - Offline cached data delivery with stale indicators
 */

const SHELL_CACHE_NAME = 'skypulse-shell-v2';
const DATA_CACHE_NAME = 'skypulse-data-v2';

const PRECACHE_URLS = [
  '/',
  '/offline.html',
  '/manifest.webmanifest',
  '/static/css/tokens.css',
  '/static/css/animations.css',
  '/static/css/main.css',
  '/static/vendor/chart.umd.min.js',
  '/static/js/app.js',
  '/static/js/api.js',
  '/static/js/state.js',
  '/static/js/ui.js',
  '/static/js/charts.js',
  '/static/js/geolocation.js',
  '/static/js/units.js',
  '/static/js/i18n.js',
  '/static/icons/weather-icons.js',
  '/static/i18n/en.json',
  '/static/i18n/hi.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon-maskable-192.png',
  '/static/icons/icon-maskable-512.png',
  '/static/icons/apple-touch-icon.png',
  '/static/icons/favicon.png'
];

const PRECACHE_DATA_URLS = [
  '/api/v1/states',
  '/api/v1/weather?lat=28.6139&lon=77.2090'
];

// Install: Precache shell and default API data
self.addEventListener('install', (event) => {
  event.waitUntil(
    Promise.all([
      caches.open(SHELL_CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)),
      caches.open(DATA_CACHE_NAME).then((cache) => cache.addAll(PRECACHE_DATA_URLS).catch(() => {}))
    ]).then(() => self.skipWaiting())
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== SHELL_CACHE_NAME && key !== DATA_CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event listener
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. Navigation requests (HTML documents)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        const shell = await caches.match('/');
        if (shell) return shell;
        return caches.match('/offline.html');
      })
    );
    return;
  }

  // 2. Stale-While-Revalidate for Weather & State Overview APIs
  const isWeatherApi = url.pathname.startsWith('/api/v1/weather');
  const isStatesApi = url.pathname.startsWith('/api/v1/states') || url.pathname.startsWith('/api/v1/overview');

  if (isWeatherApi || isStatesApi) {
    event.respondWith(
      caches.open(DATA_CACHE_NAME).then(async (cache) => {
        const cachedResponse = await cache.match(request);

        const networkFetch = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          })
          .catch((err) => {
            // Network failed - return cached or synthesized offline payload
            if (cachedResponse) {
              return cachedResponse;
            }
            throw err;
          });

        // If we have cached data, return it immediately (stale-while-revalidate)
        if (cachedResponse) {
          // Trigger the network fetch in the background to revalidate
          event.waitUntil(networkFetch);
          return cachedResponse;
        }

        // Otherwise await network
        return networkFetch;
      })
    );
    return;
  }

  // 3. Static Assets: Cache-First, fallback to network
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((response) => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(SHELL_CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // Default: pass through
  event.respondWith(fetch(request));
});
