import asyncio
from loguru import logger
from utils.logger import setup_logger
from config import config
from storage.database import Database
from channels.telegram import create_app


async def main():
    setup_logger()
    logger.info("Starting Doraemon...")

    config.validate()

    db = Database(config.DATABASE_PATH)
    await db.init()

    app = create_app(db)

    logger.info("Doraemon bot is running. Press Ctrl+C to stop.")

    # Initialize and start the application
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Keep the bot running
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Stopping Doraemon...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Doraemon stopped by user")
