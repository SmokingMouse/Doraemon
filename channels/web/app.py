"""FastAPI application for Web channel."""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import config
from storage.database import Database
from core.message_handler import MessageHandler
from channels.web import routes, websocket


def create_app(database: Database) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Doraemon Web API",
        description="Web interface for Doraemon AI assistant",
        version="1.0.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.WEB_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize message handler
    message_handler = MessageHandler(database)

    # Set dependencies for routes
    routes.set_dependencies(database, message_handler)

    # Register routes
    app.include_router(routes.router, prefix="/api", tags=["api"])

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await websocket.handle_websocket(ws, message_handler)

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    logger.info("FastAPI app created")

    return app


async def run_web_server(database: Database):
    """Run the web server."""
    import uvicorn

    app = create_app(database)

    logger.info(f"Starting web server on {config.WEB_HOST}:{config.WEB_PORT}")

    config_uvicorn = uvicorn.Config(
        app,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        log_level="info",
    )

    server = uvicorn.Server(config_uvicorn)
    await server.serve()
