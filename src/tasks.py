#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import os
import time
import discord
import random
import asyncio
from collections import deque
from discord.ext import tasks
from action import enforce_action_cooldown
from ai import (
    get_ai_response, load_prompt, is_message_relevant, is_response_needed,
    determine_gif_category, categorize_message
)
from logger import log_info, log_warning, log_error, log_success, log_custom
from conversation import (
    add_to_history, get_conversation_context, update_user_interaction,
    get_last_user_interaction
)
from chillzone import is_processing_blocked
from config import (
    SERVERS, TESTING_MODE, TESTING_USER_IDS, PROHIBITED_PHRASES,
    REPLY_COOLDOWN, QUEUE_COOLDOWN, REPLY_INSTANTLY, NORMAL_REPLY_PROBABILITY,
    GIF_PROBABILITY, GIF_CATEGORIES, MAX_QUEUE_AGE_SECONDS, REPLY_BATCH_SIZE,
)

reply_queue = deque()
last_replied_time = {}

def is_direct_reply_to_bot(message: discord.Message, bot_id: int) -> bool:
    if not message.reference:
        return False

    referenced_msg = message.reference.resolved
    if not isinstance(referenced_msg, discord.Message):
        return False
    return referenced_msg.author.id == bot_id


def pick_gif_for_category(category: str) -> str:
    if category not in GIF_CATEGORIES:
        return ""
    return random.choice(GIF_CATEGORIES[category])


def filter_response(reply: str) -> str:
    if not reply:
        return None

    for phrase in PROHIBITED_PHRASES:
        if phrase in reply.lower():
            log_info(f"Blocked prohibited phrase: {phrase}")
            return None
    return reply


@tasks.loop(seconds=QUEUE_COOLDOWN)
async def process_reply_queue():
    if is_processing_blocked():
        log_warning("Processing is currently blocked.")
        return

    queue_size = len(reply_queue)
    log_info(f"Queue size: {queue_size}")

    if queue_size > 10:
        process_reply_queue.change_interval(seconds=max(QUEUE_COOLDOWN // 2, 1))
    else:
        process_reply_queue.change_interval(seconds=QUEUE_COOLDOWN)

    sorted_queue = sorted(reply_queue, key=lambda item: (item["category"], item["timestamp"]), reverse=True)
    for i in range(REPLY_BATCH_SIZE):
        if not sorted_queue:
            log_info("Reply queue is empty.")
            return

        next_item = sorted_queue.pop(0)
        if next_item in reply_queue:
            reply_queue.remove(next_item)

        timestamp, message, context_str, system_prompt, category = (
            next_item["timestamp"],
            next_item["message"],
            next_item["context_str"],
            next_item["system_prompt"],
            next_item["category"],
        )

        if time.time() - timestamp > MAX_QUEUE_AGE_SECONDS and category != "critical":
            log_warning(f"Skipping old non-critical message: {message.content[:30]}")
            continue

        try:
            log_info(f"Processing {category} priority message: {message.content[:50]}")
            await handle_reply(message, context_str, system_prompt)
            last_replied_time[message.channel.id] = asyncio.get_event_loop().time()
        except Exception as e:
            log_error(f"Error processing queued reply: {e}")

        if i < REPLY_BATCH_SIZE - 1 and reply_queue:
            delay = random.uniform(3, 7)
            log_info(f"Waiting {delay} seconds before processing the next message.")
            await asyncio.sleep(delay)


async def process_message(client, message):
    try:
        server_id = str(message.guild.id) if message.guild else None
        channel_id = message.channel.id if message.channel else None

        if message.author == client.user and not TESTING_MODE:
            return

        server_config = SERVERS[server_id]
        exclude_user_ids = server_config["exclude_user_ids"]
        prompt_file = server_config["prompt_file"]
        system_prompt = load_prompt(prompt_file)

        context_message_count = server_config["context_message_count"]
        history_limit = server_config["history_limit"]
        min_history_message_length = server_config["min_history_message_length"]
        max_history_message_length = server_config["max_history_message_length"]

        display_name = message.guild.me.display_name

        if message.author.id in exclude_user_ids:
            log_info(f"Message from excluded user {message.author.name} ({message.author.id}) ignored.")
            return

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
        should_reply, random_engagement_selected = await is_message_relevant(
            message,
            context_str,
            display_name,
            prompt_file,
            client.user.id
        )

        if not should_reply:
            log_info("Message deemed irrelevant by AI. Skipping reply.")
            return

        last_user_interaction = get_last_user_interaction(server_id, channel_id, message.author.id)
        if last_user_interaction is None:
            last_reply = None
        else:
            last_reply = last_user_interaction.get("last_reply")

        if not random_engagement_selected:
            bot_mentioned = client.user in message.mentions
            is_direct_reply = is_direct_reply_to_bot(message, client.user.id)

            response_needed = await is_response_needed(
                last_reply,
                message.content,
                bot_mentioned,
                display_name,
                is_direct_reply
            )

            if not response_needed:
                return
        else:
            log_info("Skipping response-needed check due to random engagement.")

        now = asyncio.get_event_loop().time()
        if channel_id in last_replied_time and now - last_replied_time[channel_id] < REPLY_COOLDOWN:
            log_info("Cooldown active. Queuing the message for later reply.", True)
            reply_queue.append({
                "timestamp": time.time(),
                "message": message,
                "context_str": context_str,
                "system_prompt": system_prompt,
                "category": await categorize_message(message),
            })
            return

        await handle_reply(message, context_str, system_prompt)
        last_replied_time[channel_id] = now
    except Exception as e:
        log_error(f"Error processing message: {e}")


async def handle_reply(message, context_str, system_prompt):
    reply = None

    if random.random() < GIF_PROBABILITY:
        gif_category = await determine_gif_category(context_str, message.content, system_prompt)
        if gif_category and gif_category != "none":
            log_info("Chose to send a GIF instead of generated reply.")
            reply = pick_gif_for_category(gif_category)
    else:
        reply = await get_ai_response(message.content, message.author, context_str, system_prompt)
        log_success(f"Generated AI reply: {reply}", True)

    if not reply:
        log_warning("No reply generated.")
        return

    filtered_reply = filter_response(reply)
    if not filtered_reply:
        log_warning("Generated reply was blocked due to prohibited content.")
        return

    if random.random() < NORMAL_REPLY_PROBABILITY:
        log_info("Chose to send a normal channel message instead of replying.")
        send_method = message.channel.send
    else:
        send_method = message.reply

    if not REPLY_INSTANTLY:
        delay = random.uniform(5, 10)
        log_info(f"Waiting {delay:.1f} seconds before responding.")
        async with message.channel.typing():
            await asyncio.sleep(delay)
        log_info("Finished delay, proceeding to send reply.")

    if is_processing_blocked():
        log_info("Processing is blocked. Not sending handled reply.")
        return

    await enforce_action_cooldown()
    await asyncio.wait_for(send_method(reply), timeout=15)
    log_success(f"Replied to {message.author.name} in #{message.channel.name}.")

    server_id = str(message.guild.id) if message.guild else None
    channel_id = message.channel.id
    user_id = message.author.id
    update_user_interaction(server_id, channel_id, user_id, reply)
