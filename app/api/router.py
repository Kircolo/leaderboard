from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.leaderboard import router as leaderboard_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(leaderboard_router, prefix="/v1", tags=["leaderboard"])

