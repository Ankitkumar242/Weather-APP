/**
 * SkyPulse Weather Icons Library
 * High-quality custom inline SVGs for WMO weather codes and UI actions.
 */

export function getWeatherIconSvg(code, isDay = 1, size = 48) {
  const isNight = isDay === 0;

  // Clear Sky
  if (code === 0) {
    if (isNight) {
      return `
        <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 6C13.82 7.73 8.5 14.18 8.5 21.9C8.5 31.07 15.93 38.5 25.1 38.5C32.82 38.5 39.27 33.18 41 26C39.42 26.33 37.78 26.5 36.1 26.5C26.16 26.5 18.1 18.44 18.1 8.5C18.1 6.82 18.27 5.18 18.6 3.6" fill="#FDE047" stroke="#EAB308" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
    }
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="24" cy="24" r="10" fill="#FBBF24" stroke="#F59E0B" stroke-width="2"/>
        <line x1="24" y1="4" x2="24" y2="8" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="24" y1="40" x2="24" y2="44" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="4" y1="24" x2="8" y2="24" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="40" y1="24" x2="44" y2="24" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="9.86" y1="9.86" x2="12.69" y2="12.69" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="35.31" y1="35.31" x2="38.14" y2="38.14" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="9.86" y1="38.14" x2="12.69" y2="35.31" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="35.31" y1="12.69" x2="38.14" y2="9.86" stroke="#F59E0B" stroke-width="2.5" stroke-linecap="round"/>
      </svg>`;
  }

  // Mainly Clear / Partly Cloudy (1, 2)
  if (code === 1 || code === 2) {
    if (isNight) {
      return `
        <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 8C14.5 9.5 11 13.8 11 19C11 25.6 16.4 31 23 31C28.2 31 32.5 27.5 34 23C32.8 23.2 31.5 23.3 30.2 23.3C22.4 23.3 16.1 17 16.1 9.2C16.1 7.9 16.2 6.6 16.4 5.4" fill="#FDE047"/>
          <path d="M18 36H36C39.3 36 42 33.3 42 30C42 26.9 39.7 24.4 36.7 24.1C35.9 19.5 31.9 16 27 16C22.6 16 18.9 18.8 17.6 22.8C14.5 23.4 12 26.1 12 29.5C12 33.1 14.7 36 18 36Z" fill="#CBD5E1" stroke="#94A3B8" stroke-width="2" stroke-linejoin="round"/>
        </svg>`;
    }
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="18" cy="18" r="8" fill="#FBBF24" stroke="#F59E0B" stroke-width="2"/>
        <path d="M18 38H36C39.3 38 42 35.3 42 32C42 28.9 39.7 26.4 36.7 26.1C35.9 21.5 31.9 18 27 18C22.6 18 18.9 20.8 17.6 24.8C14.5 25.4 12 28.1 12 31.5C12 35.1 14.7 38 18 38Z" fill="#E2E8F0" stroke="#94A3B8" stroke-width="2" stroke-linejoin="round"/>
      </svg>`;
  }

  // Overcast (3)
  if (code === 3) {
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 28H34C37.3 28 40 25.3 40 22C40 18.9 37.7 16.4 34.7 16.1C33.9 11.5 29.9 8 25 8C20.6 8 16.9 10.8 15.6 14.8C12.5 15.4 10 18.1 10 21.5C10 25.1 12.7 28 16 28Z" fill="#94A3B8"/>
        <path d="M18 38H36C39.3 38 42 35.3 42 32C42 28.9 39.7 26.4 36.7 26.1C35.9 21.5 31.9 18 27 18C22.6 18 18.9 20.8 17.6 24.8C14.5 25.4 12 28.1 12 31.5C12 35.1 14.7 38 18 38Z" fill="#CBD5E1" stroke="#64748B" stroke-width="2"/>
      </svg>`;
  }

  // Fog / Rime Fog (45, 48)
  if (code === 45 || code === 48) {
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 22H34C36.8 22 39 19.8 39 17C39 14.4 37 12.3 34.4 12.1C33.7 8.3 30.3 5.3 26.3 5.3C22.6 5.3 19.5 7.7 18.4 11C15.8 11.5 13.7 13.8 13.7 16.6C13.7 19.6 16 22 19 22Z" fill="#CBD5E1"/>
        <line x1="10" y1="28" x2="38" y2="28" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="14" y1="34" x2="34" y2="34" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="12" y1="40" x2="36" y2="40" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round"/>
      </svg>`;
  }

  // Drizzle (51, 53, 55, 56, 57)
  if ((code >= 51 && code <= 57)) {
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 30H36C39.3 30 42 27.3 42 24C42 20.9 39.7 18.4 36.7 18.1C35.9 13.5 31.9 10 27 10C22.6 10 18.9 12.8 17.6 16.8C14.5 17.4 12 20.1 12 23.5C12 27.1 14.7 30 18 30Z" fill="#94A3B8" stroke="#64748B" stroke-width="2"/>
        <line x1="18" y1="34" x2="16" y2="38" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="26" y1="34" x2="24" y2="38" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="34" y1="34" x2="32" y2="38" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round"/>
      </svg>`;
  }

  // Rain / Rain Showers (61, 63, 65, 66, 67, 80, 81, 82)
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) {
    const isHeavy = code === 65 || code === 82;
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 28H36C39.3 28 42 25.3 42 22C42 18.9 39.7 16.4 36.7 16.1C35.9 11.5 31.9 8 27 8C22.6 8 18.9 10.8 17.6 14.8C14.5 15.4 12 18.1 12 21.5C12 25.1 14.7 28 18 28Z" fill="#64748B" stroke="#475569" stroke-width="2"/>
        <line x1="18" y1="33" x2="14" y2="42" stroke="#2563EB" stroke-width="${isHeavy ? 3.5 : 2.5}" stroke-linecap="round"/>
        <line x1="26" y1="33" x2="22" y2="42" stroke="#2563EB" stroke-width="${isHeavy ? 3.5 : 2.5}" stroke-linecap="round"/>
        <line x1="34" y1="33" x2="30" y2="42" stroke="#2563EB" stroke-width="${isHeavy ? 3.5 : 2.5}" stroke-linecap="round"/>
      </svg>`;
  }

  // Snow / Snow Showers (71, 73, 75, 77, 85, 86)
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) {
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 28H36C39.3 28 42 25.3 42 22C42 18.9 39.7 16.4 36.7 16.1C35.9 11.5 31.9 8 27 8C22.6 8 18.9 10.8 17.6 14.8C14.5 15.4 12 18.1 12 21.5C12 25.1 14.7 28 18 28Z" fill="#CBD5E1" stroke="#94A3B8" stroke-width="2"/>
        <circle cx="18" cy="35" r="2" fill="#E2E8F0"/>
        <circle cx="27" cy="35" r="2" fill="#E2E8F0"/>
        <circle cx="34" cy="35" r="2" fill="#E2E8F0"/>
        <circle cx="22" cy="41" r="2" fill="#E2E8F0"/>
        <circle cx="30" cy="41" r="2" fill="#E2E8F0"/>
      </svg>`;
  }

  // Thunderstorm (95, 96, 99)
  if (code === 95 || code === 96 || code === 99) {
    return `
      <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 26H36C39.3 26 42 23.3 42 20C42 16.9 39.7 14.4 36.7 14.1C35.9 9.5 31.9 6 27 6C22.6 6 18.9 8.8 17.6 12.8C14.5 13.4 12 16.1 12 19.5C12 23.1 14.7 26 18 26Z" fill="#334155" stroke="#1E293B" stroke-width="2"/>
        <path d="M25 24L18 34H26L23 44L33 32H25L27 24H25Z" fill="#FACC15" stroke="#EAB308" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>`;
  }

  // Fallback icon
  return `
    <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="10" stroke="#94A3B8" stroke-width="2.5"/>
    </svg>`;
}

