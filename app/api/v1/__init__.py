"""API v1 routers."""

from fastapi import APIRouter

from app.api.v1.locate import router as locate_router
from app.api.v1.search import router as search_router
from app.api.v1.states import router as states_router
from app.api.v1.weather import router as weather_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(weather_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(locate_router)
api_v1_router.include_router(states_router)
