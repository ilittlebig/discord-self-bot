import asyncio
import time

ACTION_COOLDOWN = 5
last_action_time = 0

async def enforce_action_cooldown():
    global last_action_time

    now = time.time()
    time_since_last_action = now - last_action_time

    if time_since_last_action < ACTION_COOLDOWN:
        delay = ACTION_COOLDOWN - time_since_last_action
        await asyncio.sleep(delay)

    last_action_time = time.time()
