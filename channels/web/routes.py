"""REST API routes for Web channel."""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from channels.base import User
from channels.web.auth import get_current_user, verify_user, create_access_token
from channels.web.models import (
    LoginRequest,
    LoginResponse,
    SessionInfo,
    CreateSessionResponse,
    MessageResponse,
)
from core.message_handler import MessageHandler
from storage.database import Database


router = APIRouter()


# Global instances (will be set by app.py)
db: Database = None
message_handler: MessageHandler = None


def set_dependencies(database: Database, handler: MessageHandler):
    """Set global dependencies."""
    global db, message_handler
    db = database
    message_handler = handler


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get JWT token."""
    if not verify_user(request.username, request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Use username as user_id for web channel
    access_token = create_access_token(request.username)

    logger.info(f"User logged in: {request.username}")

    return LoginResponse(access_token=access_token)


@router.get("/sessions", response_model=list[SessionInfo])
async def get_sessions(user_id: str = Depends(get_current_user)):
    """Get user's sessions."""
    user = User(
        channel="web",
        channel_user_id=user_id,
        username=user_id,
    )

    sessions = await message_handler.get_user_sessions(user, limit=20)

    return [
        SessionInfo(
            id=s["id"],
            claude_session_id=s["claude_session_id"] or "",
            created_at=s["created_at"],
            last_active=s["last_active"],
            message_count=s["message_count"],
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(user_id: str = Depends(get_current_user)):
    """Create a new session."""
    user = User(
        channel="web",
        channel_user_id=user_id,
        username=user_id,
    )

    session_id, claude_session_id = await message_handler.create_new_session(user)

    logger.info(f"User {user_id} created new session: {claude_session_id}")

    return CreateSessionResponse(
        session_id=session_id,
        claude_session_id=claude_session_id or "",
    )


@router.get("/messages/{session_id}", response_model=list[MessageResponse])
async def get_messages(
    session_id: int,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """Get messages for a session."""
    messages = await db.get_recent_messages(session_id, limit=limit)

    return [
        MessageResponse(
            role=m["role"],
            content=m["content"],
            created_at=m["created_at"],
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user_id: str = Depends(get_current_user),
):
    """Delete a session."""
    # TODO: Add permission check - verify session belongs to user
    await db.delete_session(session_id)
    logger.info(f"User {user_id} deleted session: {session_id}")
    return {"status": "success"}
