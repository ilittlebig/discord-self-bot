# Handles Discord WordWhiz game participation with human-like behavior
#
# Author: Elias Sjödin
# Created: 2025-01-15

import os
import time
import re
import asyncio
import discord
import random
from logger import log_info, log_warning, log_error, log_success

WORDWHIZ_TIMER = 30
WORDWHIZ_COOLDOWN_DURATION = 45
WORDLIST_FILE = os.path.join(os.path.dirname(__file__), "../wordlist.txt")

wordwhiz_active = False
wordwhiz_cooldown_end = 0
cached_wordlist = None

def is_wordwhiz_active() -> bool:
    """Check if WordWhiz game is currently active or in cooldown."""
    return wordwhiz_active or time.time() < wordwhiz_cooldown_end


def detect_wordwhiz_challenge(message: discord.Message) -> bool:
    """Detect if a message contains a WordWhiz challenge."""
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
        return None

    for embed in message.embeds:
        if not embed.description:
            continue

        match = re.search(r"word that (starts with|ends with|contains) the letters \*\*(\w+)\*\*", embed.description, re.IGNORECASE)
        if not match:
            continue
        return match.group(1).lower(), match.group(2).upper()
    return None


def load_wordlist() -> list:
    """Load the wordlist from file, caching for performance."""
    global cached_wordlist
    if cached_wordlist is None:
        try:
            with open(WORDLIST_FILE, "r") as f:
                cached_wordlist = [line.strip().lower() for line in f.readlines()]
            log_info(f"Loaded {len(cached_wordlist)} words from wordlist.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Wordlist file not found at: {os.path.abspath(WORDLIST_FILE)}")
    return cached_wordlist


def generate_wordwhiz_words(rule: str, keyword: str) -> list:
    """Generate a list of words matching the WordWhiz rule and keyword."""
    words = load_wordlist()
    keyword = keyword.lower()
    
    matching_words = []
    
    if rule == "starts with":
        matching_words = [word for word in words if word.startswith(keyword)]
    elif rule == "ends with":
        matching_words = [word for word in words if word.endswith(keyword)]
    elif rule == "contains":
        matching_words = [word for word in words if keyword in word]
    
    filtered_words = [w for w in matching_words if len(w) < 12]
    
    log_info(f"Found {len(filtered_words)} suitable words for WordWhiz rule: {rule} {keyword}")
    return filtered_words


def introduce_typo(word: str) -> str:
    if random.random() > 0.15:
        return word
    
    if len(word) < 4:
        return word
    
    typo_type = random.choice(["swap", "double", "miss", "replace"])
    
    if typo_type == "swap" and len(word) > 3:
        pos = random.randint(0, len(word) - 2)
        chars = list(word)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return ''.join(chars)
    
    elif typo_type == "double":
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos] + word[pos:]
    
    elif typo_type == "miss":
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos+1:]
    
    elif typo_type == "replace":
        keyboard_adjacency = {
            'a': 'sq', 'b': 'vn', 'c': 'xv', 'd': 'sf', 'e': 'wr', 'f': 'dg',
            'g': 'fh', 'h': 'gj', 'i': 'uo', 'j': 'hk', 'k': 'jl', 'l': 'k',
            'm': 'n', 'n': 'bm', 'o': 'ip', 'p': 'o', 'q': 'wa', 'r': 'et',
            's': 'ad', 't': 'ry', 'u': 'yi', 'v': 'cb', 'w': 'qe', 'x': 'zc',
            'y': 'tu', 'z': 'x'
        }
        
        pos = random.randint(0, len(word) - 1)
        char = word[pos].lower()
        if char in keyboard_adjacency and keyboard_adjacency[char]:
            replacement = random.choice(keyboard_adjacency[char])
            return word[:pos] + replacement + word[pos+1:]
    
    return word


async def participate_in_wordwhiz(channel: discord.TextChannel, rule: str, keyword: str):
    """Participate in a WordWhiz challenge with human-like behavior."""
    global wordwhiz_active, wordwhiz_cooldown_end
    wordwhiz_active = True
    wordwhiz_cooldown_end = time.time() + WORDWHIZ_COOLDOWN_DURATION

    try:
        log_info(f"Starting WordWhiz challenge: {rule} {keyword}")
        words = generate_wordwhiz_words(rule, keyword)
        if not words:
            log_warning("No valid words found for WordWhiz challenge.")
            return

        # Generate a good number of words - not too few, not too many
        max_words = min(len(words), random.randint(12, 15))
        selected_words = random.sample(words, max_words)
        log_info(f"Selected {len(selected_words)} words for the challenge.")
        
        start_time = time.time()
        max_duration = WORDWHIZ_TIMER - 2  # Leave 2 seconds buffer

        # Sort words by length (shorter words first for quick responses)
        selected_words.sort(key=len)
        
        # Send first 3-4 words quickly
        initial_burst = selected_words[:random.randint(3, 4)]
        remaining_words = selected_words[len(initial_burst):]
        
        # Send initial burst quickly
        for word in initial_burst:
            if time.time() - start_time >= max_duration:
                log_info("WordWhiz timer about to expire, stopping.")
                break

            try:
                word_to_send = introduce_typo(word)
                
                # Very quick typing for initial burst
                typing_duration = min(0.2 + (len(word) * 0.03), 0.8)
                log_info(f"Typing '{word_to_send}' for {typing_duration:.1f} seconds...")
                
                try:
                    await asyncio.wait_for(perform_typing(channel, typing_duration), timeout=2.0)
                except asyncio.TimeoutError:
                    log_warning("Typing indicator timed out.")
                
                await asyncio.wait_for(channel.send(word_to_send), timeout=3)
                log_success(f"Sent WordWhiz word: {word_to_send}")
                
                # Very short pause between initial burst words
                await asyncio.sleep(random.uniform(0.2, 0.5))
                
            except asyncio.TimeoutError:
                log_warning(f"Timeout while sending word: {word}")
                continue
            except Exception as e:
                log_error(f"Error sending WordWhiz word '{word}': {e}")
                continue
        
        # Then send remaining words at a moderate pace
        for word in remaining_words:
            if time.time() - start_time >= max_duration:
                log_info("WordWhiz timer about to expire, stopping.")
                break

            try:
                word_to_send = introduce_typo(word)
                
                # Moderate typing speed for remaining words
                typing_duration = min(0.3 + (len(word) * 0.05), 1.0)
                log_info(f"Typing '{word_to_send}' for {typing_duration:.1f} seconds...")
                
                try:
                    await asyncio.wait_for(perform_typing(channel, typing_duration), timeout=2.0)
                except asyncio.TimeoutError:
                    log_warning("Typing indicator timed out.")
                
                await asyncio.wait_for(channel.send(word_to_send), timeout=3)
                log_success(f"Sent WordWhiz word: {word_to_send}")
                
                # Moderate pause between words
                elapsed = time.time() - start_time
                fatigue_factor = min(0.5, elapsed / 20.0)  # Slight fatigue
                await asyncio.sleep(random.uniform(0.5, 1.0 + fatigue_factor))
                
            except asyncio.TimeoutError:
                log_warning(f"Timeout while sending word: {word}")
                continue
            except Exception as e:
                log_error(f"Error sending WordWhiz word '{word}': {e}")
                continue

        log_success("WordWhiz participation completed.")
    except Exception as e:
        log_error(f"Error in WordWhiz participation: {e}")
    finally:
        wordwhiz_active = False
        log_info("WordWhiz state reset.")


async def perform_typing(channel: discord.TextChannel, duration: float):
    async with channel.typing():
        await asyncio.sleep(duration)
