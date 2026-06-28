"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("language", sa.String(5), server_default="ru"),
        sa.Column("funnel_state", sa.String(32), server_default="NEW"),
        sa.Column("is_channel_subscribed", sa.Boolean(), server_default="false"),
        sa.Column("is_registered", sa.Boolean(), server_default="false"),
        sa.Column("is_deposited", sa.Boolean(), server_default="false"),
        sa.Column("has_unlimited", sa.Boolean(), server_default="false"),
        sa.Column("attempts_count", sa.Integer(), server_default="0"),
        sa.Column("attempts_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deposited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("is_blocked", sa.Boolean(), server_default="false"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "ai_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("image_path", sa.String(512), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("coefficient", sa.Numeric(8, 2), nullable=True),
        sa.Column("probability_percent", sa.Integer(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("risk", sa.String(16), nullable=True),
        sa.Column("confidence", sa.String(16), nullable=True),
        sa.Column("arguments", postgresql.JSONB(), nullable=True),
        sa.Column("vision_payload", postgresql.JSONB(), nullable=True),
        sa.Column("search_payload", postgresql.JSONB(), nullable=True),
        sa.Column("pipeline_version", sa.String(32), nullable=True),
        sa.Column("latency_ms", postgresql.JSONB(), nullable=True),
        sa.Column("raw_ai_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_analyses_user_id", "ai_analyses", ["user_id"])

    op.create_table(
        "postback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("payload_hash", sa.String(64), unique=True, nullable=True),
        sa.Column("processed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_postback_events_telegram_id", "postback_events", ["telegram_id"])

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "tribute_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_uuid", sa.String(128), nullable=False, unique=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_tribute_payments_order_uuid", "tribute_payments", ["order_uuid"])
    op.create_index("ix_tribute_payments_telegram_id", "tribute_payments", ["telegram_id"])

    op.create_table(
        "broadcasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("photo_url", sa.String(512), nullable=True),
        sa.Column("sent_count", sa.Integer(), server_default="0"),
        sa.Column("failed_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "translations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("locale", sa.String(5), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.UniqueConstraint("key", "locale", name="uq_translation_key_locale"),
    )
    op.create_index("ix_translations_key", "translations", ["key"])
    op.create_index("ix_translations_locale", "translations", ["locale"])


def downgrade() -> None:
    op.drop_table("translations")
    op.drop_table("broadcasts")
    op.drop_table("tribute_payments")
    op.drop_table("app_settings")
    op.drop_table("postback_events")
    op.drop_table("ai_analyses")
    op.drop_table("users")
