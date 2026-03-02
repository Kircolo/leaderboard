from collections.abc import Iterable

from redis.asyncio import Redis

from app.domain import ScoreRecord


class RedisLeaderboardCacheRepository:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @staticmethod
    def _key(game_id: str) -> str:
        return f"leaderboard:{game_id}"

    @staticmethod
    def _member(platform: str, user_id: str) -> str:
        return f"{platform}|{user_id}"

    @staticmethod
    def _parse_member(member: str) -> tuple[str, str]:
        platform, user_id = member.split("|", maxsplit=1)
        return platform, user_id

    async def set_score(self, game_id: str, platform: str, user_id: str, score: int) -> None:
        member = self._member(platform, user_id)
        await self.redis.zadd(self._key(game_id), {member: score})

    async def get_score(self, game_id: str, platform: str, user_id: str) -> int | None:
        member = self._member(platform, user_id)
        score = await self.redis.zscore(self._key(game_id), member)
        if score is None:
            return None
        return int(score)

    async def get_top(self, game_id: str, limit: int) -> list[tuple[str, str, int]]:
        entries = await self.redis.zrevrange(self._key(game_id), 0, limit - 1, withscores=True)
        return [(*self._parse_member(member), int(score)) for member, score in entries]

    async def get_all(self, game_id: str) -> list[tuple[str, str, int]]:
        entries = await self.redis.zrevrange(self._key(game_id), 0, -1, withscores=True)
        return [(*self._parse_member(member), int(score)) for member, score in entries]

    async def count_higher_scores(self, game_id: str, score: int) -> int:
        return int(await self.redis.zcount(self._key(game_id), f"({score}", "+inf"))

    async def get_user_position(self, game_id: str, platform: str, user_id: str) -> int | None:
        member = self._member(platform, user_id)
        position = await self.redis.zrevrank(self._key(game_id), member)
        return None if position is None else int(position)

    async def get_range_by_position(
        self,
        game_id: str,
        start: int,
        end: int,
    ) -> list[tuple[str, str, int]]:
        if end < start:
            return []
        entries = await self.redis.zrevrange(self._key(game_id), start, end, withscores=True)
        return [(*self._parse_member(member), int(score)) for member, score in entries]

    async def rebuild(self, game_id: str, entries: Iterable[ScoreRecord]) -> None:
        key = self._key(game_id)
        payload = {
            self._member(entry.platform, entry.user_id): entry.score
            for entry in entries
        }
        async with self.redis.pipeline(transaction=True) as pipeline:
            await pipeline.delete(key)
            if payload:
                await pipeline.zadd(key, payload)
            await pipeline.execute()
