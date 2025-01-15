#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import time
import discord
import random
import asyncio
from collections import deque
from discord.ext import tasks
from ai import get_ai_response, load_prompt, is_message_relevant
from logger import log_info, log_warning, log_error, log_success, log_custom
from conversation import add_to_history, get_conversation_context
from config import (
    SERVERS, TESTING_MODE, TESTING_USER_IDS,
    REPLY_COOLDOWN, QUEUE_COOLDOWN, REPLY_INSTANTLY
)

SEND_MESSAGE_PROB = 1/8
WORDWHIZ_COOLDOWN_DURATION = 45

reply_queue = deque()
last_replied_time = {}
last_message_ids = {}
wordwhiz_cooldown_end = 0


def is_wordwhiz_challenge(message: discord.Message) -> bool:
    if not message.author.bot:
        return False
    if message.content and "WordWhiz" in message.content:
        return True

    if message.embeds:
        for embed in message.embeds:
            if embed.title and "WordWhiz" in embed.title:
                return True
            if embed.description and "WordWhiz" in embed.description:
                return True
            for field in embed.fields:
                if "WordWhiz" in field.name or "WordWhiz" in field.value:
                    return True
    return False


@tasks.loop(seconds=QUEUE_COOLDOWN)
async def process_reply_queue():
    if reply_queue:
        message, context_str, system_prompt = reply_queue.popleft()
        try:
            await handle_reply(message, context_str, system_prompt)
            last_replied_time[message.channel.id] = asyncio.get_event_loop().time()
        except Exception as e:
            log_error(f"Error processing queued reply: {e}")


async def process_message(client, message):
    global wordwhiz_cooldown_end

    try:
        now = time.time()
        if now < wordwhiz_cooldown_end:
            log_info(f"Skipping because WordWhiz cooldown is active (ends at {wordwhiz_cooldown_end:.1f}).")
            return

        if is_wordwhiz_challenge(message):
            wordwhiz_cooldown_end = now + WORDWHIZ_COOLDOWN_DURATION
            log_info("Detected WordWhiz challenge. Starting 30s cooldown. Skipping message processing.")
            return

        server_id = str(message.guild.id) if message.guild else None
        channel_id = message.channel.id if message.channel else None

        if not server_id or not channel_id:
            log_error(f"Message guild or channel is None. Guild: {message.guild}, Channel: {message.channel}")
            return
        if message.author == client.user and not TESTING_MODE:
            return
        if server_id not in SERVERS or channel_id not in SERVERS[server_id]["channels"]:
            return

        server_config = SERVERS[server_id]
        exclude_user_ids = server_config["exclude_user_ids"]
        prompt_file = server_config["prompt_file"]
        system_prompt = load_prompt(prompt_file)

        context_message_count = server_config["context_message_count"]
        history_limit = server_config["history_limit"]
        min_history_message_length = server_config["min_history_message_length"]
        max_history_message_length = server_config["max_history_message_length"]

        if len(message.content) > max_history_message_length:
            log_warning(f"Message from {message.author.name} exceeds max history length ({max_history_message_length} chars). Skipping...")
            return
        if len(message.content) < min_history_message_length:
            log_warning(f"Message from {message.author.name} is too short ({len(message.content)} chars). Skipping...")
            return
        add_to_history(server_id, channel_id, message.author.name, message.content, history_limit)

        log_info(f"Processing message in #{message.channel.name} ({channel_id}):", True)
        log_info(f"Author: {message.author.name} ({message.author.id})")
        log_info(f"Content: {message.content}")

        if TESTING_MODE and message.author.id not in TESTING_USER_IDS:
            log_info("Testing mode is enabled, but the message author is not in the allowed testing users. Skipping.")
            return

        context_str = get_conversation_context(server_id, channel_id, max_messages=context_message_count)
        should_reply = await is_message_relevant(message, context_str, prompt_file, client.user.id)

        if not should_reply:
            log_info("Message deemed irrelevant by AI. Skipping reply.")
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
    reply = await get_ai_response(message.content, message.author, context_str, system_prompt)
    log_success(f"Generated AI reply: {reply}", True)

    if random.random() < SEND_MESSAGE_PROB:
        log_info("Chose to send a normal channel message instead of replying.")
        send_method = message.channel.send
    else:
        send_method = message.reply

    if not REPLY_INSTANTLY:
        delay = random.uniform(5, 10)
        log_info(f"Waiting {delay:.1f} seconds before responding.")
        await asyncio.sleep(delay)

    await send_method(reply)
    log_success(f"Replied to {message.author.name} in #{message.channel.name}.")
