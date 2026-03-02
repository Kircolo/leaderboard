from app.domain import RankedEntry


def competition_rank_from_higher_count(higher_count: int) -> int:
    return higher_count + 1


def build_ranked_entries(entries: list[tuple[str, int]]) -> list[RankedEntry]:
    ranked_entries: list[RankedEntry] = []
    current_rank = 0
    previous_score: int | None = None

    for index, (user_id, score) in enumerate(entries, start=1):
        if score != previous_score:
            current_rank = index
            previous_score = score
        ranked_entries.append(RankedEntry(rank=current_rank, user_id=user_id, score=score))

    return ranked_entries

