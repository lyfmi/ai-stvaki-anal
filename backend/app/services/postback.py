import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import PostbackEvent, User
from app.services.funnel import FunnelService


class PostbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.funnel = FunnelService(db)

    @staticmethod
    def _payload_hash(event_type: str, telegram_id: int, payload: dict) -> str:
        raw = json.dumps({"event_type": event_type, "telegram_id": telegram_id, "payload": payload}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _is_duplicate(self, payload_hash: str) -> bool:
        result = await self.db.execute(select(PostbackEvent).where(PostbackEvent.payload_hash == payload_hash))
        return result.scalar_one_or_none() is not None

    async def handle_registration(self, telegram_id: int, payload: dict) -> tuple[User | None, bool]:
        phash = self._payload_hash("registration", telegram_id, payload)
        if await self._is_duplicate(phash):
            result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
            return result.scalar_one_or_none(), False

        admin_bypass = telegram_id in settings.admin_ids
        user = await self.funnel.get_or_create(telegram_id)
        await self.funnel.mark_registered(user, admin_bypass=admin_bypass)
        if admin_bypass and not user.is_deposited:
            user.funnel_state = "DEPOSIT_PENDING"

        self.db.add(
            PostbackEvent(
                telegram_id=telegram_id,
                event_type="registration",
                raw_payload=payload,
                payload_hash=phash,
                processed=True,
            )
        )
        return user, True

    async def handle_deposit(self, telegram_id: int, amount: float | None, payload: dict) -> tuple[User | None, bool]:
        phash = self._payload_hash("deposit", telegram_id, payload)
        if await self._is_duplicate(phash):
            result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
            return result.scalar_one_or_none(), False

        admin_bypass = telegram_id in settings.admin_ids
        user = await self.funnel.get_or_create(telegram_id)
        if not user.is_registered:
            await self.funnel.mark_registered(user, admin_bypass=admin_bypass)
        await self.funnel.mark_deposited(user, amount=amount, admin_bypass=admin_bypass)

        self.db.add(
            PostbackEvent(
                telegram_id=telegram_id,
                event_type="deposit",
                amount=amount,
                raw_payload=payload,
                payload_hash=phash,
                processed=True,
            )
        )
        return user, True
