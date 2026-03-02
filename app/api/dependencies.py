from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import get_redis_client
from app.db.session import get_db_session
from app.repositories.leaderboard_cache_repository import RedisLeaderboardCacheRepository
from app.repositories.score_repository import SqlAlchemyScoreRepository
from app.services.leaderboard_service import LeaderboardService


async def get_session() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


async def get_leaderboard_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LeaderboardService:
    redis_client = get_redis_client()
    score_repository = SqlAlchemyScoreRepository(session)
    cache_repository = RedisLeaderboardCacheRepository(redis_client)
    return LeaderboardService(score_repository=score_repository, cache_repository=cache_repository)
