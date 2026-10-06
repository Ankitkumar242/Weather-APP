/**
 * SkyPulse Client-Side Unit Conversion System
 * The backend API exclusively serves standard metric units.
 * All user-toggled conversions occur on the client with zero network refetches.
 */

export const UNITS = {
  TEMP_C: "C",
  TEMP_F: "F",
  WIND_KMH: "km/h",
  WIND_MPH: "mph",
  WIND_MS: "m/s",
  PRECIP_MM: "mm",
  PRECIP_IN: "in",
  PRESSURE_HPA: "hPa",
  PRESSURE_INHG: "inHg",
};

export function cToF(c) {
  if (c === null || c === undefined) return null;
  return (c * 9) / 5 + 32;
}

export function formatTemp(celsius, unit = UNITS.TEMP_C, withSymbol = true) {
  if (celsius === null || celsius === undefined) return "–";
  const val = unit === UNITS.TEMP_F ? cToF(celsius) : celsius;
  const rounded = Math.round(val);
  return withSymbol ? `${rounded}°${unit}` : `${rounded}°`;
}

export function formatWind(kmh, unit = UNITS.WIND_KMH) {
  if (kmh === null || kmh === undefined) return "–";
  if (unit === UNITS.WIND_MPH) {
    return `${(kmh * 0.621371).toFixed(1)} mph`;
  }
  if (unit === UNITS.WIND_MS) {
    return `${(kmh / 3.6).toFixed(1)} m/s`;
  }
  return `${Math.round(kmh)} km/h`;
}

export function formatPrecip(mm, unit = UNITS.PRECIP_MM) {
  if (mm === null || mm === undefined) return "–";
  if (unit === UNITS.PRECIP_IN) {
    return `${(mm * 0.0393701).toFixed(2)} in`;
  }
  return `${mm.toFixed(1)} mm`;
}

export function formatPressure(hpa, unit = UNITS.PRESSURE_HPA) {
  if (hpa === null || hpa === undefined) return "–";
  if (unit === UNITS.PRESSURE_INHG) {
    return `${(hpa * 0.02953).toFixed(2)} inHg`;
  }
  return `${Math.round(hpa)} hPa`;
}

export function formatDistance(meters) {
  if (meters === null || meters === undefined) return "–";
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${Math.round(meters)} m`;
}