export const UI_ICONS = {
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
  mapPin: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`,
  star: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`,
  starFilled: `<svg viewBox="0 0 24 24" fill="#FBBF24" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`,
  wind: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path></svg>`,
  droplet: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>`,
  eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`,
  gauge: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="m14 10-3 3"></path><line x1="12" y1="3" x2="12" y2="5"></line></svg>`,
  sunRays: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`,
  sunrise: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 18a5 5 0 0 0-10 0"></path><line x1="12" y1="2" x2="12" y2="9"></line><line x1="4.22" y1="10.22" x2="5.64" y2="11.64"></line><line x1="1" y1="18" x2="3" y2="18"></line><line x1="21" y1="18" x2="23" y2="18"></line><line x1="18.36" y1="11.64" x2="19.78" y2="10.22"></line><line x1="23" y1="22" x2="1" y2="22"></line><polyline points="8 6 12 2 16 6"></polyline></svg>`,
  sunset: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 18a5 5 0 0 0-10 0"></path><line x1="12" y1="9" x2="12" y2="2"></line><line x1="4.22" y1="10.22" x2="5.64" y2="11.64"></line><line x1="1" y1="18" x2="3" y2="18"></line><line x1="21" y1="18" x2="23" y2="18"></line><line x1="18.36" y1="11.64" x2="19.78" y2="10.22"></line><line x1="23" y1="22" x2="1" y2="22"></line><polyline points="16 5 12 9 8 5"></polyline></svg>`,
  calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`,
  map: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>`,
  close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
};
