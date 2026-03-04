"""Database migration script to support multi-channel users.

This script migrates the database schema from single-channel (Telegram only)
to multi-channel support.

Changes:
- Rename telegram_id to channel_user_id
- Add channel column (default 'telegram')
- Create unique index on (channel, channel_user_id)
"""

import asyncio
import aiosqlite
from pathlib import Path
from loguru import logger


async def migrate_database(db_path: str):
    """Migrate database to support multi-channel."""
    logger.info(f"Starting database migration for: {db_path}")

    async with aiosqlite.connect(db_path) as db:
        # Check if migration is needed
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "channel" in column_names:
            logger.info("Database already migrated, skipping")
            return

        logger.info("Starting migration...")

        # Step 1: Create new users table with multi-channel support
        await db.execute(
            """
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL DEFAULT 'telegram',
                channel_user_id TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                show_thinking INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(channel, channel_user_id)
            )
        """
        )
        logger.info("Created new users table")

        # Step 2: Copy data from old table (handle missing columns)
        # Check if show_thinking column exists
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        has_show_thinking = "show_thinking" in column_names

        if has_show_thinking:
            await db.execute(
                """
                INSERT INTO users_new (id, channel, channel_user_id, username, first_name, show_thinking, created_at)
                SELECT id, 'telegram', CAST(telegram_id AS TEXT), username, first_name, show_thinking, created_at
                FROM users
            """
            )
        else:
            await db.execute(
                """
                INSERT INTO users_new (id, channel, channel_user_id, username, first_name, created_at)
                SELECT id, 'telegram', CAST(telegram_id AS TEXT), username, first_name, created_at
                FROM users
            """
            )
        logger.info("Copied data from old table")

        # Step 3: Drop old table and rename new table
        await db.execute("DROP TABLE users")
        await db.execute("ALTER TABLE users_new RENAME TO users")
        logger.info("Replaced old table with new table")

        # Step 4: Create index
        await db.execute(
            "CREATE UNIQUE INDEX idx_user_channel ON users(channel, channel_user_id)"
        )
        logger.info("Created index on (channel, channel_user_id)")

        await db.commit()
        logger.info("Migration completed successfully")


async def main():
    import sys

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default path
        db_path = "./data/doraemon.db"

    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        return

    await migrate_database(db_path)


if __name__ == "__main__":
    asyncio.run(main())
