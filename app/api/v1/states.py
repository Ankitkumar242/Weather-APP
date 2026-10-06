"""State and regional weather endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Path, Request

from app.core.ratelimit import limiter
from app.models.schemas import (
    CityItem,
    CountryOverviewResponse,
    StateOverviewResponse,
    StateSummary,
)
from app.services.aggregate import (
    compute_country_overview,
    compute_state_overview,
    get_all_states,
    get_state_by_slug,
)

router = APIRouter(tags=["states"])


@router.get("/states", response_model=list[StateSummary])
async def list_states() -> list[StateSummary]:
    """List all 36 Indian States and Union Territories with capitals and city lists."""
    return get_all_states()


@router.get("/states/{slug}/cities", response_model=list[CityItem])
async def list_state_cities(
    slug: str = Path(..., description="Kebab-case state slug"),
) -> list[CityItem]:
    """Get list of key cities in a state (capital first)."""
    state = get_state_by_slug(slug)
    return state.cities


@router.get("/states/{slug}/overview", response_model=StateOverviewResponse)
@limiter.limit("60/minute")
async def get_state_overview(
    request: Request,
    slug: str = Path(..., description="Kebab-case state slug"),
) -> StateOverviewResponse:
    """
    Get full state dashboard data in ONE batched Open-Meteo call:
    - Current weather for each major city
    - 15-day average trend across the state's cities
    """
    return await compute_state_overview(slug)


@router.get("/overview/country/in", response_model=CountryOverviewResponse)
@limiter.limit("60/minute")
async def get_all_india_overview(request: Request) -> CountryOverviewResponse:
    """
    Get All-India capitals overview in ONE batched request:
    - Weather for all 36 state & UT capitals
    - Highlights: hottest, coldest, and wettest capital
    """
    return await compute_country_overview()
