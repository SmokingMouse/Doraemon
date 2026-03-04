"""Pydantic models for Web API."""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: str


class SessionInfo(BaseModel):
    id: int
    claude_session_id: str
    created_at: str
    last_active: str
    message_count: int


class CreateSessionResponse(BaseModel):
    session_id: int
    claude_session_id: str
