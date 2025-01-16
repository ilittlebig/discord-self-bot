#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
from tasks import process_reply_queue, process_message
from config import DISCORD_BOT_TOKEN, REPLY_INSTANTLY
from chillzone import process_chillzone_message, is_processing_blocked
from commands import periodic_chillzone_commands
from logger import log_error
from config import SERVERS

client = discord.Client()

def is_valid_server_and_channel(message: discord.Message) -> bool:
    server_id = str(message.guild.id) if message.guild else None
    channel_id = message.channel.id if message.channel else None

    if not server_id or not channel_id:
        log_error(f"Message guild or channel is None. Guild: {message.guild}, Channel: {message.channel}")
        return False
    if server_id not in SERVERS or channel_id not in SERVERS[server_id]["channels"]:
        return False
    return True


@client.event
async def on_ready():
    print(f"Logged in as {client.user}!")
    if REPLY_INSTANTLY:
        process_reply_queue.change_interval(seconds=0)
    process_reply_queue.start()
    periodic_chillzone_commands.start(client)


@client.event
async def on_message(message):
    if is_processing_blocked():
        return
    if not is_valid_server_and_channel(message):
        return

    await process_chillzone_message(message)
    await process_message(client, message)


def run_bot():
    client.run(DISCORD_BOT_TOKEN)
