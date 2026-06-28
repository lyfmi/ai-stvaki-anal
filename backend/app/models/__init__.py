import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    funnel_state: Mapped[str] = mapped_column(String(32), default="NEW")
    is_channel_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deposited: Mapped[bool] = mapped_column(Boolean, default=False)
    has_unlimited: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    attempts_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deposited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deposit_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    analyses: Mapped[list["AiAnalysis"]] = relationship(back_populates="user")


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    coefficient: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    probability_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    arguments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    vision_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    search_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pipeline_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_ai_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="analyses")


class PostbackEvent(Base):
    __tablename__ = "postback_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    event_type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TributePayment(Base):
    __tablename__ = "tribute_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_uuid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger)
    message_text: Mapped[str] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_paths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("key", "locale", name="uq_translation_key_locale"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    locale: Mapped[str] = mapped_column(String(5), index=True)
    value: Mapped[str] = mapped_column(Text)
