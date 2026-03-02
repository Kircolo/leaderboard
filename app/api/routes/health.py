from fastapi import APIRouter
from sqlalchemy import text

from app.cache.redis import get_redis_client
from app.core.exceptions import DependencyUnavailableError
from app.db.session import SessionLocal

router = APIRouter()


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))

        redis_client = get_redis_client()
        await redis_client.ping()
    except Exception as exc:
        raise DependencyUnavailableError("Readiness check failed for Postgres or Redis.") from exc

    return {"status": "ok"}
