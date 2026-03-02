from textwrap import dedent


def test_api_contract_examples_are_documented():
    readme = open("/workspaces/leaderboard/README.md", encoding="utf-8").read()

    assert "/v1/games/{game_id}/scores" in readme
    assert "/v1/games/{game_id}/leaderboard" in readme
    assert "/v1/games/{game_id}/users/{user_id}/context" in readme
    assert dedent(
        """
        GET /health/live
        GET /health/ready
        """
    ).strip() in readme

