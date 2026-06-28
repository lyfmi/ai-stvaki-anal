import httpx

from app.core.config import settings


async def resolve_telegram_username(username: str) -> int | None:
    clean = username.lstrip("@").strip()
    if not clean or not settings.bot_token:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{settings.bot_token}/getChat",
                params={"chat_id": f"@{clean}"},
            )
            data = response.json()
            if data.get("ok"):
                chat_id = data["result"].get("id")
                if chat_id is not None:
                    return int(chat_id)
    except Exception:
        return None
    return None


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
