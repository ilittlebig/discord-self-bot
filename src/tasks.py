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
from ai import get_ai_response, load_prompt, is_message_relevant
from logger import log_info, log_warning, log_error, log_success, log_custom
from colorama import Fore
from conversation import add_to_history, get_conversation_context

last_message_ids = {}

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

        context_str = get_conversation_context(server_id, channel_id, max_messages=CONTEXT_MESSAGE_COUNT)
        should_reply = await is_message_relevant(message, context_str, prompt_file, client.user.id)

        if not should_reply:
            log_info("Message deemed irrelevant by AI. Skipping reply.", True)
            return

        reply = await get_ai_response(message.content, context_str, system_prompt)
        log_success(f"Generated AI reply: {reply}", True)
        await message.reply(reply)
        log_success(f"Replied to {message.author.name} in #{message.channel.name}.")
    except Exception as e:
        log_error(f"Error processing message: {e}")
