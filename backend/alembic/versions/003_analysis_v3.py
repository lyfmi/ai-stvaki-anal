"""Add v3 analysis fields and source_type to ai_analyses."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_analysis_v3"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_analyses",
        sa.Column("source_type", sa.String(length=32), server_default="screenshot", nullable=False),
    )
    op.add_column("ai_analyses", sa.Column("analysis_mode", sa.String(length=32), nullable=True))
    op.add_column("ai_analyses", sa.Column("match_status_label", sa.String(length=64), nullable=True))
    op.add_column("ai_analyses", sa.Column("match_datetime_msk", sa.String(length=64), nullable=True))
    op.add_column(
        "ai_analyses",
        sa.Column("is_betting_recommendation", sa.Boolean(), nullable=True, server_default=sa.text("true")),
    )
    op.add_column("ai_analyses", sa.Column("premium_payload", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_analyses", "premium_payload")
    op.drop_column("ai_analyses", "is_betting_recommendation")
    op.drop_column("ai_analyses", "match_datetime_msk")
    op.drop_column("ai_analyses", "match_status_label")
    op.drop_column("ai_analyses", "analysis_mode")
    op.drop_column("ai_analyses", "source_type")
