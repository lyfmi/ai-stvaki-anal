import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import AppSetting, Translation
from app.services.settings import SettingsService


TRANSLATIONS = {
    "ru": {
        "welcome": "👋 Добро пожаловать в AI Анализ Стavок!\n\nВыберите язык:",
        "choose_language": "Выберите язык:",
        "subscribe_channel": "📢 Подпишитесь на наш канал, чтобы получить доступ к сигналам.",
        "btn_subscribe": "📢 Подписаться",
        "btn_check_sub": "✅ Проверить подписку",
        "get_signal": "🎯 Нажмите «Получить сигнал», чтобы продолжить.",
        "btn_get_signal": "🎯 Получить сигнал",
        "registration": "📝 Зарегистрируйтесь по ссылке ниже.\n\nПромокод: {promo_code}",
        "btn_register": "📝 Зарегистрироваться",
        "btn_check_reg": "✅ Я зарегистрировался",
        "deposit": "💰 Сделайте первый депозит в букмекерской конторе.",
        "btn_deposit": "💰 Пополнить",
        "btn_check_deposit": "✅ Проверить депозит",
        "active": "✅ Доступ открыт! Отправьте скриншот события для AI-анализа.",
        "limit_exceeded": "⏳ Лимит исчерпан. Попробуйте позже или купите безлимит.",
        "btn_unlimited": "♾ Купить безлимит",
        "btn_support": "💬 Поддержка",
        "analyzing": "🔍 Анализирую скриншот...",
        "analysis_error": "❌ Не удалось прочитать скриншот. Попробуйте другое фото.",
        "analysis_limit": "❌ Лимит анализов исчерпан на сегодня.",
        "analysis_funnel": "❌ Сначала пройдите воронку: регистрация и депозит.",
        "registered_ok": "✅ Регистрация подтверждена!",
        "deposit_ok": "✅ Депозит подтверждён! Отправьте скрин для анализа.",
        "unlimited_ok": "♾ Безлимит активирован!",
        "admin_menu": "⚙️ Админ-панель",
        "admin_stats": "📊 Статистика",
        "admin_broadcast": "📢 Рассылка",
        "admin_affiliate": "🔗 Реф. ссылка",
        "admin_unlimited": "♾ Безлимит",
        "admin_settings": "⚙️ Настройки",
        "admin_postback": "🔗 Postback URLs",
    },
    "en": {
        "welcome": "👋 Welcome to AI Bet Analysis!\n\nChoose your language:",
        "choose_language": "Choose language:",
        "subscribe_channel": "📢 Subscribe to our channel to get access.",
        "btn_subscribe": "📢 Subscribe",
        "btn_check_sub": "✅ Check subscription",
        "get_signal": "🎯 Press «Get signal» to continue.",
        "btn_get_signal": "🎯 Get signal",
        "registration": "📝 Register using the link below.\n\nPromo code: {promo_code}",
        "btn_register": "📝 Register",
        "btn_check_reg": "✅ I registered",
        "deposit": "💰 Make your first deposit.",
        "btn_deposit": "💰 Deposit",
        "btn_check_deposit": "✅ Check deposit",
        "active": "✅ Access granted! Send an event screenshot for AI analysis.",
        "limit_exceeded": "⏳ Limit exceeded. Try later or buy unlimited.",
        "btn_unlimited": "♾ Buy unlimited",
        "btn_support": "💬 Support",
        "analyzing": "🔍 Analyzing screenshot...",
        "analysis_error": "❌ Could not read screenshot. Try another photo.",
        "analysis_limit": "❌ Daily analysis limit reached.",
        "analysis_funnel": "❌ Complete the funnel first: registration and deposit.",
        "registered_ok": "✅ Registration confirmed!",
        "deposit_ok": "✅ Deposit confirmed! Send a screenshot for analysis.",
        "unlimited_ok": "♾ Unlimited activated!",
        "admin_menu": "⚙️ Admin panel",
        "admin_stats": "📊 Stats",
        "admin_broadcast": "📢 Broadcast",
        "admin_affiliate": "🔗 Affiliate",
        "admin_unlimited": "♾ Unlimited",
        "admin_settings": "⚙️ Settings",
        "admin_postback": "🔗 Postback URLs",
    },
}


async def run_seed() -> None:
    async with async_session_factory() as db:
        settings = SettingsService(db)
        for key, value in settings.DEFAULTS.items():
            result = await db.execute(select(AppSetting).where(AppSetting.key == key))
            if not result.scalar_one_or_none():
                db.add(AppSetting(key=key, value=value))

        for locale, texts in TRANSLATIONS.items():
            for key, value in texts.items():
                result = await db.execute(
                    select(Translation).where(Translation.key == key, Translation.locale == locale)
                )
                if not result.scalar_one_or_none():
                    db.add(Translation(key=key, locale=locale, value=value))

        await db.commit()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(run_seed())
