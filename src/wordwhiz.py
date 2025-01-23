#
#
# Author: Elias Sjödin
# Created: 2025-01-15

import os
import time
import re
import asyncio
import discord
import random
from logger import log_info, log_warning

WORDWHIZ_TIMER = 30
WORDWHIZ_COOLDOWN_DURATION = 45
WORDLIST_FILE = os.path.join(os.path.dirname(__file__), "../wordlist.txt")

wordwhiz_active = False
wordwhiz_cooldown_end = 0
cached_wordlist = None

def is_wordwhiz_active() -> bool:
    return wordwhiz_active or time.time() < wordwhiz_cooldown_end


def detect_wordwhiz_challenge(message: discord.Message) -> bool:
    if not message.embeds:
        return False

    for embed in message.embeds:
        if embed.title and "WordWhiz" in embed.title:
            return True
        if embed.description and "WordWhiz" in embed.description:
            return True
    return False


def extract_wordwhiz_rule(message: discord.Message) -> tuple:
    if not message.embeds:
        return

    for embed in message.embeds:
        if not embed.description:
            continue

        match = re.search(r"word that (starts with|ends with|contains) the letters \*\*(\w+)\*\*", embed.description, re.IGNORECASE)
        if not match:
            continue
        return match.group(1).lower(), match.group(2).upper()
    return None


def load_wordlist() -> list:
    global cached_wordlist
    if cached_wordlist is None:
        try:
            with open(WORDLIST_FILE, "r") as f:
                cached_wordlist = [line.strip().lower() for line in f.readlines()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found at: {os.path.abspath(WORDLIST_FILE)}")
    return cached_wordlist


def generate_wordwhiz_words(rule: str, keyword: str) -> list:
    words = load_wordlist()
    keyword = keyword.lower()

    if rule == "starts with":
        return [word for word in words if word.startswith(keyword)]
    elif rule == "ends with":
        return [word for word in words if word.endswith(keyword)]
    elif rule == "contains":
        return [word for word in words if keyword in word]
    return []


async def participate_in_wordwhiz(channel: discord.TextChannel, rule: str, keyword: str):
    global wordwhiz_active, wordwhiz_cooldown_end
    wordwhiz_active = True
    wordwhiz_cooldown_end = time.time() + WORDWHIZ_COOLDOWN_DURATION

    try:
        log_info("Starting WordWhiz challenge.")
        words = generate_wordwhiz_words(rule, keyword)
        if not words:
            log_warning("No valid words found for WordWhiz challenge.")
            return

        log_info(f"Found {len(words)} words for the challenge.")
        random.shuffle(words)

        start_time = time.time()
        max_duration = WORDWHIZ_TIMER

        for word in words:
            if time.time() - start_time >= max_duration:
                log_info("WordWhiz timer expired.")
                break

            try:
                log_info(f"Attempting to send word: {word}")
                try:
                    duration = random.uniform(0.5, 2)
                    await asyncio.wait_for(perform_typing(channel, duration), timeout=5.0)
                except asyncio.TimeoutError:
                    log_warning("Typing indicator timed out.")
                log_info("Attempting to send the message...")
                await asyncio.wait_for(channel.send(word), timeout=5)
                log_info(f"Successfully sent word: {word}")
            except asyncio.TimeoutError:
                log_warning(f"Timeout while sending word: {word}")
                continue
            except Exception as e:
                log_error(f"Unexpected error while sending word '{word}': {e}")
                continue

        log_info("WordWhiz challenge completed.")
    except Exception as e:
        log_error(f"Error during WordWhiz challenge: {e}")
    finally:
        wordwhiz_active = False
        log_info("WordWhiz state reset.")


async def perform_typing(channel: discord.TextChannel, duration: float):
    async with channel.typing():
        await asyncio.sleep(duration)
