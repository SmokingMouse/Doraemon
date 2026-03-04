"""Base channel interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable


@dataclass
class User:
    """Universal user representation across channels."""
    channel: str  # "telegram", "web", etc.
    channel_user_id: str  # User ID in the channel (telegram_id, web user_id, etc.)
    username: Optional[str] = None
    first_name: Optional[str] = None


@dataclass
class Message:
    """Universal message representation."""
    content: str
    role: str  # "user" or "assistant"


class BaseChannel(ABC):
    """Abstract base class for all channels."""

    @abstractmethod
    async def send_message(self, user: User, message: str) -> None:
        """Send a complete message to the user."""
        pass

    @abstractmethod
    async def send_streaming_message(
        self,
        user: User,
        on_chunk: Callable[[str], Awaitable[None]],
    ) -> None:
        """Send a streaming message with real-time updates."""
        pass

    @abstractmethod
    def is_authorized(self, user: User) -> bool:
        """Check if user is authorized to use the bot."""
        pass
