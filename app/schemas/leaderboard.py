from pydantic import BaseModel, ConfigDict, Field

from app.schemas.identifiers import Identifier, PlatformIdentifier


class RankedEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    platform: str
    user_id: str
    score: int


class SubmitScoreRequest(BaseModel):
    platform: PlatformIdentifier
    user_id: Identifier
    score: int = Field(ge=0, le=9223372036854775807)


class SubmitScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    platform: str
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
    platform: str
    user_id: str
    rank: int
    score: int
    window: int
    above: list[RankedEntryResponse]
    below: list[RankedEntryResponse]
