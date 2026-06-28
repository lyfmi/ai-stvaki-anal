import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting


class SettingsService:
    DEFAULTS = {
        "affiliate_ref_url": "https://example.com/ref",
        "affiliate_promo_code": "AIBET776",
        "affiliate_sub_param": "sub1",
        "channel_id": "",
        "channel_url": "https://t.me/example",
        "reports_chat_id": "",
        "support_url": "https://t.me/support",
        "unlimited_enabled": "true",
        "unlimited_price_amount": "4900",
        "unlimited_price_currency": "rub",
        "tribute_enabled": "false",
        "tribute_mode": "shop_api",
        "tribute_product_link": "",
        "tribute_api_key": "",
        "tribute_shop_id": "",
        "tribute_webhook_secret": "",
        "enabled_languages": '["ru","en"]',
        "default_language": "ru",
        "daily_attempts_limit": "10",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str, default: str | None = None) -> str:
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if row:
            return row.value
        return default if default is not None else self.DEFAULTS.get(key, "")

    async def get_int(self, key: str, default: int = 0) -> int:
        val = await self.get(key, str(default))
        try:
            return int(val)
        except ValueError:
            return default

    async def get_bool(self, key: str, default: bool = False) -> bool:
        val = await self.get(key, str(default).lower())
        return val.lower() in ("true", "1", "yes")

    async def get_json(self, key: str, default: list | dict | None = None):
        val = await self.get(key, "")
        if not val:
            return default if default is not None else []
        return json.loads(val)

    async def set(self, key: str, value: str) -> None:
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            self.db.add(AppSetting(key=key, value=value))

    async def get_all(self) -> dict[str, str]:
        result = await self.db.execute(select(AppSetting))
        rows = {r.key: r.value for r in result.scalars().all()}
        merged = dict(self.DEFAULTS)
        merged.update(rows)
        return merged

    async def update_many(self, updates: dict[str, str | int | bool | list]) -> None:
        for key, value in updates.items():
            if isinstance(value, (list, dict)):
                await self.set(key, json.dumps(value))
            else:
                await self.set(key, str(value))
