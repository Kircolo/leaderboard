from datetime import UTC, datetime

from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScoreModel
from app.domain import ScoreRecord


def _to_record(model: ScoreModel) -> ScoreRecord:
    return ScoreRecord(
        game_id=model.game_id,
        platform=model.platform,
        user_id=model.user_id,
        score=model.score,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_submitted_at=model.last_submitted_at,
    )


class SqlAlchemyScoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_score(self, game_id: str, platform: str, user_id: str) -> ScoreRecord | None:
        statement: Select[tuple[ScoreModel]] = select(ScoreModel).where(
            ScoreModel.game_id == game_id,
            ScoreModel.platform == platform,
            ScoreModel.user_id == user_id,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return None if model is None else _to_record(model)

    async def upsert_high_score(
        self,
        game_id: str,
        platform: str,
        user_id: str,
        score: int,
    ) -> tuple[ScoreRecord, bool]:
        now = datetime.now(UTC)
        returning_columns = (
            ScoreModel.game_id,
            ScoreModel.platform,
            ScoreModel.user_id,
            ScoreModel.score,
            ScoreModel.created_at,
            ScoreModel.updated_at,
            ScoreModel.last_submitted_at,
        )
        insert_statement = pg_insert(ScoreModel).values(
            game_id=game_id,
            platform=platform,
            user_id=user_id,
            score=score,
            created_at=now,
            updated_at=now,
            last_submitted_at=now,
        )
        upsert_statement = (
            insert_statement.on_conflict_do_update(
                index_elements=[ScoreModel.game_id, ScoreModel.platform, ScoreModel.user_id],
                set_={
                    "score": insert_statement.excluded.score,
                    "updated_at": now,
                    "last_submitted_at": now,
                },
                where=insert_statement.excluded.score > ScoreModel.score,
            )
            .returning(*returning_columns)
        )
        result = await self.session.execute(upsert_statement)
        row = result.one_or_none()

        if row is not None:
            await self.session.commit()
            return ScoreRecord(*row), True

        touch_statement = (
            update(ScoreModel)
            .where(
                ScoreModel.game_id == game_id,
                ScoreModel.platform == platform,
                ScoreModel.user_id == user_id,
            )
            .values(last_submitted_at=now)
            .returning(*returning_columns)
        )
        touch_result = await self.session.execute(touch_statement)
        await self.session.commit()
        return ScoreRecord(*touch_result.one()), False

    async def get_all_scores_for_game(self, game_id: str) -> list[ScoreRecord]:
        statement: Select[tuple[ScoreModel]] = (
            select(ScoreModel)
            .where(ScoreModel.game_id == game_id)
            .order_by(ScoreModel.score.desc(), ScoreModel.platform.asc(), ScoreModel.user_id.asc())
        )
        result = await self.session.execute(statement)
        return [_to_record(model) for model in result.scalars().all()]
