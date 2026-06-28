from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def language_keyboard() -> InlineKeyboardMarkup:
    langs = [
        ("🇷🇺 Русский", "lang:ru"),
        ("🇬🇧 English", "lang:en"),
    ]
    buttons = [[InlineKeyboardButton(text=t, callback_data=d)] for t, d in langs]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscription_keyboard(channel_url: str, t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t.get("btn_subscribe", "Subscribe"), url=channel_url)],
            [InlineKeyboardButton(text=t.get("btn_check_sub", "Check"), callback_data="check_sub")],
        ]
    )


def get_signal_keyboard(t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t.get("btn_get_signal", "Get signal"), callback_data="get_signal")]]
    )


def registration_keyboard(ref_url: str, t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t.get("btn_register", "Register"), url=ref_url)],
            [InlineKeyboardButton(text=t.get("btn_check_reg", "I registered"), callback_data="check_reg")],
        ]
    )


def deposit_keyboard(ref_url: str, t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t.get("btn_deposit", "Deposit"), url=ref_url)],
            [InlineKeyboardButton(text=t.get("btn_check_deposit", "Check deposit"), callback_data="check_deposit")],
        ]
    )


def active_keyboard(
    webapp_url: str,
    payment_url: str | None,
    t: dict,
    *,
    show_unlimited: bool = True,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t.get("btn_open_webapp", "Open Mini App"),
                web_app=WebAppInfo(url=webapp_url),
            )
        ],
    ]
    if show_unlimited and payment_url:
        rows.append([InlineKeyboardButton(text=t.get("btn_unlimited", "Unlimited"), url=payment_url)])
    rows.append([InlineKeyboardButton(text=t.get("btn_change_language", "Change language"), callback_data="show_language")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def limit_keyboard(support_url: str, payment_url: str | None, t: dict) -> InlineKeyboardMarkup:
    rows = []
    if payment_url:
        rows.append([InlineKeyboardButton(text=t.get("btn_unlimited", "Unlimited"), url=payment_url)])
    rows.append([InlineKeyboardButton(text=t.get("btn_support", "Support"), url=support_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_keyboard(t: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t.get("admin_stats", "Stats"), callback_data="admin:stats"),
                InlineKeyboardButton(text=t.get("admin_postback", "Postback"), callback_data="admin:postback"),
            ],
            [
                InlineKeyboardButton(text=t.get("admin_unlimited", "Unlimited"), callback_data="admin:unlimited"),
            ],
        ]
    )
