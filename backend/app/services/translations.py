from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AiAnalysis, Translation


class TranslationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str, locale: str, **params) -> str:
        result = await self.db.execute(
            select(Translation).where(Translation.key == key, Translation.locale == locale)
        )
        row = result.scalar_one_or_none()
        if not row:
            result = await self.db.execute(
                select(Translation).where(Translation.key == key, Translation.locale == "ru")
            )
            row = result.scalar_one_or_none()
        text = row.value if row else key
        for k, v in params.items():
            text = text.replace("{" + k + "}", str(v))
        return text

    async def get_many(self, locale: str) -> dict[str, str]:
        result = await self.db.execute(select(Translation).where(Translation.locale == locale))
        return {r.key: r.value for r in result.scalars().all()}


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> dict:
        from app.models import User

        total = await self.db.scalar(select(func.count()).select_from(User))
        registered = await self.db.scalar(select(func.count()).select_from(User).where(User.is_registered.is_(True)))
        deposited = await self.db.scalar(select(func.count()).select_from(User).where(User.is_deposited.is_(True)))
        unlimited = await self.db.scalar(select(func.count()).select_from(User).where(User.has_unlimited.is_(True)))
        analyses = await self.db.scalar(select(func.count()).select_from(AiAnalysis))
        today = await self.db.scalar(
            select(func.count())
            .select_from(AiAnalysis)
            .where(func.date(AiAnalysis.created_at) == func.current_date())
        )
        return {
            "total_users": total or 0,
            "registered_users": registered or 0,
            "deposited_users": deposited or 0,
            "unlimited_users": unlimited or 0,
            "total_analyses": analyses or 0,
            "analyses_today": today or 0,
        }
