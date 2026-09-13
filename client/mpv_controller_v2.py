import mpv
import time
import asyncio
import websockets
import json
import sys
import os

def create_player(video_path):
    player = mpv.MPV(
        input_default_bindings = True,
        input_vo_keyboard = True,
        osc = True
    )
    player.play(video_path)
    return player

async def consumer(queue, websocket, player):
    while True:
        event_data = await queue.get()
        
        message = json.dumps({
            "type": "pause" if event_data else "play",
            "position": player.time_pos
        })
        
        await websocket.send(message)
        print("Sent to server:", message)

async def server_listener(websocket, player):
    async for message in websocket:
        data = json.loads(message)
        print("Received from server:", data)
        
        if data["type"] == "pause":
            player.pause = True
        elif data["type"] == "play":
            player.pause = False

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    video_path = "D:/SyncPlayer/test.mp4"
    player = create_player(video_path)
    
    @player.property_observer("pause")
    def on_pause_change(name, value):
        loop.call_soon_threadsafe(queue.put_nowait, value)

    @player.event_callback("shutdown")
    def on_shutdown(event):
        print("MPV was closed, shutting down...")
        os._exit(0)
        
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("connected to server")
        
        await asyncio.gather(
            consumer(queue, websocket, player),
            server_listener(websocket, player)
        )

asyncio.run(main())