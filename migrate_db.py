#!/usr/bin/env python3
"""
Database migration script to add claude_session_id to sessions table.
Run this if you have an existing database from Phase 1.
"""
import asyncio
import aiosqlite
import sys
from pathlib import Path


async def migrate():
    db_path = "./data/doraemon.db"

    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("No migration needed - database will be created with correct schema.")
        return

    print(f"Migrating database at {db_path}...")

    async with aiosqlite.connect(db_path) as db:
        # Check if column already exists
        cursor = await db.execute("PRAGMA table_info(sessions)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "claude_session_id" in column_names:
            print("✓ Database already migrated")
            return

        # Add the new column (without UNIQUE constraint first)
        await db.execute("ALTER TABLE sessions ADD COLUMN claude_session_id TEXT")

        # Generate UUIDs for existing sessions
        import uuid

        cursor = await db.execute("SELECT id FROM sessions")
        sessions = await cursor.fetchall()

        for (session_id,) in sessions:
            claude_session_id = str(uuid.uuid4())
            await db.execute(
                "UPDATE sessions SET claude_session_id = ? WHERE id = ?",
                (claude_session_id, session_id),
            )

        await db.commit()
        print(f"✓ Migrated {len(sessions)} sessions")
        print("✓ Migration complete!")


if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
