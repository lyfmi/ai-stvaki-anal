import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import settings
from app.handlers import user as user_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    if not settings.bot_token or settings.bot_token.startswith("000000:"):
        logger.warning("BOT_TOKEN not configured — skipping webhook setup")
        return
    webhook_url = f"{settings.public_base_url.rstrip('/')}{settings.webhook_path}"
    await bot.set_webhook(webhook_url)
    logger.info("Webhook set to %s", webhook_url)


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()


def main() -> None:
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(user_handlers.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=settings.webhook_host, port=settings.webhook_port)


if __name__ == "__main__":
    main()
