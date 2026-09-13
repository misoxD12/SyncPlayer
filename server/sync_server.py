import asyncio
import websockets
import json 

connected_client = set()

async def handle_client(websocket):
    connected_client.add(websocket)
    print("A client connected. Total: ", len(connected_client))

    try:
        async for message in websocket:
                data = json.loads(message)
                print("Received:", message)
                print("Type:", data["type"])

                for client in connected_client:
                     if client != websocket:
                          await client.send(message)

    finally:
         connected_client.remove(websocket)
         print("A client disconnected")

async def main():
    async with websockets.serve(handle_client, "localhost", 8765, reuse_address=True):
        await asyncio.Future()

asyncio.run(main())