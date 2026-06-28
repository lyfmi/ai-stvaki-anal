"""Post-install configuration — writes app_settings and activates bootstrap admin."""
import asyncio
import os
import sys

from app.core.database import async_session_factory
from app.services.funnel import FunnelService
from app.services.settings import SettingsService


async def main() -> None:
    mapping = {
        "channel_id": os.environ.get("CHANNEL_ID", ""),
        "channel_url": os.environ.get("CHANNEL_URL", ""),
        "reports_chat_id": os.environ.get("REPORTS_CHANNEL_ID", ""),
        "support_url": os.environ.get("SUPPORT_URL", "https://t.me/support"),
        "affiliate_ref_url": os.environ.get("AFFILIATE_REF_URL", ""),
        "affiliate_promo_code": os.environ.get("AFFILIATE_PROMO_CODE", ""),
        "tribute_api_key": os.environ.get("TRIBUTE_API_KEY", ""),
        "tribute_shop_id": os.environ.get("TRIBUTE_SHOP_ID", ""),
        "tribute_webhook_secret": os.environ.get("TRIBUTE_WEBHOOK_SECRET", ""),
        "tribute_enabled": os.environ.get("TRIBUTE_ENABLED", "false"),
        "unlimited_enabled": os.environ.get("UNLIMITED_ENABLED", "false"),
        "unlimited_price_amount": os.environ.get("UNLIMITED_PRICE_AMOUNT", "4900"),
        "unlimited_price_currency": os.environ.get("UNLIMITED_PRICE_CURRENCY", "rub"),
    }

    admin_raw = os.environ.get("ADMIN_TELEGRAM_ID", "").strip()

    async with async_session_factory() as session:
        svc = SettingsService(session)
        for key, value in mapping.items():
            if value is not None and value != "":
                await svc.set(key, str(value))

        if admin_raw.isdigit():
            funnel = FunnelService(session)
            user = await funnel.get_or_create(int(admin_raw))
            await funnel.ensure_full_access(user)
            print(f"Bootstrap admin {admin_raw} activated (ACTIVE, без воронки).", file=sys.stderr)

        await session.commit()

    print("App settings configured.", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
