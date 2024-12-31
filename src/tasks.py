#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
import random
import asyncio
from discord.ext import tasks
from config import (
    SERVERS, TESTING_MODE, TESTING_USER_IDS, REPLY_TO_BOTS,
    CONTEXT_MESSAGE_COUNT, TASKS_LOOP_SECONDS
)
from ai import get_ai_response, load_prompt
from logger import log_info, log_warning, log_error, log_success, log_custom
from colorama import Fore
from conversation import add_to_history, get_conversation_context

last_message_ids = {}

@tasks.loop(seconds=TASKS_LOOP_SECONDS)
async def reply_to_messages(client):
    log_custom("EVENT", "==== Starting message processing loop ====", Fore.CYAN)
    for server_id, server_config in SERVERS.items():
        try:
            await handle_server(client, server_id, server_config)
        except Exception as e:
            log_error(f"Error in server {server_id}: {e}")
    log_custom("EVENT", "==== Finished message processing loop ====", Fore.CYAN, True)


async def handle_server(client, server_id, server_config):
    try:
        prompt_file = server_config["prompt_file"]
        channels = server_config["channels"]
        exclude_user_ids = server_config["exclude_user_ids"]
        system_prompt = load_prompt(prompt_file)

        for channel_id in channels:
            await handle_channel(client, server_id, channel_id, system_prompt, exclude_user_ids)
    except Exception as e:
        log_error(f"Error in server {server_id}: {e}")


async def handle_channel(client, server_id, channel_id, system_prompt, exclude_user_ids):
    try:
        guild = discord.utils.get(client.guilds, id=int(server_id))
        if not guild:
            log_warning(f"Server with ID {server_id} not found")
            return

        channel = discord.utils.get(guild.text_channels, id=int(channel_id))
        if not channel:
            log_warning(f"Channel {channel_id} not found in server {server_id}")
            return

        async for latest_message in channel.history(limit=1):
            break
        else:
            log_info(f"No messages found in channel #{channel.name} ({channel.id})")
            return
        add_to_history(server_id, channel_id, latest_message.author.name, latest_message.content)

        log_info(f"Processing latest message in #{channel.name} ({channel.id}):", True)
        log_info(f"Author: {latest_message.author.name} ({latest_message.author.id})")
        log_info(f"Content: {latest_message.content}")
        print()

        if not REPLY_TO_BOTS and latest_message.author.bot:
            log_info("Skipping bot message because REPLY_TO_BOTS is False", True)
            return

        already_replied = latest_message.id == last_message_ids.get(channel_id)
        is_own_message = (latest_message.author == client.user)

        # Skip conditions
        if already_replied:
            log_info("Message already replied to. Skipping...", True)
            return
        if is_own_message and not TESTING_MODE:
            log_info("Bot's own message and not in testing mode. Skipping...", True)
            return
        if TESTING_MODE and latest_message.author.id not in TESTING_USER_IDS:
            log_info("Testing mode on, author not in allowed list. Skipping...", True)
            return
        if latest_message.author.id in exclude_user_ids:
            log_info("Author is in the excluded user list. Skipping...", True)
            return

        # Build context from conversation history
        context_str = get_conversation_context(server_id, channel_id, max_messages=CONTEXT_MESSAGE_COUNT)

        # Generate and send reply
        await generate_ai_response(channel, latest_message, context_str, system_prompt)
        last_message_ids[channel_id] = latest_message.id
    except Exception as e:
        log_error(f"Error in channel {channel_id}: {e}")


async def generate_ai_response(channel, latest_message, context_str, system_prompt):
    reply = await get_ai_response(latest_message.content, context_str, system_prompt)
    log_success(f"Generated AI reply: {reply}", True)
    await latest_message.reply(reply)
    log_info(f"Replied to {latest_message.author.name} in #{channel.name}.")
