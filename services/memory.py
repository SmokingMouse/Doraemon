from storage.database import Database
from loguru import logger


class MemoryService:
    """Service for managing conversation memory and context."""

    def __init__(self, db: Database):
        self.db = db

    async def get_conversation_context(
        self, session_id: int, max_messages: int = 10
    ) -> str:
        """Get recent conversation history formatted as context.

        Args:
            session_id: The session ID
            max_messages: Maximum number of recent messages to retrieve

        Returns:
            Formatted conversation history string
        """
        messages = await self.db.get_recent_messages(session_id, max_messages)

        if not messages:
            return ""

        # Format messages as conversation history
        context_lines = ["最近的对话历史："]
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"][:100]  # Truncate long messages
            if len(msg["content"]) > 100:
                content += "..."
            context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)

    async def should_summarize(self, session_id: int) -> bool:
        """Check if conversation history should be summarized.

        Future enhancement: implement smart summarization when context gets too long.
        """
        messages = await self.db.get_recent_messages(session_id, limit=100)
        return len(messages) > 50  # Placeholder logic
