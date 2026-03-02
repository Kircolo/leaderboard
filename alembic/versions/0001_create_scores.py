"""create scores table

Revision ID: 0001_create_scores
Revises: 
Create Date: 2026-03-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_scores"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("game_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("score", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("game_id", "user_id"),
    )
    op.create_index("ix_scores_game_score_user", "scores", ["game_id", "score", "user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scores_game_score_user", table_name="scores")
    op.drop_table("scores")

