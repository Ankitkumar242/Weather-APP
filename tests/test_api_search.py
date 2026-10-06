"""Integration tests for /api/v1/search endpoint."""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient, Response

from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
@respx.mock
async def test_search_endpoint_success(async_client: AsyncClient) -> None:
    mock_search = {
        "results": [
            {
                "id": 1269843,
                "name": "Jaipur",
                "latitude": 26.9124,
                "longitude": 75.7873,
                "country": "India",
                "admin1": "Rajasthan",
            }
        ]
    }
    respx.get(settings.open_meteo_geocoding_url).mock(
        return_value=Response(200, json=mock_search)
    )

    resp = await async_client.get("/api/v1/search", params={"q": "Jaipur"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Jaipur"
    assert data[0]["admin1"] == "Rajasthan"


@pytest.mark.asyncio
async def test_search_endpoint_validation_error(async_client: AsyncClient) -> None:
    # Query too short (< 2 chars)
    resp = await async_client.get("/api/v1/search", params={"q": "a"})
    assert resp.status_code == 422
