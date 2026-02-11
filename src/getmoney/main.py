"""Main entry point for GetMoney Telegram Bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from getmoney.config import settings
from getmoney.db import init_db
from getmoney.handlers import setup_routers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Actions to perform on bot startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    # Notify admin that bot is online
    try:
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text="🟢 Бот запущен и готов к работе!",
        )
    except Exception as e:
        logger.warning(f"Could not notify admin: {e}")

    logger.info("Bot started successfully!")


async def on_shutdown(bot: Bot) -> None:
    """Actions to perform on bot shutdown."""
    logger.info("Shutting down bot...")

    try:
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text="🔴 Бот остановлен.",
        )
    except Exception:
        pass

    logger.info("Bot stopped.")


async def main() -> None:
    """Main function to run the bot."""
    logger.info("Starting GetMoney Bot...")

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher with memory storage for FSM
    dp = Dispatcher(storage=MemoryStorage())

    # Setup routers
    dp.include_router(setup_routers())

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting long polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
