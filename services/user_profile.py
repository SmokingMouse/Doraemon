from storage.database import Database
from loguru import logger


class UserProfileService:
    """Service for managing user profiles and statistics."""

    def __init__(self, db: Database):
        self.db = db

    async def get_profile_summary(self, user_id: int) -> str:
        """Get a formatted summary of user profile."""
        stats = await self.db.get_user_stats(user_id)

        summary_parts = []
        if stats["message_count"] > 0:
            summary_parts.append(f"已发送 {stats['message_count']} 条消息")
        if stats["session_count"] > 1:
            summary_parts.append(f"进行了 {stats['session_count']} 次会话")

        if summary_parts:
            return "用户信息：" + "，".join(summary_parts)
        return ""

    async def log_user_activity(self, user_id: int, activity: str):
        """Log user activity for future analysis."""
        logger.debug(f"User {user_id} activity: {activity}")
        # Future: store activity patterns for personalization
