import asyncio
from dataclasses import replace
from datetime import UTC, datetime

from app.core.exceptions import NotFoundError
from app.domain import ScoreRecord
from app.services.leaderboard_service import LeaderboardService


def make_record(game_id: str, platform: str, user_id: str, score: int) -> ScoreRecord:
    now = datetime.now(UTC)
    return ScoreRecord(
        game_id=game_id,
        platform=platform,
        user_id=user_id,
        score=score,
        created_at=now,
        updated_at=now,
        last_submitted_at=now,
    )


class FakeScoreRepository:
    def __init__(self, records: dict[tuple[str, str, str], ScoreRecord] | None = None):
        self.records = records or {}

    async def get_score(self, game_id: str, platform: str, user_id: str) -> ScoreRecord | None:
        return self.records.get((game_id, platform, user_id))

    async def upsert_high_score(
        self,
        game_id: str,
        platform: str,
        user_id: str,
        score: int,
    ) -> tuple[ScoreRecord, bool]:
        existing = self.records.get((game_id, platform, user_id))
        if existing is None:
            record = make_record(game_id, platform, user_id, score)
            self.records[(game_id, platform, user_id)] = record
            return record, True

        if score > existing.score:
            updated = replace(
                existing,
                score=score,
                updated_at=datetime.now(UTC),
                last_submitted_at=datetime.now(UTC),
            )
            self.records[(game_id, platform, user_id)] = updated
            return updated, True

        touched = replace(existing, last_submitted_at=datetime.now(UTC))
        self.records[(game_id, platform, user_id)] = touched
        return touched, False

    async def get_all_scores_for_game(self, game_id: str) -> list[ScoreRecord]:
        return sorted(
            [record for record in self.records.values() if record.game_id == game_id],
            key=lambda record: (-record.score, record.platform, record.user_id),
        )


class FakeCacheRepository:
    def __init__(self):
        self.boards: dict[str, dict[tuple[str, str], int]] = {}

    async def set_score(self, game_id: str, platform: str, user_id: str, score: int) -> None:
        self.boards.setdefault(game_id, {})[(platform, user_id)] = score

    async def get_score(self, game_id: str, platform: str, user_id: str) -> int | None:
        return self.boards.get(game_id, {}).get((platform, user_id))

    async def get_top(self, game_id: str, limit: int) -> list[tuple[str, str, int]]:
        return self._ordered(game_id)[:limit]

    async def get_all(self, game_id: str) -> list[tuple[str, str, int]]:
        return self._ordered(game_id)

    async def count_higher_scores(self, game_id: str, score: int) -> int:
        return sum(1 for _, _, current_score in self._ordered(game_id) if current_score > score)

    async def get_user_position(self, game_id: str, platform: str, user_id: str) -> int | None:
        for index, (entry_platform, entry_user_id, _) in enumerate(self._ordered(game_id)):
            if entry_platform == platform and entry_user_id == user_id:
                return index
        return None

    async def get_range_by_position(
        self,
        game_id: str,
        start: int,
        end: int,
    ) -> list[tuple[str, str, int]]:
        return self._ordered(game_id)[start : end + 1]

    async def rebuild(self, game_id: str, entries: list[ScoreRecord]) -> None:
        self.boards[game_id] = {
            (entry.platform, entry.user_id): entry.score
            for entry in entries
        }

    def _ordered(self, game_id: str) -> list[tuple[str, str, int]]:
        board = self.boards.get(game_id, {})
        ordered = sorted(board.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        return [(platform, user_id, score) for (platform, user_id), score in ordered]


def test_submit_score_keeps_highest_score():
    score_repository = FakeScoreRepository(
        {("game-1", "steam", "alice"): make_record("game-1", "steam", "alice", 100)}
    )
    cache_repository = FakeCacheRepository()
    asyncio.run(cache_repository.set_score("game-1", "steam", "alice", 100))
    service = LeaderboardService(
        score_repository=score_repository,
        cache_repository=cache_repository,
    )

    result = asyncio.run(service.submit_score("game-1", "steam", "alice", 90))

    assert result.updated is False
    assert result.platform == "steam"
    assert result.stored_score == 100
    assert result.rank == 1


def test_submit_score_creates_new_record_when_user_is_new():
    service = LeaderboardService(
        score_repository=FakeScoreRepository(),
        cache_repository=FakeCacheRepository(),
    )

    result = asyncio.run(service.submit_score("game-1", "steam", "alice", 100))

    assert result.updated is True
    assert result.platform == "steam"
    assert result.stored_score == 100
    assert result.rank == 1


def test_get_top_leaderboard_rebuilds_cache_when_missing():
    score_repository = FakeScoreRepository(
        {
            ("game-1", "steam", "alice"): make_record("game-1", "steam", "alice", 100),
            ("game-1", "psn", "bob"): make_record("game-1", "psn", "bob", 90),
        }
    )
    cache_repository = FakeCacheRepository()
    service = LeaderboardService(
        score_repository=score_repository,
        cache_repository=cache_repository,
    )

    result = asyncio.run(service.get_top_leaderboard("game-1", 10))

    assert [(entry.platform, entry.user_id, entry.rank) for entry in result.entries] == [
        ("steam", "alice", 1),
        ("psn", "bob", 2),
    ]


def test_submit_score_treats_same_user_id_on_different_platforms_as_distinct():
    score_repository = FakeScoreRepository(
        {("game-1", "steam", "alice"): make_record("game-1", "steam", "alice", 100)}
    )
    cache_repository = FakeCacheRepository()
    asyncio.run(cache_repository.set_score("game-1", "steam", "alice", 100))
    service = LeaderboardService(
        score_repository=score_repository,
        cache_repository=cache_repository,
    )

    result = asyncio.run(service.submit_score("game-1", "xbox", "alice", 80))

    assert result.updated is True
    assert result.platform == "xbox"
    assert result.rank == 2


def test_get_user_context_raises_not_found_for_unknown_user():
    service = LeaderboardService(
        score_repository=FakeScoreRepository(),
        cache_repository=FakeCacheRepository(),
    )

    try:
        asyncio.run(service.get_user_context("game-1", "steam", "missing", 2))
    except NotFoundError:
        return

    raise AssertionError("Expected NotFoundError to be raised")
