#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
from tasks import process_message
from config import DISCORD_BOT_TOKEN

client = discord.Client()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}!")
    #reply_to_messages.start(client)


@client.event
async def on_message(message):
    await process_message(client, message)


def run_bot():
    client.run(DISCORD_BOT_TOKEN)
