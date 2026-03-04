"""Core message handling logic, channel-agnostic."""

from typing import Optional, Callable, Awaitable
from loguru import logger

from channels.base import User, Message
from storage.database import Database
from services.claude_code import _claude_service


class MessageHandler:
    """Handles message processing logic that's common across all channels."""

    def __init__(self, database: Database):
        self.db = database

    async def process_message(
        self,
        user: User,
        message_text: str,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> str:
        """Process a user message and return Claude's response.

        Args:
            user: User object
            message_text: User's message
            on_chunk: Optional callback for streaming responses

        Returns:
            Claude's response text
        """
        # Get or create user in database
        user_id = await self._get_or_create_user(user)

        # Get or create session
        session_id, claude_session_id = await self.db.get_or_create_session(user_id)

        # Get user's thinking preference
        show_thinking = await self.db.get_user_show_thinking(user_id)

        # Save user message
        await self.db.save_message(session_id, "user", message_text)

        logger.info(
            f"User {user.channel}:{user.channel_user_id} ({user.first_name}): "
            f"{message_text[:50]}..."
        )

        # Call Claude with streaming
        # 如果 claude_session_id 为 None，让 Claude Code 创建新 session
        response, new_claude_session_id = await _claude_service.ask_claude_streaming(
            message_text, session_id=claude_session_id, on_chunk=on_chunk
        )

        # Update session ID if changed
        if new_claude_session_id and new_claude_session_id != claude_session_id:
            await self.db.update_session_claude_id(session_id, new_claude_session_id)
            logger.info(
                f"Updated session {session_id} with new claude_session_id: "
                f"{new_claude_session_id}"
            )

        # Filter thinking process if user doesn't want it
        if not show_thinking:
            response = self._filter_thinking(response)
            logger.info(f"Filtered thinking process, new length: {len(response)}")

        # Save assistant response
        await self.db.save_message(session_id, "assistant", response)

        return response

    async def create_new_session(self, user: User) -> tuple[int, str]:
        """Create a new session for the user.

        Returns:
            (session_id, claude_session_id)
        """
        user_id = await self._get_or_create_user(user)
        # 不预先生成 UUID，让 Claude Code 在第一次调用时创建
        return await self.db.create_new_session(user_id)

    async def clear_session_context(self, user: User) -> None:
        """Clear current session context."""
        user_id = await self._get_or_create_user(user)
        session_id, old_claude_session_id = await self.db.get_or_create_session(
            user_id
        )
        await self.db.update_session_claude_id(session_id, None)
        logger.info(
            f"User {user.channel}:{user.channel_user_id} cleared session context: "
            f"{old_claude_session_id} -> None"
        )

    async def toggle_thinking_display(self, user: User) -> bool:
        """Toggle thinking process display for user.

        Returns:
            New setting value
        """
        user_id = await self._get_or_create_user(user)
        current_setting = await self.db.get_user_show_thinking(user_id)
        new_setting = not current_setting
        await self.db.set_user_show_thinking(user_id, new_setting)
        logger.info(
            f"User {user.channel}:{user.channel_user_id} toggled thinking display: "
            f"{current_setting} -> {new_setting}"
        )
        return new_setting

    async def get_user_sessions(self, user: User, limit: int = 10) -> list[dict]:
        """Get user's sessions."""
        user_id = await self._get_or_create_user(user)
        return await self.db.get_user_sessions(user_id, limit)

    async def get_current_session(self, user: User) -> tuple[int, str]:
        """Get current session for user.

        Returns:
            (session_id, claude_session_id)
        """
        user_id = await self._get_or_create_user(user)
        return await self.db.get_or_create_session(user_id)

    async def switch_session(self, user: User, session_id: int) -> tuple[int, str]:
        """Switch to a specific session.

        Returns:
            (session_id, claude_session_id)
        """
        return await self.db.switch_to_session(session_id)

    async def get_user_stats(self, user: User) -> dict:
        """Get user statistics."""
        user_id = await self._get_or_create_user(user)
        return await self.db.get_user_stats(user_id)

    async def _get_or_create_user(self, user: User) -> int:
        """Get or create user in database, returns user_id."""
        return await self.db.get_or_create_user(
            channel=user.channel,
            channel_user_id=user.channel_user_id,
            username=user.username,
            first_name=user.first_name,
        )

    @staticmethod
    def _filter_thinking(text: str) -> str:
        """Remove thinking blocks from text."""
        if not text:
            return text

        lines = []
        in_thinking = False

        for line in text.split("\n"):
            # Detect thinking block start
            if "💭 **思考过程：**" in line or line.strip().startswith("💭"):
                in_thinking = True
                continue

            # Detect thinking block end (separator)
            if in_thinking and line.strip() == "---":
                in_thinking = False
                continue

            # Keep line if not in thinking block
            if not in_thinking:
                lines.append(line)

        return "\n".join(lines).strip()
