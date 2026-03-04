import asyncio
from loguru import logger
from utils.logger import setup_logger
from config import config
from storage.database import Database
from channels.telegram import create_app as create_telegram_app
from channels.web.app import run_web_server


async def run_telegram(db: Database):
    """Run Telegram bot."""
    app = create_telegram_app(db)

    logger.info("Starting Telegram bot...")

    # Initialize and start the application
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Keep the bot running
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Stopping Telegram bot...")


async def main():
    setup_logger()
    logger.info("Starting Doraemon...")

    config.validate()

    db = Database(config.DATABASE_PATH)
    await db.init()

    # Run both Telegram and Web in parallel
    telegram_task = asyncio.create_task(run_telegram(db))
    web_task = asyncio.create_task(run_web_server(db))

    logger.info("Doraemon is running (Telegram + Web). Press Ctrl+C to stop.")

    try:
        await asyncio.gather(telegram_task, web_task)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping Doraemon...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Doraemon stopped by user")

