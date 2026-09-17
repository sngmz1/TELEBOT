import asyncio
import logging
import os
import signal

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import (
    BOT_TOKEN,
    WEBHOOK_BASE_URL,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
)
from app.database.db import init_db
from app.handlers import start, services, orders, profile, more, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    try:
        await bot.set_webhook(
            url=f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET or None,
        )
    except Exception as exc:
        logger.error("Failed to set Telegram webhook: %s", exc)
        raise


async def on_shutdown(bot: Bot) -> None:
    try:
        await bot.delete_webhook()
    except Exception as exc:
        logger.warning("Failed to delete Telegram webhook on shutdown: %s", exc)
    await bot.session.close()


def _parse_port(raw: str) -> int | None:
    try:
        port = int(raw)
    except (TypeError, ValueError):
        logger.error("Invalid PORT value: %r", raw)
        return None
    if not (0 < port < 65536):
        logger.error("PORT out of range: %s", port)
        return None
    return port


async def main() -> int:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Check your .env file.")
        return 1

    if not WEBHOOK_BASE_URL:
        logger.error("WEBHOOK_BASE_URL is not set. Check your .env file.")
        return 1

    port = _parse_port(os.getenv("PORT", "8080"))
    if port is None:
        return 1

    try:
        await init_db()
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        return 1
    logger.info("Database initialized.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_routers(
        start.router,
        services.router,
        orders.router,
        profile.router,
        more.router,
        admin.router,
    )

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET or None,
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    async def health(request: web.Request) -> web.Response:
        return web.Response(text="Bot is running.")

    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    try:
        await runner.setup()
        site = web.TCPSite(runner, WEBHOOK_HOST, port)
        await site.start()
    except Exception as exc:
        logger.error("Failed to start webhook server on %s:%s: %s", WEBHOOK_HOST, port, exc)
        try:
            await runner.cleanup()
        except Exception:
            pass
        await bot.session.close()
        return 1

    logger.info("Webhook server started on %s:%s%s", WEBHOOK_HOST, port, WEBHOOK_PATH)
    logger.info("Telegram webhook URL: %s%s", WEBHOOK_BASE_URL, WEBHOOK_PATH)

    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_shutdown)
        except (NotImplementedError, RuntimeError):
            break

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass

    try:
        await runner.cleanup()
    except Exception as exc:
        logger.warning("Error while shutting down the webhook server: %s", exc)

    logger.info("Bot stopped.")
    return 0


if __name__ == "__main__":
    try:
        code = asyncio.run(main())
    except KeyboardInterrupt:
        code = 0
    raise SystemExit(code)