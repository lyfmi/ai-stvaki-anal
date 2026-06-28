import httpx
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.api_client import BackendClient
from app.config import settings
from app.keyboards.inline import (
    active_keyboard,
    admin_keyboard,
    deposit_keyboard,
    get_signal_keyboard,
    language_keyboard,
    limit_keyboard,
    registration_keyboard,
    subscription_keyboard,
)
from app.utils.affiliate import build_affiliate_url
from app.utils.formatters import clear_translation_cache, format_analysis, get_t

router = Router()
backend = BackendClient()


async def _send_step(message: Message, text: str, reply_markup, *, edit: bool = False) -> None:
    if edit:
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=reply_markup)


async def show_funnel_step(
    message: Message,
    telegram_id: int,
    user: dict | None = None,
    *,
    edit: bool = False,
):
    if user is None:
        user = await backend.get_user(telegram_id)
    locale = user.get("language") or "ru"
    t = await get_t(locale)
    app_settings = await backend.get_settings()
    state = user.get("funnel_state", "NEW")

    if state == "NEW":
        await _send_step(message, t.get("welcome", "Welcome"), language_keyboard(), edit=edit)
        return

    if state == "LANGUAGE_SELECTED":
        await _send_step(
            message,
            t.get("subscribe_channel", "Subscribe"),
            subscription_keyboard(app_settings.get("channel_url", "https://t.me/example"), t),
            edit=edit,
        )
        return

    if state in ("CHANNEL_SUBSCRIBED", "REGISTRATION_PENDING"):
        await _send_step(
            message,
            t.get("get_signal", "Get signal"),
            get_signal_keyboard(t),
            edit=edit,
        )
        return

    if state in ("REGISTERED", "DEPOSIT_PENDING"):
        promo = app_settings.get("affiliate_promo_code", "")
        ref_url = build_affiliate_url(
            app_settings.get("affiliate_ref_url", "https://example.com"),
            app_settings.get("affiliate_sub_param", "sub1"),
            telegram_id,
        )
        if state == "DEPOSIT_PENDING":
            text = t.get("deposit", "Deposit")
            keyboard = deposit_keyboard(ref_url, t)
        else:
            text = t.get("registration", "Register").format(promo_code=promo)
            keyboard = registration_keyboard(ref_url, t)
        await _send_step(message, text, keyboard, edit=edit)
        return

    if state in ("ACTIVE", "UNLIMITED"):
        await _send_step(
            message,
            t.get("active", "Send screenshot"),
            active_keyboard(app_settings.get("support_url", "https://t.me/support"), t),
            edit=edit,
        )
        return

    if state == "LIMIT_EXCEEDED":
        payment_url = None
        try:
            payment = await backend.create_unlimited_payment(telegram_id)
            payment_url = payment.get("webapp_payment_url") or payment.get("payment_url")
        except Exception:
            pass
        await _send_step(
            message,
            t.get("limit_exceeded", "Limit exceeded"),
            limit_keyboard(
                app_settings.get("support_url", "https://t.me/support"),
                payment_url,
                t,
            ),
            edit=edit,
        )


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await backend.get_user(message.from_user.id)
    await show_funnel_step(message, message.from_user.id, user)


