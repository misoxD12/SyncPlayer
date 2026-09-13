import asyncio
import websockets

async def connect():
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Connected to server!")
        await websocket.send("hello from B")
        await asyncio.sleep(5)

asyncio.run(connect())