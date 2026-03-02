from dataclasses import replace
from datetime import UTC, datetime
import asyncio

from app.core.exceptions import NotFoundError
from app.domain import ScoreRecord
from app.services.leaderboard_service import LeaderboardService


def make_record(game_id: str, user_id: str, score: int) -> ScoreRecord:
    now = datetime.now(UTC)
    return ScoreRecord(
        game_id=game_id,
        user_id=user_id,
        score=score,
        created_at=now,
        updated_at=now,
        last_submitted_at=now,
    )


class FakeScoreRepository:
    def __init__(self, records: dict[tuple[str, str], ScoreRecord] | None = None):
        self.records = records or {}

    async def get_score(self, game_id: str, user_id: str) -> ScoreRecord | None:
        return self.records.get((game_id, user_id))

    async def create_score(self, game_id: str, user_id: str, score: int) -> ScoreRecord:
        record = make_record(game_id, user_id, score)
        self.records[(game_id, user_id)] = record
        return record

    async def update_score(self, game_id: str, user_id: str, score: int) -> ScoreRecord:
        existing = self.records[(game_id, user_id)]
        updated = replace(existing, score=score, updated_at=datetime.now(UTC), last_submitted_at=datetime.now(UTC))
        self.records[(game_id, user_id)] = updated
        return updated

    async def touch_submission(self, game_id: str, user_id: str) -> ScoreRecord:
        existing = self.records[(game_id, user_id)]
        updated = replace(existing, last_submitted_at=datetime.now(UTC))
        self.records[(game_id, user_id)] = updated
        return updated

    async def get_all_scores_for_game(self, game_id: str) -> list[ScoreRecord]:
        return sorted(
            [record for record in self.records.values() if record.game_id == game_id],
            key=lambda record: (-record.score, record.user_id),
        )


class FakeCacheRepository:
    def __init__(self):
        self.boards: dict[str, dict[str, int]] = {}

    async def set_score(self, game_id: str, user_id: str, score: int) -> None:
        self.boards.setdefault(game_id, {})[user_id] = score

    async def get_score(self, game_id: str, user_id: str) -> int | None:
        return self.boards.get(game_id, {}).get(user_id)

    async def get_top(self, game_id: str, limit: int) -> list[tuple[str, int]]:
        return self._ordered(game_id)[:limit]

    async def get_all(self, game_id: str) -> list[tuple[str, int]]:
        return self._ordered(game_id)

    async def count_higher_scores(self, game_id: str, score: int) -> int:
        return sum(1 for _, current_score in self._ordered(game_id) if current_score > score)

    async def get_user_position(self, game_id: str, user_id: str) -> int | None:
        for index, (member, _) in enumerate(self._ordered(game_id)):
            if member == user_id:
                return index
        return None

    async def get_range_by_position(self, game_id: str, start: int, end: int) -> list[tuple[str, int]]:
        return self._ordered(game_id)[start : end + 1]

    async def rebuild(self, game_id: str, entries: list[ScoreRecord]) -> None:
        self.boards[game_id] = {entry.user_id: entry.score for entry in entries}

    def _ordered(self, game_id: str) -> list[tuple[str, int]]:
        board = self.boards.get(game_id, {})
        return sorted(board.items(), key=lambda item: (-item[1], item[0]))


def test_submit_score_keeps_highest_score():
    score_repository = FakeScoreRepository({("game-1", "alice"): make_record("game-1", "alice", 100)})
    cache_repository = FakeCacheRepository()
    asyncio.run(cache_repository.set_score("game-1", "alice", 100))
    service = LeaderboardService(score_repository=score_repository, cache_repository=cache_repository)

    result = asyncio.run(service.submit_score("game-1", "alice", 90))

    assert result.updated is False
    assert result.stored_score == 100
    assert result.rank == 1


def test_get_top_leaderboard_rebuilds_cache_when_missing():
    score_repository = FakeScoreRepository(
        {
            ("game-1", "alice"): make_record("game-1", "alice", 100),
            ("game-1", "bob"): make_record("game-1", "bob", 90),
        }
    )
    cache_repository = FakeCacheRepository()
    service = LeaderboardService(score_repository=score_repository, cache_repository=cache_repository)

    result = asyncio.run(service.get_top_leaderboard("game-1", 10))

    assert [(entry.user_id, entry.rank) for entry in result.entries] == [("alice", 1), ("bob", 2)]


def test_get_user_context_raises_not_found_for_unknown_user():
    service = LeaderboardService(score_repository=FakeScoreRepository(), cache_repository=FakeCacheRepository())

    try:
        asyncio.run(service.get_user_context("game-1", "missing", 2))
    except NotFoundError:
        return

    raise AssertionError("Expected NotFoundError to be raised")
