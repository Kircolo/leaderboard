from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_leaderboard_service
from app.schemas.identifiers import Identifier, PlatformIdentifier
from app.schemas.leaderboard import (
    LeaderboardResponse,
    SubmitScoreRequest,
    SubmitScoreResponse,
    UserContextResponse,
)
from app.services.leaderboard_service import LeaderboardService

router = APIRouter()


GameId = Annotated[Identifier, Path()]
UserId = Annotated[Identifier, Path()]
Platform = Annotated[PlatformIdentifier, Path()]
LeaderboardLimit = Annotated[int, Query(ge=1, le=100)]
ContextWindow = Annotated[int, Query(ge=1, le=10)]
LeaderboardServiceDependency = Annotated[LeaderboardService, Depends(get_leaderboard_service)]


@router.post("/games/{game_id}/scores", response_model=SubmitScoreResponse)
async def submit_score(
    payload: SubmitScoreRequest,
    game_id: GameId,
    service: LeaderboardServiceDependency,
) -> SubmitScoreResponse:
    result = await service.submit_score(
        game_id=game_id,
        platform=payload.platform,
        user_id=payload.user_id,
        score=payload.score,
    )
    return SubmitScoreResponse.model_validate(result)


@router.get("/games/{game_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    game_id: GameId,
    service: LeaderboardServiceDependency,
    limit: LeaderboardLimit = 10,
) -> LeaderboardResponse:
    result = await service.get_top_leaderboard(game_id=game_id, limit=limit)
    return LeaderboardResponse.model_validate(result)


@router.get(
    "/games/{game_id}/platforms/{platform}/users/{user_id}/context",
    response_model=UserContextResponse,
)
async def get_user_context(
    game_id: GameId,
    platform: Platform,
    user_id: UserId,
    service: LeaderboardServiceDependency,
    window: ContextWindow = 2,
) -> UserContextResponse:
    result = await service.get_user_context(
        game_id=game_id,
        platform=platform,
        user_id=user_id,
        window=window,
    )
    return UserContextResponse.model_validate(result)
