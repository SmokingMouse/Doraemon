"""Simple WebSocket test."""

import asyncio
import sys


async def test():
    # Start server in background
    from storage.database import Database
    from channels.web.app import create_app
    import uvicorn

    db = Database("./data/doraemon.db")
    await db.init()
    app = create_app(db)

    config = uvicorn.Config(app, host="127.0.0.1", port=8002, log_level="error")
    server = uvicorn.Server(config)

    # Run server in background
    server_task = asyncio.create_task(server.serve())

    # Wait for server to start
    await asyncio.sleep(2)

    # Test WebSocket
    try:
        import aiohttp
        import json

        # Login
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8002/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            ) as resp:
                data = await resp.json()
                token = data["access_token"]
                print(f"✅ Logged in")

            # Connect WebSocket
            async with session.ws_connect("http://localhost:8002/ws") as ws:
                print("✅ WebSocket connected")

                # Auth
                await ws.send_json({"type": "auth", "token": token})
                auth_resp = await ws.receive_json()
                print(f"✅ Authenticated: {auth_resp}")

                # Send message
                print("\n📤 Sending: 'What is 1+1?'")
                await ws.send_json({"type": "message", "content": "What is 1+1?"})

                # Receive response
                print("📥 Response:")
                while True:
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=60)

                    if msg["type"] == "status":
                        print(f"  Status: {msg['status']}")
                    elif msg["type"] == "chunk":
                        print(msg["content"], end="", flush=True)
                    elif msg["type"] == "complete":
                        print(f"\n\n✅ Complete!")
                        break
                    elif msg["type"] == "error":
                        print(f"\n❌ Error: {msg['message']}")
                        break

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop server
        server.should_exit = True
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test())
