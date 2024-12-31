#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
import random
import asyncio
from collections import deque
from discord.ext import tasks
from config import (
    SERVERS, TESTING_MODE, TESTING_USER_IDS, REPLY_TO_BOTS,
    CONTEXT_MESSAGE_COUNT, REPLY_COOLDOWN
)
from ai import get_ai_response, load_prompt, is_message_relevant
from logger import log_info, log_warning, log_error, log_success, log_custom
from conversation import add_to_history, get_conversation_context

reply_queue = deque()
last_replied_time = {}
last_message_ids = {}

@tasks.loop(seconds=30)
async def process_reply_queue():
    if reply_queue:
        message, context_str, system_prompt = reply_queue.popleft()
        try:
            await handle_reply(message, context_str, system_prompt)
            last_replied_time[message.channel.id] = asyncio.get_event_loop().time()
        except Exception as e:
            log_error(f"Error processing queued reply: {e}")

async def process_message(client, message):
    try:
        server_id = str(message.guild.id)
        channel_id = message.channel.id

        if server_id not in SERVERS or channel_id not in SERVERS[server_id]["channels"]:
            log_warning(f"Server ID {server_id} or Channel ID {channel_id} not configured in SERVERS.")
            return

        server_config = SERVERS[server_id]
        exclude_user_ids = server_config["exclude_user_ids"]
        prompt_file = server_config["prompt_file"]
        system_prompt = load_prompt(prompt_file)

        add_to_history(server_id, channel_id, message.author.name, message.content)

        log_info(f"Processing message in #{message.channel.name} ({channel_id}):", True)
        log_info(f"Author: {message.author.name} ({message.author.id})")
        log_info(f"Content: {message.content}")

        if TESTING_MODE and message.author.id not in TESTING_USER_IDS:
            log_info("Testing mode is enabled, but the message author is not in the allowed testing users. Skipping.")
            return

        context_str = get_conversation_context(server_id, channel_id, max_messages=CONTEXT_MESSAGE_COUNT)
        should_reply = await is_message_relevant(message, context_str, prompt_file, client.user.id)

        if not should_reply:
            log_info("Message deemed irrelevant by AI. Skipping reply.", True)
            return

        now = asyncio.get_event_loop().time()
        if channel_id in last_replied_time and now - last_replied_time[channel_id] < REPLY_COOLDOWN:
            log_info("Cooldown active. Queuing the message for later reply.", True)
            reply_queue.append((message, context_str, system_prompt))
            return

        await handle_reply(message, context_str, system_prompt)
        last_replied_time[channel_id] = now
    except Exception as e:
        log_error(f"Error processing message: {e}")


async def handle_reply(message, context_str, system_prompt):
    reply = await get_ai_response(message.content, context_str, system_prompt)
    log_success(f"Generated AI reply: {reply}", True)

    delay = random.uniform(5, 10)
    log_info(f"Waiting {delay:.1f} seconds before replying")
    await asyncio.sleep(delay)

    log_success(f"Replied to {message.author.name} in #{message.channel.name}.")
    await message.reply(reply)
