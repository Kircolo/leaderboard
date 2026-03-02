from collections.abc import Iterable

from redis.asyncio import Redis

from app.domain import ScoreRecord


class RedisLeaderboardCacheRepository:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @staticmethod
    def _key(game_id: str) -> str:
        return f"leaderboard:{game_id}"

    async def set_score(self, game_id: str, user_id: str, score: int) -> None:
        await self.redis.zadd(self._key(game_id), {user_id: score})

    async def get_score(self, game_id: str, user_id: str) -> int | None:
        score = await self.redis.zscore(self._key(game_id), user_id)
        if score is None:
            return None
        return int(score)

    async def get_top(self, game_id: str, limit: int) -> list[tuple[str, int]]:
        entries = await self.redis.zrevrange(self._key(game_id), 0, limit - 1, withscores=True)
        return [(user_id, int(score)) for user_id, score in entries]

    async def get_all(self, game_id: str) -> list[tuple[str, int]]:
        entries = await self.redis.zrevrange(self._key(game_id), 0, -1, withscores=True)
        return [(user_id, int(score)) for user_id, score in entries]

    async def count_higher_scores(self, game_id: str, score: int) -> int:
        return int(await self.redis.zcount(self._key(game_id), f"({score}", "+inf"))

    async def get_user_position(self, game_id: str, user_id: str) -> int | None:
        position = await self.redis.zrevrank(self._key(game_id), user_id)
        return None if position is None else int(position)

    async def get_range_by_position(
        self,
        game_id: str,
        start: int,
        end: int,
    ) -> list[tuple[str, int]]:
        if end < start:
            return []
        entries = await self.redis.zrevrange(self._key(game_id), start, end, withscores=True)
        return [(user_id, int(score)) for user_id, score in entries]

    async def rebuild(self, game_id: str, entries: Iterable[ScoreRecord]) -> None:
        key = self._key(game_id)
        payload = {entry.user_id: entry.score for entry in entries}
        async with self.redis.pipeline(transaction=True) as pipeline:
            await pipeline.delete(key)
            if payload:
                await pipeline.zadd(key, payload)
            await pipeline.execute()
