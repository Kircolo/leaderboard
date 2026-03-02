from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def close_redis() -> None:
    client = get_redis_client()
    await client.aclose()
    get_redis_client.cache_clear()

