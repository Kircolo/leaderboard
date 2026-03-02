from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScoreModel
from app.domain import ScoreRecord


def _to_record(model: ScoreModel) -> ScoreRecord:
    return ScoreRecord(
        game_id=model.game_id,
        user_id=model.user_id,
        score=model.score,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_submitted_at=model.last_submitted_at,
    )


class SqlAlchemyScoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_score(self, game_id: str, user_id: str) -> ScoreRecord | None:
        statement: Select[tuple[ScoreModel]] = select(ScoreModel).where(
            ScoreModel.game_id == game_id,
            ScoreModel.user_id == user_id,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return None if model is None else _to_record(model)

    async def create_score(self, game_id: str, user_id: str, score: int) -> ScoreRecord:
        now = datetime.now(UTC)
        model = ScoreModel(
            game_id=game_id,
            user_id=user_id,
            score=score,
            created_at=now,
            updated_at=now,
            last_submitted_at=now,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return _to_record(model)

    async def update_score(self, game_id: str, user_id: str, score: int) -> ScoreRecord:
        statement: Select[tuple[ScoreModel]] = select(ScoreModel).where(
            ScoreModel.game_id == game_id,
            ScoreModel.user_id == user_id,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one()
        now = datetime.now(UTC)
        model.score = score
        model.updated_at = now
        model.last_submitted_at = now
        await self.session.commit()
        await self.session.refresh(model)
        return _to_record(model)

    async def touch_submission(self, game_id: str, user_id: str) -> ScoreRecord:
        statement: Select[tuple[ScoreModel]] = select(ScoreModel).where(
            ScoreModel.game_id == game_id,
            ScoreModel.user_id == user_id,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one()
        model.last_submitted_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(model)
        return _to_record(model)

    async def get_all_scores_for_game(self, game_id: str) -> list[ScoreRecord]:
        statement: Select[tuple[ScoreModel]] = (
            select(ScoreModel)
            .where(ScoreModel.game_id == game_id)
            .order_by(ScoreModel.score.desc(), ScoreModel.user_id.asc())
        )
        result = await self.session.execute(statement)
        return [_to_record(model) for model in result.scalars().all()]

