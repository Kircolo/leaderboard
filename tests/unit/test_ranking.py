from app.services.ranking import build_ranked_entries, competition_rank_from_higher_count


def test_build_ranked_entries_uses_competition_ranking():
    ranked = build_ranked_entries(
        [
            ("steam", "alice", 100),
            ("psn", "bob", 95),
            ("xbox", "carol", 95),
            ("ea", "dave", 80),
        ]
    )

    assert [(entry.platform, entry.user_id, entry.rank) for entry in ranked] == [
        ("steam", "alice", 1),
        ("psn", "bob", 2),
        ("xbox", "carol", 2),
        ("ea", "dave", 4),
    ]


def test_competition_rank_from_higher_count():
    assert competition_rank_from_higher_count(0) == 1
    assert competition_rank_from_higher_count(4) == 5
