import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import User
from app.services.settings import SettingsService

logger = logging.getLogger(__name__)


class TelegramNotify:
    async def _reports_chat_id(self, db: AsyncSession) -> str | None:
        chat_id = await SettingsService(db).get("reports_chat_id", "")
        if not chat_id and getattr(settings, "reports_chat_id", ""):
            chat_id = settings.reports_chat_id
        return chat_id or None

    async def send(self, db: AsyncSession, text: str) -> bool:
        chat_id = await self._reports_chat_id(db)
        if not chat_id or not settings.bot_token or settings.bot_token.startswith("000000:"):
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )
                if not response.is_success:
                    logger.warning("Reports chat send failed: %s", response.text[:300])
                return response.is_success
        except Exception:
            logger.exception("Failed to send report to Telegram")
            return False

    @staticmethod
    def _user_line(user: User | None, telegram_id: int) -> str:
        if user and user.username:
            return f"<code>{telegram_id}</code> (@{user.username})"
        return f"<code>{telegram_id}</code>"

    async def report_registration(
        self,
        db: AsyncSession,
        *,
        user: User | None,
        telegram_id: int,
    ) -> None:
        line = self._user_line(user, telegram_id)
        await self.send(db, f"✅ <b>REG</b> — регистрация\n👤 {line}")

    async def report_deposit(
        self,
        db: AsyncSession,
        *,
        user: User | None,
        telegram_id: int,
        amount: float | None,
    ) -> None:
        line = self._user_line(user, telegram_id)
        amount_text = f"{amount:g}" if amount is not None else "—"
        await self.send(db, f"💰 <b>DEP</b> — первый депозит\n👤 {line}\n💵 {amount_text}")

    async def report_unlimited_paid(
        self,
        db: AsyncSession,
        *,
        user: User | None,
        telegram_id: int,
        amount: int | float | None,
        currency: str | None,
        order_uuid: str | None,
    ) -> None:
        line = self._user_line(user, telegram_id)
        price = f"{amount:g} {currency or ''}".strip() if amount is not None else "—"
        order = f"\n🧾 <code>{order_uuid}</code>" if order_uuid else ""
        await self.send(db, f"♾ <b>UNLIMITED</b> — оплата\n👤 {line}\n💳 {price}{order}")

    async def report_unlimited_refund(
        self,
        db: AsyncSession,
        *,
        user: User | None,
        telegram_id: int,
        order_uuid: str | None,
    ) -> None:
        line = self._user_line(user, telegram_id)
        order = f"\n🧾 <code>{order_uuid}</code>" if order_uuid else ""
        await self.send(db, f"↩️ <b>REFUND</b> — возврат безлимита\n👤 {line}{order}")

    async def report_payment_failed(
        self,
        db: AsyncSession,
        *,
        telegram_id: int,
        order_uuid: str | None,
    ) -> None:
        order = f"\n🧾 <code>{order_uuid}</code>" if order_uuid else ""
        await self.send(db, f"❌ <b>PAY FAIL</b>\n👤 <code>{telegram_id}</code>{order}")
