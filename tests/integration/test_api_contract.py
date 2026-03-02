from pathlib import Path
from textwrap import dedent


def test_api_contract_examples_are_documented():
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")

    assert "/games/{game_id}/scores" in readme
    assert "/games/{game_id}/leaderboard" in readme
    assert "/games/{game_id}/platforms/{platform}/users/{user_id}/context" in readme
    assert dedent(
        """
        GET /health/live
        GET /health/ready
        """
    ).strip() in readme