@router.message(Command("language"))
async def cmd_language(message: Message):
    user = await backend.get_user(message.from_user.id)
    locale = user.get("language") or "ru"
    t = await get_t(locale)
    await message.answer(t.get("choose_language", "Choose language:"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def on_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    clear_translation_cache(lang)
    user = await backend.set_language(callback.from_user.id, lang)
    await get_t(lang, force=True)
    t = await get_t(lang)
    await callback.answer(t.get("language_changed", "OK")[:200])
    if user.get("funnel_state") == "NEW":
        await show_funnel_step(callback.message, callback.from_user.id, user, edit=True)
    else:
        await show_funnel_step(callback.message, callback.from_user.id, user, edit=True)


@router.callback_query(F.data == "check_sub")
async def on_check_sub(callback: CallbackQuery):
    prev_state = (await backend.get_user(callback.from_user.id)).get("funnel_state")
    user = await backend.check_subscription(callback.from_user.id)
    t = await get_t(user.get("language") or "ru")
    if user.get("funnel_state") != prev_state:
        await callback.answer(t.get("sub_check_ok", "OK"))
        await show_funnel_step(callback.message, callback.from_user.id, user, edit=True)
    else:
        await callback.answer(t.get("sub_not_joined", "Not subscribed"), show_alert=True)


@router.callback_query(F.data == "get_signal")
async def on_get_signal(callback: CallbackQuery):
    user = await backend.get_user(callback.from_user.id)
    t = await get_t(user.get("language") or "ru")
    app_settings = await backend.get_settings()
    promo = app_settings.get("affiliate_promo_code", "")
    ref_url = build_affiliate_url(
        app_settings.get("affiliate_ref_url", "https://example.com"),
        app_settings.get("affiliate_sub_param", "sub1"),
        callback.from_user.id,
    )
    text = t.get("registration", "Register").format(promo_code=promo)
    await callback.message.edit_text(text, reply_markup=registration_keyboard(ref_url, t))
    await callback.answer()


@router.callback_query(F.data == "check_reg")
async def on_check_reg(callback: CallbackQuery):
    user = await backend.get_user(callback.from_user.id)
    t = await get_t(user.get("language") or "ru")
    if user.get("is_registered"):
        await callback.answer(t.get("registered_ok", "OK"))
        await show_funnel_step(callback.message, callback.from_user.id, user, edit=True)
    else:
        await callback.answer(t.get("waiting_registration", "Waiting..."), show_alert=True)


@router.callback_query(F.data == "check_deposit")
async def on_check_deposit(callback: CallbackQuery):
    user = await backend.get_user(callback.from_user.id)
    t = await get_t(user.get("language") or "ru")
    if user.get("is_deposited"):
        await callback.answer(t.get("deposit_ok", "OK"))
        await show_funnel_step(callback.message, callback.from_user.id, user, edit=True)
    else:
        await callback.answer(t.get("waiting_deposit", "Waiting..."), show_alert=True)


@router.message(F.photo)
async def on_photo(message: Message, bot: Bot):
    telegram_id = message.from_user.id
    user = await backend.get_user(telegram_id)
    locale = user.get("language") or "ru"
    t = await get_t(locale)

    status = await backend.get_status(telegram_id)
    if not status.get("can_analyze") and telegram_id not in settings.admin_ids:
        if not user.get("is_deposited"):
            await message.answer(t.get("analysis_funnel", "Complete funnel"))
            await show_funnel_step(message, telegram_id, user)
        else:
            await message.answer(t.get("analysis_limit", "Limit exceeded"))
        return

    await message.answer(t.get("analyzing", "Analyzing..."))
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read()

    try:
        result = await backend.analyze(telegram_id, content, "photo.jpg")
        await message.answer(format_analysis(result, locale))
    except httpx.HTTPStatusError as e:
        detail = "Error"
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        if e.response.status_code == 422:
            await message.answer(t.get("analysis_error", detail))
        elif e.response.status_code == 403:
            await message.answer(t.get("analysis_limit", detail))
        else:
            await message.answer(f"❌ {detail}")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    t = await get_t("ru")
    await message.answer(t.get("admin_menu", "Admin"), reply_markup=admin_keyboard(t))


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        return
    stats = await backend.admin_stats(callback.from_user.id)
    text = (
        f"📊 Статистика\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"📝 Регистраций: {stats['registered_users']}\n"
        f"💰 Депозитов: {stats['deposited_users']}\n"
        f"♾ Безлимит: {stats['unlimited_users']}\n"
        f"🔍 Анализов: {stats['total_analyses']} (сегодня: {stats['analyses_today']})"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin:postback")
async def admin_postback(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        return
    urls = await backend.admin_postback_urls(callback.from_user.id)
    text = f"Registration:\n{urls['registration'].replace('{telegram_id}', str(callback.from_user.id))}\n\nDeposit:\n{urls['deposit'].replace('{telegram_id}', str(callback.from_user.id))}"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin:unlimited")
async def admin_unlimited(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        return
    await callback.message.answer("Перешлите сообщение пользователя или отправьте его Telegram ID для выдачи безлимита.")
    await callback.answer()


@router.message(F.forward_from)
async def admin_grant_forward(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    target_id = message.forward_from.id
    await backend.grant_unlimited(message.from_user.id, target_id)
    await message.answer(f"♾ Безлимит выдан пользователю {target_id}")


@router.message(F.text.regexp(r"^\d+$"))
async def admin_grant_id(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    target_id = int(message.text)
    await backend.grant_unlimited(message.from_user.id, target_id)
    await message.answer(f"♾ Безлимит выдан пользователю {target_id}")
