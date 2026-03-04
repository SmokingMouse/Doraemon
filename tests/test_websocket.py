"""Test WebSocket messaging."""

import asyncio
import json
import websockets


async def test_websocket():
    """Test WebSocket connection and messaging."""
    # Get token first
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(
            "http://localhost:8765/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        ) as resp:
            data = await resp.json()
            token = data["access_token"]
            print(f"✅ Logged in, token: {token[:20]}...")

    # Connect to WebSocket
    uri = "ws://localhost:8765/ws"

    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket connected")

        # Send auth
        await websocket.send(json.dumps({
            "type": "auth",
            "token": token
        }))

        # Receive auth response
        auth_response = await websocket.recv()
        print(f"Auth response: {auth_response}")

        # Send a message
        print("\n📤 Sending message: 'Hello, what's 1+1?'")
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Hello, what's 1+1?"
        }))

        # Receive streaming response
        print("\n📥 Receiving response:")
        accumulated = ""

        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
                data = json.loads(response)

                if data["type"] == "status":
                    print(f"Status: {data['status']}")

                elif data["type"] == "chunk":
                    chunk = data["content"]
                    accumulated += chunk
                    print(chunk, end="", flush=True)

                elif data["type"] == "complete":
                    print(f"\n\n✅ Complete! Total length: {len(data['content'])} chars")
                    break

                elif data["type"] == "error":
                    print(f"\n❌ Error: {data['message']}")
                    break

            except asyncio.TimeoutError:
                print("\n⏱️ Timeout waiting for response")
                break


if __name__ == "__main__":
    asyncio.run(test_websocket())
