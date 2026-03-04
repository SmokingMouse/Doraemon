"""Test script for Web API."""

import asyncio
from storage.database import Database
from channels.web.app import create_app


async def main():
    # Initialize database
    db = Database("./data/doraemon.db")
    await db.init()

    # Create app
    app = create_app(db)

    print("✅ Web app created successfully")
    print(f"Routes: {[route.path for route in app.routes]}")


if __name__ == "__main__":
    asyncio.run(main())
