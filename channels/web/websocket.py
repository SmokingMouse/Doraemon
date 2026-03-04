"""WebSocket handler for streaming messages."""

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from channels.base import User
from channels.web.auth import decode_access_token
from core.message_handler import MessageHandler


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept and store connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        """Remove connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: {user_id}")

    async def send_message(self, user_id: str, message: dict):
        """Send message to specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)


manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, message_handler: MessageHandler):
    """Handle WebSocket connection for streaming messages."""
    user_id = None

    try:
        # Accept connection first
        await websocket.accept()
        logger.info("WebSocket connection accepted")

        # Wait for authentication message
        auth_data = await websocket.receive_json()

        if auth_data.get("type") != "auth":
            await websocket.close(code=1008, reason="Authentication required")
            return

        token = auth_data.get("token")
        if not token:
            await websocket.close(code=1008, reason="Token required")
            return

        # Verify token
        try:
            user_id = decode_access_token(token)
        except Exception as e:
            logger.error(f"WebSocket auth failed: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Store connection
        manager.active_connections[user_id] = websocket
        logger.info(f"WebSocket authenticated: {user_id}")

        # Send auth success
        await websocket.send_json({"type": "auth_success", "user_id": user_id})

        # Handle messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "message":
                # User sent a message
                content = data.get("content")
                if not content:
                    await websocket.send_json(
                        {"type": "error", "message": "Content required"}
                    )
                    continue

                logger.info(f"WebSocket message from {user_id}: {content[:50]}...")

                # Create user object
                user = User(
                    channel="web",
                    channel_user_id=user_id,
                    username=user_id,
                )

                # Send thinking indicator
                await websocket.send_json(
                    {"type": "status", "status": "thinking"}
                )

                # Streaming callback
                async def on_chunk(chunk: str):
                    await websocket.send_json(
                        {"type": "chunk", "content": chunk}
                    )

                # Process message
                try:
                    response = await message_handler.process_message(
                        user, content, on_chunk=on_chunk
                    )

                    # Send completion
                    await websocket.send_json(
                        {
                            "type": "complete",
                            "content": response,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Error processing message: {str(e)}",
                        }
                    )

            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user_id:
            manager.disconnect(user_id)
