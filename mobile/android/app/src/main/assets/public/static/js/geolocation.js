/**
 * SkyPulse Geolocation Orchestrator
 * Coordinates browser navigator.geolocation, native Capacitor GPS, IP fallback, and default location flows.
 */

import { api } from "./api.js";
import { store } from "./state.js";

const DEFAULT_FALLBACK = {
  name: "New Delhi",
  state: "Delhi",
  country: "India",
  lat: 28.6139,
  lon: 77.209,
  isApproximate: false,
  source: "default",
};

async function getNativeCoordinates() {
  const Geolocation = window.Capacitor?.Plugins?.Geolocation;
  if (!Geolocation) {
    throw new Error("Capacitor Geolocation plugin unavailable");
  }

  try {
    const status = await Geolocation.checkPermissions();
    if (status?.location !== "granted" && status?.coarseLocation !== "granted") {
      await Geolocation.requestPermissions();
    }
  } catch (err) {
    console.warn("Capacitor permissions request note:", err);
  }

  // 1. Try high accuracy first (GPS satellites)
  try {
    const pos = await Geolocation.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 8000,
      maximumAge: 60000,
    });
    if (pos?.coords) return pos.coords;
  } catch (gpsErr) {
    console.warn("Native GPS high accuracy failed, falling back to network cell tower location:", gpsErr);
  }

  // 2. Fallback to low accuracy (Wi-Fi / Cell tower)
  const pos2 = await Geolocation.getCurrentPosition({
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 300000,
  });
  return pos2.coords;
}

export async function requestBrowserLocation() {
  const isNative = Boolean(
    typeof window !== "undefined" &&
      window.Capacitor &&
      (window.Capacitor.isNativePlatform?.() || window.Capacitor.isNative) &&
      window.Capacitor.Plugins?.Geolocation
  );

  let coords = null;

  if (isNative) {
    try {
      coords = await getNativeCoordinates();
    } catch (nativeErr) {
      console.warn("Native geolocation failed, attempting standard navigator.geolocation:", nativeErr);
    }
  }

  if (!coords) {
    if (!navigator.geolocation) {
      throw new Error("Geolocation is not supported by your browser");
    }
    coords = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve(pos.coords),
        (err) => reject(err),
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 120000,
        }
      );
    });
  }

  const latitude = coords.latitude;
  const longitude = coords.longitude;

  try {
    // Reverse geocode to acquire clean City, State, Country
    const geo = await api.reverseGeocode(latitude, longitude);
    return {
      name: geo.city || geo.name || `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
      state: geo.state || null,
      country: geo.country || "India",
      lat: latitude,
      lon: longitude,
      isApproximate: false,
      source: isNative ? "native-gps" : "geo",
    };
  } catch {
    return {
      name: `${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
      state: null,
      country: "India",
      lat: latitude,
      lon: longitude,
      isApproximate: false,
      source: isNative ? "native-gps" : "geo",
    };
  }
}

export async function getFallbackLocation() {
  // 1. Try IP Geolocation
  try {
    const ipLoc = await api.locateByIp();
    const lat = ipLoc?.latitude ?? ipLoc?.lat;
    const lon = ipLoc?.longitude ?? ipLoc?.lon;
    if (lat != null && lon != null && !isNaN(Number(lat)) && !isNaN(Number(lon))) {
      return {
        name: ipLoc.city || "Current Location",
        state: ipLoc.state || null,
        country: ipLoc.country || "India",
        lat: Number(lat),
        lon: Number(lon),
        isApproximate: true,
        source: "ip",
      };
    }
  } catch (err) {
    console.warn("IP geolocation fallback failed:", err);
  }

  // 2. Try last saved location from store
  const saved = store.get("activeLocation");
  if (saved && saved.lat && saved.lon) {
    return {
      ...saved,
      source: "saved",
    };
  }

  // 3. Configured default city (New Delhi)
  return DEFAULT_FALLBACK;
}
