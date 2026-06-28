from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import User
from app.services.settings import SettingsService


class AttemptsLimitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = SettingsService(db)

    async def get_daily_limit(self) -> int:
        limit = await self.settings.get_int("daily_attempts_limit", settings.daily_attempts_limit)
        return limit

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _window_expired(self, user: User) -> bool:
        if user.attempts_window_start is None:
            return True
        return self._now() >= user.attempts_window_start + timedelta(hours=24)

    async def refresh_window(self, user: User) -> None:
        if self._window_expired(user):
            user.attempts_count = 0
            user.attempts_window_start = None

    async def can_analyze(self, user: User) -> tuple[bool, int, datetime | None]:
        if user.has_unlimited:
            return True, 999999, None
        await self.refresh_window(user)
        limit = await self.get_daily_limit()
        remaining = max(0, limit - user.attempts_count)
        reset_at = None
        if user.attempts_window_start and user.attempts_count >= limit:
            reset_at = user.attempts_window_start + timedelta(hours=24)
        return remaining > 0, remaining, reset_at

    async def consume_attempt(self, user: User) -> None:
        if user.has_unlimited:
            return
        await self.refresh_window(user)
        if user.attempts_window_start is None:
            user.attempts_window_start = self._now()
        user.attempts_count += 1
        limit = await self.get_daily_limit()
        if user.attempts_count >= limit and not user.has_unlimited:
            user.funnel_state = "LIMIT_EXCEEDED"
