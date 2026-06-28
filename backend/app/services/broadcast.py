import json
import logging
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Broadcast, User

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _photo_paths(broadcast: Broadcast) -> list[str]:
        if broadcast.photo_paths:
            return list(broadcast.photo_paths)
        if broadcast.photo_url:
            try:
                parsed = json.loads(broadcast.photo_url)
                if isinstance(parsed, list):
                    return [str(p) for p in parsed]
            except json.JSONDecodeError:
                return [broadcast.photo_url]
        return []

    async def _send_message(self, client: httpx.AsyncClient, telegram_id: int, text: str) -> bool:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
            json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        if not response.is_success:
            logger.warning("Broadcast message failed for %s: %s", telegram_id, response.text[:200])
        return response.is_success

    async def _send_photos(
        self,
        client: httpx.AsyncClient,
        telegram_id: int,
        text: str,
        photo_paths: list[str],
    ) -> bool:
        existing = [p for p in photo_paths if Path(p).exists()]
        if not existing:
            return await self._send_message(client, telegram_id, text)

        if len(existing) == 1:
            with open(existing[0], "rb") as photo_file:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.bot_token}/sendPhoto",
                    data={"chat_id": str(telegram_id), "caption": text, "parse_mode": "HTML"},
                    files={"photo": (Path(existing[0]).name, photo_file, "image/jpeg")},
                )
            if not response.is_success:
                logger.warning("Broadcast photo failed for %s: %s", telegram_id, response.text[:200])
            return response.is_success

        media = []
        files: dict[str, tuple] = {}
        for idx, path in enumerate(existing[:5]):
            key = f"photo{idx}"
            media.append(
                {
                    "type": "photo",
                    "media": f"attach://{key}",
                    **({"caption": text, "parse_mode": "HTML"} if idx == 0 else {}),
                }
            )
            files[key] = (Path(path).name, open(path, "rb"), "image/jpeg")

        try:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.bot_token}/sendMediaGroup",
                data={"chat_id": str(telegram_id), "media": json.dumps(media)},
                files=files,
            )
            if not response.is_success:
                logger.warning("Broadcast media group failed for %s: %s", telegram_id, response.text[:200])
            return response.is_success
        finally:
            for file_tuple in files.values():
                file_tuple[1].close()

    async def run(self, broadcast: Broadcast) -> tuple[int, int]:
        if not settings.bot_token or settings.bot_token.startswith("000000:"):
            raise RuntimeError("BOT_TOKEN is not configured")

        result = await self.db.execute(
            select(User).where(User.is_blocked.is_(False)).order_by(User.created_at.asc())
        )
        users = list(result.scalars().all())
        photo_paths = self._photo_paths(broadcast)
        sent = 0
        failed = 0

        async with httpx.AsyncClient(timeout=60.0) as client:
            for user in users:
                try:
                    ok = (
                        await self._send_photos(client, user.telegram_id, broadcast.message_text, photo_paths)
                        if photo_paths
                        else await self._send_message(client, user.telegram_id, broadcast.message_text)
                    )
                    if ok:
                        sent += 1
                    else:
                        failed += 1
                except Exception:
                    logger.exception("Broadcast failed for user %s", user.telegram_id)
                    failed += 1

        broadcast.sent_count = sent
        broadcast.failed_count = failed
        return sent, failed
