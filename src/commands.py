import random
import discord
import os
import json
import time
import asyncio
from logger import log_error, log_info
from discord.ext import tasks

GUILD_ID = "219564597349318656"
CHANNEL_ID = "627217930576199690"

COMMAND_USAGE_FILE = "command_usage.json"
COMMAND_PROBABILITY = 0.15
CHILLZONE_COMMAND_COOLDOWNS = {
    ".p": 900,
    ".v": 900,
    ".cc": 900,
    ".ac": 900,
    ".put all": 900,
    ".work": 900,
    ".world": 900,
    ".fame": 900,
}

last_command_usage = None

def load_command_usage():
    if not os.path.exists(COMMAND_USAGE_FILE):
        return {}

    try:
        with open(COMMAND_USAGE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Error loading {COMMAND_USAGE_FILE}: {e}")
        return {}


def save_command_usage(data: dict):
    try:
        with open(COMMAND_USAGE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        log_error(f"Error saving {COMMAND_USAGE_FILE}: {e}")


@tasks.loop(seconds=60)
async def periodic_chillzone_commands(client):
    global last_command_usage
    if last_command_usage is None:
        last_command_usage = load_command_usage()

    if random.random() > COMMAND_PROBABILITY:
        return

    guild = discord.utils.get(client.guilds, id=int(GUILD_ID))
    if not guild:
        return

    channel = discord.utils.get(guild.text_channels, id=int(CHANNEL_ID))
    if not channel:
        return

    possible_commands = list(CHILLZONE_COMMAND_COOLDOWNS.keys())
    random.shuffle(possible_commands)
    now = time.time()

    for command in possible_commands:
        last_used = last_command_usage.get(command, 0)
        cooldown = CHILLZONE_COMMAND_COOLDOWNS[command]

        if now - last_used >= cooldown:
            async with channel.typing():
                await asyncio.sleep(random.uniform(2, 4))

            await channel.send(command)
            log_info(f"Used command: {command}")

            last_command_usage[command] = now
            save_command_usage(last_command_usage)

            break
