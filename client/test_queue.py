import asyncio
import threading
import time

def background_worker(queue, loop):
    for i in range(5):
        time.sleep(1)
        loop.call_soon_threadsafe(queue.put_nowait, f"event {i}")

async def consumer(queue):
    while True:
        item = await queue.get()
        print("Got from queue:", item)

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    threading.Thread(target=background_worker, args=(queue, loop)).start()

    await consumer(queue)

asyncio.run(main())
