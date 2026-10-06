"""Search API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.core.ratelimit import limiter
from app.models.schemas import PlaceSearchResult
from app.services.geocoding import search_places

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[PlaceSearchResult])
@limiter.limit("60/minute")
async def search_locations(
    request: Request,
    q: str = Query(..., min_length=2, max_length=80, description="City or place search query"),
    state: str | None = Query(None, description="Optional state filter"),
) -> list[PlaceSearchResult]:
    """Search worldwide places with optional state constraint."""
    return await search_places(query=q, state_filter=state)
