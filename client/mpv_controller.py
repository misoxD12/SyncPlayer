import subprocess
import time
import json
import asyncio
import threading
import websockets
import sys  
import win32file

pending_responses = {}
response_ready = {}
request_id_counter = 0

initial_skipped= set()
request_lock = threading.Lock()

def reader_thread(pipe, event_queue, loop):
    buffer = b""
    while True:
        result, data = win32file.ReadFile(pipe, 4096)
        buffer += data
        while b"\n" in buffer:
            line,buffer = buffer.split(b"\n",1)
            if not line.strip():
                continue

            data_json = json.loads(line.decode("utf-8"))

            if "request_id" in data_json:
                request_id = data_json["request_id"]
                pending_responses[request_id] = data_json
                if request_id in response_ready:
                    response_ready[request_id].set()
            elif data_json.get("event") == "property-change":
                prop_id = data_json["id"]
                if prop_id not in initial_skipped:
                    initial_skipped.add(prop_id)
                    continue
                loop.call_soon_threadsafe(event_queue.put_nowait, data_json)        

def send_command(pipe, command_list):
    global request_id_counter

    with request_lock:
        request_id_counter += 1
        request_id = request_id_counter
        response_ready[request_id] = threading.Event()

    request = json.dumps({"command": command_list, "request_id": request_id}) + "\n"
    win32file.WriteFile(pipe, request.encode("utf-8"))
    response_ready[request_id].wait()

    response = pending_responses.pop(request_id)
    del response_ready[request_id]
    return response

def keepalive(pipe):
    while True:
        time.sleep(1)
        try:
            send_command(pipe, ["get_property", "time-pos"])
        except Exception:
            pass                        

def connect_to_mpvpipe(ipc_path, retries=20, delay=0.25):
    for attempt in range(retries):
        try:
            handle = win32file.CreateFile(
                ipc_path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            return handle
        except Exception:
            time.sleep(delay)
    raise RuntimeError("could not connect")

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
        print("Raw event:", event)

        message = json.dumps({
            "type": "pause" if event["data"] else "play",
            "position": get_time_pos(pipe)
        })

        await websocket.send(message)
        print("Sent to server:", message)

async def server_listener(websocket, pipe):
    async for message in websocket:
        data = json.loads(message)
        print("Received from server:", data)

        if data["type"] == "pause":
            pause(pipe)
        elif data["type"] == "play":
            play(pipe)    

video_path = "D:/SyncPlayer/test.mp4"
client_id = sys.argv[1] if len(sys.argv) > 1 else "1"
ipc_path = rf"\\.\pipe\mpvsocket_{client_id}"

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    process = subprocess.Popen(
        ["mpv", video_path, f"--input-ipc-server={ipc_path}", "--idle=yes", "--no-audio"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )   
        
    time.sleep(1)
    pipe = connect_to_mpvpipe(ipc_path)

    print("mpv connected", flush=True)

    threading.Thread(target=reader_thread, args=(pipe, queue, loop)).start()
    threading.Thread(target=keepalive, args=(pipe,)).start()
    print(f"[{time.time():.2f}] about to send observe_property")
    send_command(pipe, ["observe_property", 1, "pause"])
    print(f"[{time.time():.2f}] observe_property confirmed")
   

    async with websockets.connect("ws://localhost:8765") as websocket:
        print("connected to server")  

        await asyncio.gather(
            consumer(queue, websocket, pipe),
            server_listener(websocket, pipe)
        )

asyncio.run(main())