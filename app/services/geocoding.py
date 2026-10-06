"""Geocoding search service with Open-Meteo Geocoding API and state name normalization."""

from __future__ import annotations

import re
from typing import Any

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.http import resilient_request
from app.models.schemas import PlaceSearchResult

settings = get_settings()

STATE_ALIASES: dict[str, str] = {
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    "pondicherry": "Puducherry",
    "national capital territory of delhi": "Delhi",
    "nct of delhi": "Delhi",
    "delhi": "Delhi",
    "andaman and nicobar islands": "Andaman & Nicobar Islands",
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "dadra and nagar haveli and daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
    "dadra & nagar haveli and daman & diu": "Dadra & Nagar Haveli and Daman & Diu",
    "jammu and kashmir": "Jammu & Kashmir",
    "jammu & kashmir": "Jammu & Kashmir",
}


def normalize_state_name(state: str | None) -> str | None:
    """Normalize state variations to canonical dataset names."""
    if not state:
        return None
    cleaned = re.sub(r"\s+", " ", state.strip().lower())
    return STATE_ALIASES.get(cleaned, state.strip())


async def search_places(query: str, state_filter: str | None = None) -> list[PlaceSearchResult]:
    """
    Search places worldwide via Open-Meteo Geocoding API.
    Optionally filter results by state name (admin1 match).
    Cached for 24h.
    """
    q_clean = query.strip()
    if len(q_clean) < 2:
        return []

    cache_key = f"{q_clean.lower()}:{state_filter or ''}"

    async def _fetch() -> list[dict[str, Any]]:
        params = {
            "name": q_clean,
            "count": 15,
            "language": "en",
        }
        res = await resilient_request("GET", settings.open_meteo_geocoding_url, params=params)
        if res.status_code != 200:
            return []
        data = res.json()
        return data.get("results", [])

    raw_results, _ = await cache_manager.get_or_set_coalesced("search", cache_key, _fetch)

    output: list[PlaceSearchResult] = []
    norm_state = normalize_state_name(state_filter)
    norm_filter = norm_state.lower() if norm_state else None

    for r in raw_results:
        raw_admin1 = r.get("admin1")
        norm_admin1 = normalize_state_name(raw_admin1)

        # If state filter is specified, only include matching state
        if norm_filter and (not norm_admin1 or norm_admin1.lower() != norm_filter):
            continue

        output.append(
            PlaceSearchResult(
                id=r.get("id"),
                name=r.get("name", ""),
                admin1=norm_admin1,
                country=r.get("country", ""),
                country_code=r.get("country_code"),
                latitude=float(r.get("latitude", 0.0)),
                longitude=float(r.get("longitude", 0.0)),
                population=r.get("population"),
                timezone=r.get("timezone"),
            )
        )

    return output
