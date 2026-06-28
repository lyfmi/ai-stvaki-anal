import httpx

from app.core.config import settings


async def is_channel_member(channel_id: str, telegram_id: int) -> bool:
    if not channel_id or not settings.bot_token:
        return True
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{settings.bot_token}/getChatMember",
                params={"chat_id": channel_id, "user_id": telegram_id},
            )
            data = response.json()
            if not data.get("ok"):
                return False
            return data["result"].get("status") in ("member", "administrator", "creator")
    except Exception:
        return False
