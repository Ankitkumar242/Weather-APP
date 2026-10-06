/**
 * SkyPulse i18n Translation Engine
 * Supports real-time English and Hindi switching.
 */

import { store } from "./state.js";

let translations = {
  en: {},
  hi: {},
};

export async function initI18n() {
  try {
    const [enRes, hiRes] = await Promise.all([
      fetch("/static/i18n/en.json").then((r) => r.json()),
      fetch("/static/i18n/hi.json").then((r) => r.json()),
    ]);
    translations.en = enRes;
    translations.hi = hiRes;
  } catch (e) {
    console.warn("Could not load i18n dictionaries, using fallbacks:", e);
  }
}

export function t(key, params = {}) {
  const lang = store.get("lang") || "en";
  let text = translations[lang]?.[key] || translations.en?.[key] || key;

  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, v);
  }
  return text;
}

export function tCondition(conditionLabel) {
  if (!conditionLabel) return "–";
  const lang = store.get("lang") || "en";
  if (lang === "en") return conditionLabel;

  const translated = translations.hi?.conditions?.[conditionLabel];
  return translated || conditionLabel;
}

export function getLanguage() {
  return store.get("lang") || "en";
}

export function setLanguage(lang) {
  store.set({ lang });
  document.documentElement.lang = lang;
}
