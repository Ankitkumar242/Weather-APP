/**
 * SkyPulse Service Worker
 * Caches application shell assets for instant load and offline resilience.
 */

const CACHE_NAME = 'skypulse-shell-v1';
const SHELL_ASSETS = [
  '/',
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
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(SHELL_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // For API calls: Network first, with fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request);
      })
    );
    return;
  }

  // For Shell static assets: Cache first, fallback to network
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return (
        cached ||
        fetch(event.request).then((response) => {
          if (response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
      );
    })
  );
});
