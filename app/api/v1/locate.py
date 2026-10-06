"""Location and utility API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Query, Request

from app.core.ratelimit import limiter
from app.models.schemas import HealthResponse, IPLocationResponse, ReverseGeoResponse
from app.services.ip_locate import locate_by_ip
from app.services.reverse_geo import reverse_geocode

router = APIRouter(tags=["locate"])


@router.get("/reverse", response_model=ReverseGeoResponse)
@limiter.limit("60/minute")
async def get_reverse_geocode(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
) -> ReverseGeoResponse:
    """Reverse geocode coordinates to City, State, Country via OSM Nominatim."""
    return await reverse_geocode(lat, lon)


@router.get("/locate/ip", response_model=IPLocationResponse)
@limiter.limit("60/minute")
async def get_ip_location(request: Request) -> IPLocationResponse:
    """Approximate location based on client IP."""
    client_ip = request.client.host if request.client else None
    return await locate_by_ip(client_ip)


@router.get("/healthz", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC).isoformat(),
        version="0.1.0",
    )
