import subprocess
import time
import json

def send_command(pipe, command_list):
    request = json.dumps({"command": command_list}) + "\n"
    pipe.write(request.encode("utf-8"))

    while True:
        response = pipe.readline()
        response_data = json.loads(response.decode("utf-8"))

        if"error" in response_data:
            return response_data

def play(pipe):
    return send_command(pipe, ["set_property", "pause", False])

def pause(pipe):
    return send_command(pipe, ["set_property", "pause", True])

def seek(pipe, seconds):
    return send_command(pipe, ["set_property", "time-pos", seconds])

def get_time_pos(pipe):
    response = send_command(pipe, ["get_property", "time-pos"])
    return response["data"]

video_path = "D:/SyncPlayer/test.mp4"
ipc_path = r"\\.\pipe\mpvsocket"

process = subprocess.Popen(
    ["mpv", video_path, f"--input-ipc-server={ipc_path}", "--idle=yes"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
    )   
    
time.sleep(1)
pipe = open(ipc_path, "r+b", buffering=0)

print("mpv connected")

play(pipe)
time.sleep(3)

current_time = get_time_pos(pipe)
print("Current position:", current_time)

pause(pipe)
print("paused")