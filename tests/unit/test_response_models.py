from app.domain import LeaderboardResult, RankedEntry, UserContextResult
from app.schemas.leaderboard import LeaderboardResponse, UserContextResponse


def test_leaderboard_response_accepts_domain_ranked_entries():
    payload = LeaderboardResult(
        game_id="game_1",
        limit=10,
        entries=[RankedEntry(rank=1, user_id="alice", score=100)],
    )

    result = LeaderboardResponse.model_validate(payload)

    assert result.entries[0].user_id == "alice"
    assert result.entries[0].rank == 1


def test_user_context_response_accepts_domain_ranked_entries():
    payload = UserContextResult(
        game_id="game_1",
        user_id="alice",
        rank=1,
        score=100,
        window=2,
        above=[],
        below=[RankedEntry(rank=2, user_id="bob", score=90)],
    )

    result = UserContextResponse.model_validate(payload)

    assert result.below[0].user_id == "bob"
    assert result.below[0].rank == 2
