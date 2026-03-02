import aiosqlite
from pathlib import Path
from loguru import logger


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    claude_session_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """
            )
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def get_or_create_user(
        self, telegram_id: int, username: str = None, first_name: str = None
    ) -> int:
        """Get existing user or create new one. Returns user ID."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            row = await cursor.fetchone()
            if row:
                return row[0]

            cursor = await db.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (telegram_id, username, first_name),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_or_create_session(self, user_id: int) -> tuple[int, str]:
        """Get active session or create new one. Returns (session_id, claude_session_id)."""
        import uuid

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, claude_session_id FROM sessions WHERE user_id = ? ORDER BY last_active DESC LIMIT 1",
                (user_id,),
            )
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                    (row[0],),
                )
                await db.commit()
                return row[0], row[1]

            # Create new session with unique Claude session ID
            claude_session_id = str(uuid.uuid4())
            cursor = await db.execute(
                "INSERT INTO sessions (user_id, claude_session_id) VALUES (?, ?)",
                (user_id, claude_session_id),
            )
            await db.commit()
            return cursor.lastrowid, claude_session_id

    async def update_session_claude_id(self, session_id: int, new_claude_session_id: str):
        """Update the claude_session_id for a session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET claude_session_id = ? WHERE id = ?",
                (new_claude_session_id, session_id),
            )
            await db.commit()

    async def save_message(self, session_id: int, role: str, content: str):
        """Save a message to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            await db.commit()

    async def get_recent_messages(self, session_id: int, limit: int = 10) -> list[dict]:
        """Get recent messages for a session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            # Reverse to get chronological order
            return [dict(row) for row in reversed(rows)]

    async def get_user_stats(self, user_id: int) -> dict:
        """Get statistics for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            # Get total message count
            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE s.user_id = ? AND m.role = 'user'
                """,
                (user_id,),
            )
            message_count = (await cursor.fetchone())[0]

            # Get session count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)
            )
            session_count = (await cursor.fetchone())[0]

            # Get first and last activity
            cursor = await db.execute(
                """
                SELECT MIN(created_at), MAX(last_active)
                FROM sessions
                WHERE user_id = ?
                """,
                (user_id,),
            )
            first_seen, last_active = await cursor.fetchone()

            return {
                "message_count": message_count,
                "session_count": session_count,
                "first_seen": first_seen,
                "last_active": last_active,
            }
