import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import AppSetting, Translation
from app.services.settings import SettingsService


TRANSLATIONS = {
    "ru": {
        "welcome": (
            "👋 <b>Добро пожаловать в AI Анализ Стavок!</b>\n\n"
            "🤖 Бот проанализирует скриншот события и подскажет, куда ставить.\n\n"
            "🌍 Выберите язык интерфейса:\n"
            "💡 Сменить язык позже: /language"
        ),
        "choose_language": "🌍 Выберите язык / Choose language:",
        "language_changed": "✅ Язык изменён",
        "subscribe_channel": (
            "📢 <b>Шаг 1 — подписка на канал</b>\n\n"
            "Подпишитесь на наш Telegram-канал с прогнозами и сигналами.\n\n"
            "1️⃣ Нажмите «Подписаться на канал»\n"
            "2️⃣ Вступите в канал\n"
            "3️⃣ Вернитесь сюда и нажмите «Проверить подписку» 👇"
        ),
        "btn_subscribe": "📢 Подписаться на канал",
        "btn_check_sub": "✅ Проверить подписку",
        "sub_check_ok": "✅ Подписка подтверждена!",
        "sub_not_joined": "❌ Вы ещё не подписаны. Вступите в канал и нажмите проверку снова.",
        "get_signal": (
            "🎯 <b>Шаг 2 — получить ссылку</b>\n\n"
            "Нажмите кнопку ниже — бот выдаст персональную реферальную ссылку и промокод для регистрации 👇"
        ),
        "btn_get_signal": "🎯 Получить сигнал",
        "registration": (
            "📝 <b>Шаг 3 — регистрация в БК</b>\n\n"
            "1️⃣ Нажмите «Зарегистрироваться»\n"
            "2️⃣ Создайте аккаунт по ссылке\n"
            "3️⃣ Введите промокод: <code>{promo_code}</code>\n\n"
            "Когда закончите — нажмите «Я зарегистрировался» ✅"
        ),
        "btn_register": "📝 Зарегистрироваться",
        "btn_check_reg": "✅ Я зарегистрировался",
        "waiting_registration": "⏳ Ожидаем подтверждение регистрации от партнёрки. Попробуйте через минуту.",
        "deposit": (
            "💰 <b>Шаг 4 — первый депозит</b>\n\n"
            "Пополните счёт в букмекерской конторе (подойдёт минимальная сумма).\n\n"
            "После пополнения нажмите «Проверить депозит» 👇"
        ),
        "btn_deposit": "💰 Пополнить счёт",
        "btn_check_deposit": "✅ Проверить депозит",
        "waiting_deposit": "⏳ Ожидаем postback депозита. Если уже пополнили — подождите 1–2 минуты.",
        "active": (
            "✅ <b>Доступ открыт!</b>\n\n"
            "📸 Отправьте скриншот события из букмекерской конторы — AI проанализирует и даст рекомендацию.\n\n"
            "💡 Также можно открыть Web App через кнопку меню внизу."
        ),
        "limit_exceeded": (
            "⏳ <b>Дневной лимит исчерпан</b>\n\n"
            "10 бесплатных анализов за 24 часа использованы.\n\n"
            "Подождите до сброса или купите безлимит ♾"
        ),
        "btn_unlimited": "♾ Купить безлимит",
        "btn_support": "💬 Написать в поддержку",
        "analyzing": "🔍 Анализирую скриншот… Это займёт 10–20 секунд.",
        "analysis_error": "❌ Не удалось прочитать скриншот. Попробуйте другое фото с чёткими коэффициентами.",
        "analysis_limit": "❌ Лимит анализов исчерпан на сегодня.",
        "analysis_funnel": "❌ Сначала пройдите воронку: подписка → регистрация → депозит.",
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
        "welcome": (
            "👋 <b>Welcome to AI Bet Analysis!</b>\n\n"
            "🤖 The bot analyzes event screenshots and suggests where to bet.\n\n"
            "🌍 Choose your language:\n"
            "💡 Change later: /language"
        ),
        "choose_language": "🌍 Choose language / Выберите язык:",
        "language_changed": "✅ Language updated",
        "subscribe_channel": (
            "📢 <b>Step 1 — channel subscription</b>\n\n"
            "Subscribe to our Telegram channel with picks and signals.\n\n"
            "1️⃣ Tap «Subscribe to channel»\n"
            "2️⃣ Join the channel\n"
            "3️⃣ Come back and tap «Check subscription» 👇"
        ),
        "btn_subscribe": "📢 Subscribe to channel",
        "btn_check_sub": "✅ Check subscription",
        "sub_check_ok": "✅ Subscription confirmed!",
        "sub_not_joined": "❌ Not subscribed yet. Join the channel and check again.",
        "get_signal": (
            "🎯 <b>Step 2 — get your link</b>\n\n"
            "Tap the button below to get your personal referral link and promo code 👇"
        ),
        "btn_get_signal": "🎯 Get signal",
        "registration": (
            "📝 <b>Step 3 — bookmaker registration</b>\n\n"
            "1️⃣ Tap «Register»\n"
            "2️⃣ Create an account via the link\n"
            "3️⃣ Use promo code: <code>{promo_code}</code>\n\n"
            "When done — tap «I registered» ✅"
        ),
        "btn_register": "📝 Register",
        "btn_check_reg": "✅ I registered",
        "waiting_registration": "⏳ Waiting for registration confirmation from the partner. Try again in a minute.",
        "deposit": (
            "💰 <b>Step 4 — first deposit</b>\n\n"
            "Top up your bookmaker account (minimum amount is fine).\n\n"
            "After depositing, tap «Check deposit» 👇"
        ),
        "btn_deposit": "💰 Make a deposit",
        "btn_check_deposit": "✅ Check deposit",
        "waiting_deposit": "⏳ Waiting for deposit postback. If you already deposited — wait 1–2 minutes.",
        "active": (
            "✅ <b>Access granted!</b>\n\n"
            "📸 Send an event screenshot from the bookmaker — AI will analyze it and give a recommendation.\n\n"
            "💡 You can also open the Web App via the menu button."
        ),
        "limit_exceeded": (
            "⏳ <b>Daily limit reached</b>\n\n"
            "10 free analyses per 24 hours used up.\n\n"
            "Wait for reset or buy unlimited ♾"
        ),
        "btn_unlimited": "♾ Buy unlimited",
        "btn_support": "💬 Contact support",
        "analyzing": "🔍 Analyzing screenshot… This takes 10–20 seconds.",
        "analysis_error": "❌ Could not read the screenshot. Try another photo with clear odds.",
        "analysis_limit": "❌ Daily analysis limit reached.",
        "analysis_funnel": "❌ Complete the funnel first: subscribe → register → deposit.",
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
                row = result.scalar_one_or_none()
                if row:
                    row.value = value
                else:
                    db.add(Translation(key=key, locale=locale, value=value))

        await db.commit()
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(run_seed())
