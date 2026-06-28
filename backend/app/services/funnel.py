from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class FunnelState:
    NEW = "NEW"
    LANGUAGE_SELECTED = "LANGUAGE_SELECTED"
    CHANNEL_SUBSCRIBED = "CHANNEL_SUBSCRIBED"
    REGISTRATION_PENDING = "REGISTRATION_PENDING"
    REGISTERED = "REGISTERED"
    DEPOSIT_PENDING = "DEPOSIT_PENDING"
    DEPOSIT_CONFIRMED = "DEPOSIT_CONFIRMED"
    ACTIVE = "ACTIVE"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    UNLIMITED = "UNLIMITED"


class FunnelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, telegram_id: int, username: str | None = None) -> User:
        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            if username and user.username != username:
                user.username = username
            return user
        user = User(telegram_id=telegram_id, username=username, funnel_state=FunnelState.NEW)
        self.db.add(user)
        await self.db.flush()
        return user

    async def set_language(self, user: User, language: str) -> User:
        user.language = language
        if user.funnel_state == FunnelState.NEW:
            user.funnel_state = FunnelState.LANGUAGE_SELECTED
        return user

    async def mark_channel_subscribed(self, user: User) -> User:
        user.is_channel_subscribed = True
        if user.funnel_state in (FunnelState.LANGUAGE_SELECTED, FunnelState.NEW):
            user.funnel_state = FunnelState.CHANNEL_SUBSCRIBED
        return user

    async def start_registration(self, user: User) -> User:
        if user.funnel_state in (FunnelState.CHANNEL_SUBSCRIBED, FunnelState.LANGUAGE_SELECTED):
            user.funnel_state = FunnelState.REGISTRATION_PENDING
        return user

    async def mark_registered(self, user: User, admin_bypass: bool = False) -> User:
        user.is_registered = True
        user.registered_at = datetime.now(UTC)
        user.funnel_state = FunnelState.REGISTERED
        if admin_bypass or user.is_deposited:
            pass
        else:
            user.funnel_state = FunnelState.DEPOSIT_PENDING
        return user

    async def mark_deposited(self, user: User, amount: float | None = None, admin_bypass: bool = False) -> User:
        user.is_deposited = True
        user.deposited_at = datetime.now(UTC)
        if amount is not None:
            user.deposit_amount = amount
        if user.has_unlimited:
            user.funnel_state = FunnelState.UNLIMITED
        else:
            user.funnel_state = FunnelState.ACTIVE
        return user

    async def ensure_full_access(self, user: User, *, language: str = "ru") -> User:
        """Полный доступ без воронки — для bootstrap-админа и ручной активации."""
        if not user.language:
            user.language = language
        user.is_channel_subscribed = True
        user.is_registered = True
        if not user.registered_at:
            user.registered_at = datetime.now(UTC)
        user.is_deposited = True
        if not user.deposited_at:
            user.deposited_at = datetime.now(UTC)
        if user.has_unlimited:
            user.funnel_state = FunnelState.UNLIMITED
        else:
            user.funnel_state = FunnelState.ACTIVE
        return user

    async def grant_unlimited(self, user: User) -> User:
        user.has_unlimited = True
        user.funnel_state = FunnelState.UNLIMITED
        return user

    async def revoke_unlimited(self, user: User) -> User:
        user.has_unlimited = False
        if user.is_deposited:
            user.funnel_state = FunnelState.ACTIVE
        elif user.is_registered:
            user.funnel_state = FunnelState.DEPOSIT_PENDING
        else:
            user.funnel_state = FunnelState.REGISTRATION_PENDING
        return user

    async def can_analyze_funnel(self, user: User, telegram_id: int) -> bool:
        from app.services.admin import AdminService

        if await AdminService(self.db).is_admin(telegram_id):
            return True
        return user.funnel_state in (FunnelState.ACTIVE, FunnelState.UNLIMITED, FunnelState.LIMIT_EXCEEDED) and (
            user.is_deposited or user.has_unlimited
        )
