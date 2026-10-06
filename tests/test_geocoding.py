"""Tests for geocoding search service and state alias normalization."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import get_settings
from app.services.geocoding import normalize_state_name, search_places

settings = get_settings()


def test_normalize_state_name() -> None:
    assert normalize_state_name("Orissa") == "Odisha"
    assert normalize_state_name("Uttaranchal") == "Uttarakhand"
    assert normalize_state_name("Pondicherry") == "Puducherry"
    assert normalize_state_name("National Capital Territory of Delhi") == "Delhi"
    assert normalize_state_name("NCT of Delhi") == "Delhi"
    assert normalize_state_name("Rajasthan") == "Rajasthan"
    assert normalize_state_name(None) is None


@pytest.mark.asyncio
@respx.mock
async def test_search_places_with_state_filter() -> None:
    mock_search = {
        "results": [
            {
                "id": 1273294,
                "name": "Delhi",
                "latitude": 28.65,
                "longitude": 77.23,
                "country": "India",
                "admin1": "National Capital Territory of Delhi",
                "population": 11000000,
            },
            {
                "id": 9999999,
                "name": "Delhi",
                "latitude": 42.0,
                "longitude": -75.0,
                "country": "United States",
                "admin1": "New York",
                "population": 3000,
            },
        ]
    }

    respx.get(settings.open_meteo_geocoding_url).mock(
        return_value=Response(200, json=mock_search)
    )

    # Search with state filter "Delhi" -> should filter out New York
    results = await search_places(query="Delhi", state_filter="Delhi")
    assert len(results) == 1
    assert results[0].name == "Delhi"
    assert results[0].admin1 == "Delhi"  # normalized
    assert results[0].country == "India"
