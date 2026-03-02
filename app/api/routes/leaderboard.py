from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_leaderboard_service
from app.schemas.leaderboard import (
    LeaderboardResponse,
    SubmitScoreRequest,
    SubmitScoreResponse,
    UserContextResponse,
)
from app.services.leaderboard_service import LeaderboardService

router = APIRouter()


GameId = Path(min_length=1, max_length=128)
UserId = Path(min_length=1, max_length=128)


@router.post("/games/{game_id}/scores", response_model=SubmitScoreResponse)
async def submit_score(
    payload: SubmitScoreRequest,
    game_id: str = GameId,
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> SubmitScoreResponse:
    result = await service.submit_score(game_id=game_id, user_id=payload.user_id, score=payload.score)
    return SubmitScoreResponse.model_validate(result)


@router.get("/games/{game_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    game_id: str = GameId,
    limit: int = Query(default=10, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> LeaderboardResponse:
    result = await service.get_top_leaderboard(game_id=game_id, limit=limit)
    return LeaderboardResponse.model_validate(result)


@router.get("/games/{game_id}/users/{user_id}/context", response_model=UserContextResponse)
async def get_user_context(
    game_id: str = GameId,
    user_id: str = UserId,
    window: int = Query(default=2, ge=1, le=10),
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> UserContextResponse:
    result = await service.get_user_context(game_id=game_id, user_id=user_id, window=window)
    return UserContextResponse.model_validate(result)

