# Handles Discord ChillZone server specific functionality
#
# Author: Elias Sjödin
# Created: 2024-01-15

import discord
import re
import random
import asyncio
import time
import datetime
from datetime import timedelta
from logger import log_info, log_error, log_warning, log_success
from action import enforce_action_cooldown
from wordwhiz import (
    is_wordwhiz_active,
    detect_wordwhiz_challenge,
    extract_wordwhiz_rule,
    participate_in_wordwhiz
)

# Configuration
SKIP_WELCOME_MESSAGE_PROB = 0.65  # Increased to make bot less likely to respond to welcomes
REPUTATION_COMMAND_COOLDOWN = 20
WELCOME_MESSAGE_DEBOUNCE = 30  # Increased to avoid responding to multiple welcome messages
WELCOME_MESSAGE = "### <:cz_bot_love:880661730961805322> WELCOME TO CHILLZONE. HAVE SO SO SO MUCH FUN!!! <:cz_bot_love:880661730961805322>"

# Tracking variables
last_welcome_time = {}
last_reputation_command_time = 0
last_point_drop_time = 0
recent_point_drops = set()  # Track recent point drop codes to avoid duplicates

def is_processing_blocked():
    """Check if message processing should be blocked (e.g., during WordWhiz)."""
    return is_wordwhiz_active()


def is_multi_message_welcome(message: discord.Message) -> bool:
    if not message.guild:
        return False
    return False
async def check_multi_message(message: discord.Message) -> bool:
    if not message.guild:
        return False
        
    try:
        recent_messages = []
        async for msg in message.channel.history(limit=8, after=datetime.datetime.utcnow() - timedelta(seconds=8)):
            recent_messages.append(msg)
        
        author_messages = [msg for msg in recent_messages if msg.author == message.author]
        
        # If user sent 3+ messages in quick succession, it's multi-message spam
        if len(author_messages) >= 3:
            log_info(f"Detected multi-message spam from {message.author.name} - {len(author_messages)} messages in 8 seconds")
            return True
            
        # If user sent 2 messages and they're both short, likely multi-message
        if len(author_messages) == 2:
            if all(len(msg.content) < 20 for msg in author_messages):
                log_info(f"Detected short multi-message from {message.author.name}")
                return True
    except Exception as e:
        log_error(f"Error checking for multi-message: {e}")
        
    return False


async def handle_point_drop(message: discord.Message) -> bool:
    global last_point_drop_time, recent_point_drops
    
    if not message.embeds:
        return False

    for embed in message.embeds:
        if not embed.description:
            continue

        match = re.search(r"Type \*\*(\S\w+)\*\*", embed.description)
        if not match:
            continue
            
        code = match.group(1)
        
        current_time = time.time()
        if code in recent_point_drops or current_time - last_point_drop_time < 5:
            log_warning(f"Skipping point drop '{code}' - duplicate or too soon after previous")
            return False
            
        # Check if someone else already responded to this point drop
        try:
            recent_messages = []
            async for msg in message.channel.history(limit=3, after=message.created_at):
                recent_messages.append(msg)
                
            for msg in recent_messages:
                if msg.author != message.author and code.lower() in msg.content.lower():
                    log_warning(f"Someone already responded to point drop '{code}' - skipping")
                    return False
        except Exception as e:
            log_error(f"Error checking recent messages: {e}")

        await enforce_action_cooldown()

        # Simulate human typing speed based on code length
        typing_duration = random.uniform(1.5, 3.5)
        async with message.channel.typing():
            await asyncio.sleep(typing_duration)

        await message.channel.send(code)
        log_success(f"Sent message for point drop: {code}")
        
        # Update tracking
        last_point_drop_time = current_time
        recent_point_drops.add(code)
        if len(recent_point_drops) > 10:  # Limit size of tracking set
            recent_point_drops.pop()
            
        return True
    return False


async def handle_welcome_message(message: discord.Message) -> bool:
    if not message.embeds:
        return False
        
    # Skip if this is part of a multi-message
    if await check_multi_message(message):
        return False

    for embed in message.embeds:
        if embed.description and "Welcome to **ChillZone**!" in embed.description:
            channel_id = message.channel.id
            current_time = time.time()

            # Higher chance to skip welcome messages
            if random.random() < SKIP_WELCOME_MESSAGE_PROB:
                log_info("Skipping welcome message due to random chance.")
                return False

            # Longer debounce period to avoid responding to multiple welcomes
            if channel_id in last_welcome_time and current_time - last_welcome_time[channel_id] < WELCOME_MESSAGE_DEBOUNCE:
                log_info("Skipping welcome message due to debounce.")
                return False

            last_welcome_time[channel_id] = current_time

            await enforce_action_cooldown()
            
            # More human-like delay
            delay = random.uniform(2, 5)
            log_info(f"Waiting {delay:.1f} seconds before sending welcome message")
            await asyncio.sleep(delay)
            
            await message.channel.send(WELCOME_MESSAGE)
            log_success("Sent welcoming message for ChillZone.")
            return True
    return False


async def handle_wordwhiz(message: discord.Message) -> bool:
    """Handle WordWhiz challenges."""
    if not detect_wordwhiz_challenge(message):
        return False

    rule_and_keyword = extract_wordwhiz_rule(message)
    if not rule_and_keyword:
        return False

    rule, keyword = rule_and_keyword
    await participate_in_wordwhiz(message.channel, rule, keyword)
    return True


async def handle_chillzone_command(client, message: discord.Message) -> bool:
    """Handle ChillZone reputation commands (.neg, .boost)."""
    global last_reputation_command_time

    content = message.content.lower()
    if not content.startswith((".neg", ".boost")):
        return False

    bot_mentioned = client.user in message.mentions
    is_reply_to_bot = (
        message.reference and
        isinstance(message.reference.resolved, discord.Message) and
        message.reference.resolved.author.id == client.user.id
    )

    if not bot_mentioned and not is_reply_to_bot:
        return False

    now = time.time()
    if now - last_reputation_command_time < REPUTATION_COMMAND_COOLDOWN:
        log_info(f"Ignoring '.{content.split()[0]}' due to cooldown.")
        return False

    command_match = re.match(r"\.(neg|boost)", content)
    if not command_match:
        return False

    command = command_match.group(1)
    
    # More varied responses
    if command == "neg":
        responses = ["uuugh", "why tho", "rude", "bruh", "nah"]
        response = random.choice(responses)
    elif command == "boost":
        responses = ["nuh uh, neg me", "neg me instead", "nah neg", "neg > boost", "negs only"]
        response = random.choice(responses)

    log_info(f"Bot was '.{command}'. Replying with: '{response}'")
    last_reputation_command_time = now

    await enforce_action_cooldown()
    
    # More human-like delay
    delay = random.uniform(1.5, 3)
    await asyncio.sleep(delay)
    
    await message.reply(response)
    return True


async def process_chillzone_message(client, message: discord.Message):
    """Main entry point for processing ChillZone messages."""
    # Handle commands from any user
    if await handle_chillzone_command(client, message):
        return

    # Only process bot messages for special events
    if not message.author.bot:
        return

    try:
        # Process in order of priority
        if await handle_point_drop(message):
            return
        if await handle_welcome_message(message):
            return
        if await handle_wordwhiz(message):
            return
    except Exception as e:
        log_error(f"Error in chillzone processing: {e}")
