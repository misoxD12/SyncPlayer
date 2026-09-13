import subprocess
import time
import json
import asyncio
import threading
import websockets

pending_responses = {}
response_ready = {}
request_id_counter = 0

def reader_thread(pipe, event_queue, loop):
    while True:
        line = pipe.readline()
        data = json.loads(line.decode("utf-8"))

        if "request_id" in data:
            request_id = data["request_id"]
            pending_responses[request_id] = data
            if request_id in response_ready:
                response_ready[request_id].set()
        elif data.get("event") == "property-change":
            loop.call_soon_threadsafe(event_queue.put_nowait, data)        

def send_command(pipe, command_list):
    global request_id_counter
    request_id_counter += 1
    request_id = request_id_counter

    response_ready[request_id] = threading.Event()

    request = json.dumps({"command": command_list, "request_id": request_id}) + "\n"
    pipe.write(request.encode("utf-8"))

    response_ready[request_id].wait()

    response = pending_responses.pop(request_id)
    del response_ready[request_id]
    return response

def play(pipe):
    return send_command(pipe, ["set_property", "pause", False])

def pause(pipe):
    return send_command(pipe, ["set_property", "pause", True])

def seek(pipe, seconds):
    return send_command(pipe, ["set_property", "time-pos", seconds])

def get_time_pos(pipe):
    response = send_command(pipe, ["get_property", "time-pos"])
    return response["data"]

async def consumer(queue, websocket, pipe):
    while True:
        event = await queue.get()

        message = json.dumps({
            "type": "pause" if event["data"] else "play",
            "position": get_time_pos(pipe)
        })

        await websocket.send(message)
        print("Sent to server:", message)

video_path = "D:/SyncPlayer/test.mp4"
ipc_path = r"\\.\pipe\mpvsocket"

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    process = subprocess.Popen(
        ["mpv", video_path, f"--input-ipc-server={ipc_path}", "--idle=yes"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )   
        
    time.sleep(1)
    pipe = open(ipc_path, "r+b", buffering=0)

    print("mpv connected")

    threading.Thread(target=reader_thread, args=(pipe, queue, loop)).start()
    send_command(pipe, ["observe_property", 1, "pause"])

    async with websockets.connect("ws://localhost:8765") as websocket:
        print("connected to server")        
        await consumer(queue, websocket, pipe)

asyncio.run(main())