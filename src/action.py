import asyncio
import time
from logger import log_info

ACTION_COOLDOWN = 3

last_action_time = 0
lock = asyncio.Lock()

async def enforce_action_cooldown():
    global last_action_time

    async with lock:
        now = time.time()
        time_since_last_action = now - last_action_time

        if time_since_last_action < ACTION_COOLDOWN:
            delay = ACTION_COOLDOWN - time_since_last_action
            log_info(f"Cooldown started. Waiting for {delay:.2f} seconds.")
            await asyncio.sleep(delay)

        last_action_time = time.time()
