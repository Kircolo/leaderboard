from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ScoreRecord:
    game_id: str
    platform: str
    user_id: str
    score: int
    created_at: datetime
    updated_at: datetime
    last_submitted_at: datetime


@dataclass(slots=True)
class RankedEntry:
    rank: int
    platform: str
    user_id: str
    score: int


@dataclass(slots=True)
class SubmitScoreResult:
    game_id: str
    platform: str
    user_id: str
    submitted_score: int
    stored_score: int
    updated: bool
    rank: int


@dataclass(slots=True)
class LeaderboardResult:
    game_id: str
    limit: int
    entries: list[RankedEntry]


@dataclass(slots=True)
class UserContextResult:
    game_id: str
    platform: str
    user_id: str
    rank: int
    score: int
    window: int
    above: list[RankedEntry]
    below: list[RankedEntry]
