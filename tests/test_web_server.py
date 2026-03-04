"""Simple test script for Web API."""

import asyncio
import sys


async def test_web_api():
    from storage.database import Database
    from channels.web.app import create_app
    import uvicorn

    # Initialize database
    db = Database("./data/doraemon.db")
    await db.init()

    # Create app
    app = create_app(db)

    print("✅ Web app created successfully")
    print("Starting server on http://localhost:8765")
    print("Test with: curl http://localhost:8765/health")

    # Run server
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(test_web_api())
    except KeyboardInterrupt:
        print("\nServer stopped")
