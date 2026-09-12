import asyncio
import websockets

async def handle_client(websocket):
    print("A client connected")

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())