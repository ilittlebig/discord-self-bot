#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
from tasks import process_reply_queue, process_message
from config import DISCORD_BOT_TOKEN, REPLY_INSTANTLY
from chillzone import process_chillzone_message, is_processing_blocked
from commands import periodic_chillzone_commands
from logger import log_error, log_info
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
    log_info(f"Logged in as {client.user}!")
    try:
        if REPLY_INSTANTLY:
            process_reply_queue.change_interval(seconds=0)

        if process_reply_queue.is_running():
            process_reply_queue.cancel()
            log_info("Canceled existing process_reply_queue task.")
        process_reply_queue.start()

        if periodic_chillzone_commands.is_running():
            periodic_chillzone_commands.cancel()
            log_info("Canceled existing periodic_chillzone_commands task.")
        periodic_chillzone_commands.start(client)
    except Exception as e:
        log_error(f"Error in on_ready: {e}")


@client.event
async def on_message(message):
    if is_processing_blocked():
        return
    if not is_valid_server_and_channel(message):
        return

    await process_chillzone_message(client, message)
    await process_message(client, message)


def run_bot():
    client.run(DISCORD_BOT_TOKEN)
