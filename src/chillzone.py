#
#
# Author: Elias Sjödin
# Created: 2024-01-15

import discord
import re
import random
import asyncio
import time
from logger import log_info, log_error
from action import enforce_action_cooldown
from wordwhiz import (
    is_wordwhiz_active,
    detect_wordwhiz_challenge,
    extract_wordwhiz_rule,
    participate_in_wordwhiz
)

SKIP_WELCOME_MESSAGE_PROB = 0.25
REPUTATION_COMMAND_COOLDOWN = 20

WELCOME_MESSAGE_DEBOUNCE = 10
WELCOME_MESSAGE = "### <:cz_bot_love:880661730961805322> WELCOME TO CHILLZONE. HAVE SO SO SO MUCH FUN!!! <:cz_bot_love:880661730961805322>"

last_welcome_time = {}
last_reputation_command_time = 0

def is_processing_blocked():
    return is_wordwhiz_active()


async def handle_point_drop(message: discord.Message):
    if not message.embeds:
        return False

    for embed in message.embeds:
        if not embed.description:
            continue

        match = re.search(r"Type \*\*(\S\w+)\*\*", embed.description)
        if not match:
            continue

        await enforce_action_cooldown()

        code = match.group(1)
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(2, 4))

        await message.channel.send(code)
        log_info(f"Sent message for point drop: {code}")
        return True
    return False


async def handle_welcome_message(message: discord.Message):
    if not message.embeds:
        return False

    for embed in message.embeds:
        if embed.description and "Welcome to **ChillZone**!" in embed.description:
            channel_id = message.channel.id
            current_time = time.time()

            if random.random() < SKIP_WELCOME_MESSAGE_PROB:
                log_info("Skipping welcome message due to random chance.")
                return False

            if channel_id in last_welcome_time and current_time - last_welcome_time[channel_id] < WELCOME_MESSAGE_DEBOUNCE:
                log_info("Skipping welcome message due to debounce.")
                return False

            last_welcome_time[channel_id] = current_time

            await enforce_action_cooldown()
            await asyncio.sleep(random.uniform(1, 4))
            await message.channel.send(WELCOME_MESSAGE)

            log_info("Sent welcoming message for ChillZone.")
            return True
    return False


async def handle_wordwhiz(message: discord.Message):
    if not detect_wordwhiz_challenge(message):
        return False

    rule_and_keyword = extract_wordwhiz_rule(message)
    if not rule_and_keyword:
        return False

    rule, keyword = rule_and_keyword
    await participate_in_wordwhiz(message.channel, rule, keyword)
    return True


async def handle_chillzone_command(client, message: discord.Message):
    global last_reputation_command_time

    content = message.content.lower()
    if not content.startswith((".neg", ".boost")):
        return

    bot_mentioned = client.user in message.mentions
    is_reply_to_bot = (
        message.reference and
        isinstance(message.reference.resolved, discord.Message) and
        message.reference.resolved.author.id == client.user.id
    )

    if not bot_mentioned and not is_reply_to_bot:
        return

    now = time.time()
    if now - last_reputation_command_time < REPUTATION_COMMAND_COOLDOWN:
        log_info(f"Ignoring '.{content.split()[0]}' due to cooldown.")
        return

    command_match = re.match(r"\.(neg|boost)", content)
    if not command_match:
        return

    command = command_match.group(1)
    if command == "neg":
        response = f"uuugh"
    elif command == "boost":
        response = f"nuh uh, neg me"

    log_info(f"Bot was '.{command}'. Replying with: '{response}'")
    last_reputation_command_time = now

    await enforce_action_cooldown()
    await asyncio.sleep(random.uniform(2, 3))
    await message.reply(response)


async def process_chillzone_message(client, message: discord.Message):
    if await handle_chillzone_command(client, message):
        return

    if not message.author.bot:
        return

    try:
        if await handle_point_drop(message):
            return
        if await handle_welcome_message(message):
            return
        if await handle_wordwhiz(message):
            return
    except Exception as e:
        log_error(f"Error in chillzone processing: {e}")
