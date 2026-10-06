/**
 * SkyPulse Geolocation Orchestrator
 * Coordinates browser navigator.geolocation, IP fallback, and default location flows.
 */

import { api } from "./api.js";
import { store } from "./state.js";

const DEFAULT_FALLBACK = {
  name: "New Delhi",
  state: "Delhi",
  country: "India",
  lat: 28.6139,
  lon: 77.2090,
  isApproximate: false,
  source: "default",
};

async function getNativeCoordinates() {
  const Geolocation = window.Capacitor?.Plugins?.Geolocation;
  if (!Geolocation) {
    throw new Error("Capacitor Geolocation plugin unavailable");
  }
  try {
    const permStatus = await Geolocation.checkPermissions();
    if (permStatus?.location !== "granted") {
      await Geolocation.requestPermissions();
    }
  } catch (err) {
    console.warn("Capacitor permissions request note:", err);
  }
  const pos = await Geolocation.getCurrentPosition({
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 600000,
  });
  return pos.coords;
}

export async function requestBrowserLocation() {
  const isNative = Boolean(
    typeof window !== "undefined" &&
    window.Capacitor &&
    (window.Capacitor.isNativePlatform?.() || window.Capacitor.isNative) &&
    window.Capacitor.Plugins?.Geolocation
  );

  let coords;
  if (isNative) {
    coords = await getNativeCoordinates();
  } else {
    if (!navigator.geolocation) {
      throw new Error("Geolocation is not supported by your browser");
    }
    coords = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve(pos.coords),
        (err) => reject(err),
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 600000, // 10 minutes cache
        }
      );
    });
  }

  const { latitude, longitude } = coords;
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
    if (ipLoc && ipLoc.latitude && ipLoc.longitude) {
      return {
        name: ipLoc.city,
        state: ipLoc.state,
        country: ipLoc.country,
        lat: ipLoc.latitude,
        lon: ipLoc.longitude,
        isApproximate: true,
        source: "ip",
      };
    }
  } catch {
    // Continue to saved or default
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
