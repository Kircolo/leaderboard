from pydantic import BaseModel, ConfigDict, Field


class RankedEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    user_id: str
    score: int


class SubmitScoreRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    score: int = Field(ge=0, le=9223372036854775807)


class SubmitScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    user_id: str
    submitted_score: int
    stored_score: int
    updated: bool
    rank: int


class LeaderboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    limit: int
    entries: list[RankedEntryResponse]


class UserContextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    user_id: str
    rank: int
    score: int
    window: int
    above: list[RankedEntryResponse]
    below: list[RankedEntryResponse]
