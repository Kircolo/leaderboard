from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


SessionLocal = async_sessionmaker(bind=get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def close_engine() -> None:
    await get_engine().dispose()
    get_engine.cache_clear()

