import json

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import User
from app.schemas import AdminOut, UserOut
from app.services.settings import SettingsService
from app.services.telegram_bot import resolve_telegram_username


class AdminService:
    EXTRA_KEY = "extra_admin_telegram_ids"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = SettingsService(db)

    @staticmethod
    def env_admin_ids() -> set[int]:
        return settings.admin_ids

    async def extra_admin_ids(self) -> set[int]:
        raw = await self.settings.get(self.EXTRA_KEY, "[]")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return set()
        return {int(x) for x in data if str(x).isdigit()}

    async def all_admin_ids(self) -> set[int]:
        return self.env_admin_ids() | await self.extra_admin_ids()

    async def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in await self.all_admin_ids()

    async def enrich_user(self, user: User) -> UserOut:
        return UserOut.model_validate(user).model_copy(update={"is_admin": await self.is_admin(user.telegram_id)})

    async def list_admins(self) -> list[AdminOut]:
        all_ids = await self.all_admin_ids()
        env_ids = self.env_admin_ids()
        result = await self.db.execute(select(User).where(User.telegram_id.in_(all_ids)))
        users_by_id = {u.telegram_id: u for u in result.scalars().all()}

        admins: list[AdminOut] = []
        for telegram_id in sorted(all_ids):
            user = users_by_id.get(telegram_id)
            admins.append(
                AdminOut(
                    telegram_id=telegram_id,
                    username=user.username if user else None,
                    removable=telegram_id not in env_ids,
                    source="env" if telegram_id in env_ids else "panel",
                )
            )
        return admins

    async def resolve_telegram_id(self, *, telegram_id: int | None = None, username: str | None = None) -> int:
        if telegram_id is not None:
            return telegram_id
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_id or username required")

        clean = username.lstrip("@").strip().lower()
        if not clean:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")

        result = await self.db.execute(select(User).where(func.lower(User.username) == clean))
        user = result.scalar_one_or_none()
        if user:
            return user.telegram_id

        resolved = await resolve_telegram_username(clean)
        if resolved is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. They must start the bot first or exist in the database.",
            )
        return resolved

    async def add_admin(self, *, telegram_id: int | None = None, username: str | None = None) -> AdminOut:
        target_id = await self.resolve_telegram_id(telegram_id=telegram_id, username=username)
        if await self.is_admin(target_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already an admin")

        extra = await self.extra_admin_ids()
        extra.add(target_id)
        await self.settings.set(self.EXTRA_KEY, json.dumps(sorted(extra)))

        user_result = await self.db.execute(select(User).where(User.telegram_id == target_id))
        user = user_result.scalar_one_or_none()
        clean_username = username.lstrip("@").strip().lower() if username else None
        if user is None:
            user = User(telegram_id=target_id, username=clean_username, funnel_state="NEW")
            self.db.add(user)
        elif clean_username and not user.username:
            user.username = clean_username
        await self.db.flush()

        return AdminOut(
            telegram_id=target_id,
            username=user.username,
            removable=True,
            source="panel",
        )

    async def remove_admin(self, telegram_id: int, actor_id: int) -> None:
        if telegram_id in self.env_admin_ids():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove bootstrap admin")
        if telegram_id == actor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself")

        extra = await self.extra_admin_ids()
        if telegram_id not in extra:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

        extra.remove(telegram_id)
        await self.settings.set(self.EXTRA_KEY, json.dumps(sorted(extra)))
