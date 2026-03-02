from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    created_at: Optional[datetime] = None


class Session(BaseModel):
    id: Optional[int] = None
    user_id: int
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None


class Message(BaseModel):
    id: Optional[int] = None
    session_id: int
    role: str  # 'user' or 'assistant'
    content: str
    created_at: Optional[datetime] = None
