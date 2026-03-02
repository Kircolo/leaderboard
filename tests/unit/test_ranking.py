from app.services.ranking import build_ranked_entries, competition_rank_from_higher_count


def test_build_ranked_entries_uses_competition_ranking():
    ranked = build_ranked_entries(
        [
            ("alice", 100),
            ("bob", 95),
            ("carol", 95),
            ("dave", 80),
        ]
    )

    assert [(entry.user_id, entry.rank) for entry in ranked] == [
        ("alice", 1),
        ("bob", 2),
        ("carol", 2),
        ("dave", 4),
    ]


def test_competition_rank_from_higher_count():
    assert competition_rank_from_higher_count(0) == 1
    assert competition_rank_from_higher_count(4) == 5

