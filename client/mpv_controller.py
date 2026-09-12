import subprocess
import time
import json

video_path = "D:/SyncPlayer/test.mp4"
ipc_path = r"\\.\pipe\mpvsocket"

process = subprocess.Popen(
    ["mpv", video_path, f"--input-ipc-server={ipc_path}", "--idle=yes"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
    )   
    
time.sleep(1)
pipe = open(ipc_path, "r+b", buffering=0)

print("mpv connected")

command = json.dumps({"command":["set_property", "pause", True]}) + "\n"
pipe.write(command.encode("utf-8"))

response = pipe.readline()
print(response)

response_text = response.decode("utf-8")
response_data = json.loads(response_text)
print(response_data)