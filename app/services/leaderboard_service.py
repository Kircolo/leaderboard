from typing import Protocol

from app.core.exceptions import NotFoundError
from app.domain import LeaderboardResult, ScoreRecord, SubmitScoreResult, UserContextResult
from app.services.ranking import build_ranked_entries, competition_rank_from_higher_count


class ScoreRepositoryProtocol(Protocol):
    async def get_score(self, game_id: str, platform: str, user_id: str) -> ScoreRecord | None: ...
    async def upsert_high_score(
        self,
        game_id: str,
        platform: str,
        user_id: str,
        score: int,
    ) -> tuple[ScoreRecord, bool]: ...
    async def get_all_scores_for_game(self, game_id: str) -> list[ScoreRecord]: ...


class LeaderboardCacheRepositoryProtocol(Protocol):
    async def set_score(self, game_id: str, platform: str, user_id: str, score: int) -> None: ...
    async def get_score(self, game_id: str, platform: str, user_id: str) -> int | None: ...
    async def get_top(self, game_id: str, limit: int) -> list[tuple[str, str, int]]: ...
    async def get_all(self, game_id: str) -> list[tuple[str, str, int]]: ...
    async def count_higher_scores(self, game_id: str, score: int) -> int: ...
    async def get_user_position(self, game_id: str, platform: str, user_id: str) -> int | None: ...
    async def get_range_by_position(
        self,
        game_id: str,
        start: int,
        end: int,
    ) -> list[tuple[str, str, int]]: ...
    async def rebuild(self, game_id: str, entries: list[ScoreRecord]) -> None: ...


class LeaderboardService:
    def __init__(
        self,
        score_repository: ScoreRepositoryProtocol,
        cache_repository: LeaderboardCacheRepositoryProtocol,
    ):
        self.score_repository = score_repository
        self.cache_repository = cache_repository

    async def submit_score(
        self,
        game_id: str,
        platform: str,
        user_id: str,
        score: int,
    ) -> SubmitScoreResult:
        record, updated = await self.score_repository.upsert_high_score(
            game_id=game_id,
            platform=platform,
            user_id=user_id,
            score=score,
        )

        if updated:
            await self.cache_repository.set_score(game_id, platform, user_id, record.score)
        else:
            cached_score = await self.cache_repository.get_score(game_id, platform, user_id)
            if cached_score is None:
                await self._rebuild_game_cache(game_id)

        rank = await self._get_rank(game_id, platform, record.user_id, record.score)
        return SubmitScoreResult(
            game_id=game_id,
            platform=platform,
            user_id=user_id,
            submitted_score=score,
            stored_score=record.score,
            updated=updated,
            rank=rank,
        )

    async def get_top_leaderboard(self, game_id: str, limit: int) -> LeaderboardResult:
        entries = await self.cache_repository.get_top(game_id, limit)
        if not entries:
            entries = await self._get_or_rebuild_top(game_id, limit)

        ranked = build_ranked_entries(entries)
        return LeaderboardResult(game_id=game_id, limit=limit, entries=ranked)

    async def get_user_context(
        self,
        game_id: str,
        platform: str,
        user_id: str,
        window: int,
    ) -> UserContextResult:
        cached_score = await self.cache_repository.get_score(game_id, platform, user_id)
        if cached_score is None:
            record = await self.score_repository.get_score(game_id, platform, user_id)
            if record is None:
                message = (
                    f"User '{user_id}' on platform '{platform}' does not have a score "
                    f"for game '{game_id}'."
                )
                raise NotFoundError(message)
            await self._rebuild_game_cache(game_id)
            cached_score = record.score

        entries = await self.cache_repository.get_all(game_id)
        if not entries:
            await self._rebuild_game_cache(game_id)
            entries = await self.cache_repository.get_all(game_id)

        ranked_entries = build_ranked_entries(entries)
        try:
            target_index = next(
                index
                for index, entry in enumerate(ranked_entries)
                if entry.platform == platform and entry.user_id == user_id
            )
        except StopIteration as exc:
            message = (
                f"User '{user_id}' on platform '{platform}' does not have a score "
                f"for game '{game_id}'."
            )
            raise NotFoundError(message) from exc

        start = max(target_index - window, 0)
        end = target_index + window + 1
        above = ranked_entries[start:target_index]
        below = ranked_entries[target_index + 1 : end]

        target_rank = competition_rank_from_higher_count(
            await self.cache_repository.count_higher_scores(game_id, cached_score)
        )

        return UserContextResult(
            game_id=game_id,
            platform=platform,
            user_id=user_id,
            rank=target_rank,
            score=cached_score,
            window=window,
            above=above,
            below=below,
        )

    async def _get_rank(self, game_id: str, platform: str, user_id: str, score: int) -> int:
        cached_score = await self.cache_repository.get_score(game_id, platform, user_id)
        if cached_score is None:
            await self._rebuild_game_cache(game_id)
        higher_count = await self.cache_repository.count_higher_scores(game_id, score)
        return competition_rank_from_higher_count(higher_count)

    async def _get_or_rebuild_top(self, game_id: str, limit: int) -> list[tuple[str, str, int]]:
        records = await self.score_repository.get_all_scores_for_game(game_id)
        if not records:
            return []
        await self.cache_repository.rebuild(game_id, records)
        return [(record.platform, record.user_id, record.score) for record in records[:limit]]

    async def _rebuild_game_cache(self, game_id: str) -> None:
        records = await self.score_repository.get_all_scores_for_game(game_id)
        await self.cache_repository.rebuild(game_id, records)
