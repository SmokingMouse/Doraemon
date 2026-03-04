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
            # Create users table with multi-channel support
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
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

            # Create index if not exists
            try:
                await db.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_channel ON users(channel, channel_user_id)"
                )
            except Exception:
                pass  # Index already exists

            # Legacy: Check if we need to migrate from old schema
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            if "telegram_id" in column_names and "channel" not in column_names:
                logger.warning(
                    "Old database schema detected. Please run migrate_to_multichannel.py"
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
        self, telegram_id: int = None, username: str = None, first_name: str = None,
        channel: str = "telegram", channel_user_id: str = None
    ) -> int:
        """Get existing user or create new one. Returns user ID.

        Args:
            telegram_id: Legacy parameter for backward compatibility
            username: User's username
            first_name: User's first name
            channel: Channel name (telegram, web, etc.)
            channel_user_id: User ID in the channel

        Returns:
            User ID
        """
        # Backward compatibility: if telegram_id is provided, use it
        if telegram_id is not None and channel_user_id is None:
            channel = "telegram"
            channel_user_id = str(telegram_id)

        if channel_user_id is None:
            raise ValueError("Either telegram_id or channel_user_id must be provided")

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM users WHERE channel = ? AND channel_user_id = ?",
                (channel, channel_user_id),
            )
            row = await cursor.fetchone()
            if row:
                return row[0]

            cursor = await db.execute(
                "INSERT INTO users (channel, channel_user_id, username, first_name) VALUES (?, ?, ?, ?)",
                (channel, channel_user_id, username, first_name),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_or_create_session(self, user_id: int) -> tuple[int, str]:
        """Get active session or create new one. Returns (session_id, claude_session_id)."""
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

            # Create new session without claude_session_id
            # Let Claude Code create it on first message
            cursor = await db.execute(
                "INSERT INTO sessions (user_id, claude_session_id) VALUES (?, ?)",
                (user_id, None),
            )
            await db.commit()
            return cursor.lastrowid, None

    async def update_session_claude_id(self, session_id: int, new_claude_session_id: str):
        """Update the claude_session_id for a session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET claude_session_id = ? WHERE id = ?",
                (new_claude_session_id, session_id),
            )
            await db.commit()

    async def create_new_session(self, user_id: int) -> tuple[int, str]:
        """Create a new session for the user. Returns (session_id, claude_session_id)."""
        async with aiosqlite.connect(self.db_path) as db:
            # Don't generate UUID, let Claude Code create session on first message
            cursor = await db.execute(
                "INSERT INTO sessions (user_id, claude_session_id) VALUES (?, ?)",
                (user_id, None),
            )
            await db.commit()
            return cursor.lastrowid, None

    async def get_user_sessions(self, user_id: int, limit: int = 10) -> list[dict]:
        """Get user's sessions with message counts. Returns list of session info."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    s.id,
                    s.claude_session_id,
                    s.created_at,
                    s.last_active,
                    COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.user_id = ?
                GROUP BY s.id
                ORDER BY s.last_active DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def switch_to_session(self, session_id: int) -> tuple[int, str]:
        """Switch to a specific session. Returns (session_id, claude_session_id)."""
        async with aiosqlite.connect(self.db_path) as db:
            # Update last_active
            await db.execute(
                "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
            await db.commit()

            # Get session info
            cursor = await db.execute(
                "SELECT id, claude_session_id FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            if row:
                return row[0], row[1]
            else:
                raise ValueError(f"Session {session_id} not found")

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

    async def get_user_show_thinking(self, user_id: int) -> bool:
        """Get user's show_thinking preference."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT show_thinking FROM users WHERE id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return bool(row[0]) if row else True

    async def set_user_show_thinking(self, user_id: int, show_thinking: bool):
        """Set user's show_thinking preference."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET show_thinking = ? WHERE id = ?",
                (1 if show_thinking else 0, user_id),
            )
            await db.commit()
