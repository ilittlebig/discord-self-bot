#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import discord
import os
import string
from logger import log_info, log_custom, log_error
from openai import OpenAI
from colorama import Fore
from config import (
    MODEL, OPENAI_API_KEY, REPLY_TO_BOTS,
    MAX_CHARACTERS_TO_REPLY_TO, MIN_CHARACTERS_TO_REPLY_TO
)

client = OpenAI(api_key=OPENAI_API_KEY)

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


def sanitize_response(response: str) -> str:
    response = response.split("\n")[0].strip()
    response = remove_punctuation(response)
    words = response.split()

    if len(words) < 2 or len(words) > 30:
        return None
    return response


def load_prompt(prompt_file: str) -> str:
    try:
        with open("prompts/" + prompt_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"Prompt file '{prompt_file}' not found. Please check your configuration.")


def load_relevance_prompt(prompt_file: str) -> str:
    base_name = os.path.splitext(prompt_file)[0]
    relevance_prompt_file = f"prompts/{base_name}_relevance_prompt.txt"

    try:
        with open(relevance_prompt_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"Relevance prompt file '{relevance_prompt_file}' not found. Please create it.")


async def get_ai_response(prompt: str, context: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation so far:\n{context}\n\nUser: {prompt}"},
            ]
        )

        reply = response.choices[0].message.content.strip()
        sanitized_reply = sanitize_response(reply)
        return sanitized_reply if sanitized_reply else "idk bro, can't think of anything rn"
    except Exception as e:
        log_error(f"Error during AI generation: {e}")
        return "idk, something's off"


async def is_message_relevant(message: discord.Message, context: str, prompt_file: str, bot_user_id: int) -> bool:
    is_direct_reply = message.reference is not None and message.reference.resolved is not None
    is_direct_reply = is_direct_reply and message.reference.resolved.author.id == bot_user_id

    if message.author.bot and not REPLY_TO_BOTS:
        log_custom(
            "RELEVANCE",
            "Message is from a bot, and REPLY_TO_BOTS is set to False. Deemed irrelevant.",
            Fore.CYAN
        )
        return False

    if message.attachments and not message.content.strip():
        log_custom(
            "RELEVANCE",
            "Message contains only attachments. Deemed irrelevant.",
            Fore.CYAN
        )
        return False

    if len(message.content.split()) < MINIMUM_CHARACTERS_TO_REPLY_TO:
        log_custom(
            "RELEVANCE",
            "Message is too short. Deemed irrelevant.",
            Fore.CYAN
        )
        return False

    if len(message.content) > MAXIMUM_CHARACTERS_TO_REPLY_TO:
        log_custom(
            "RELEVANCE",
            "Message is too long. Deemed irrelevant.",
            Fore.CYAN
        )
        return False

    if is_direct_reply:
        log_custom(
            "RELEVANCE",
            "Message is a direct reply to the bot. Automatically deemed relevant.",
            Fore.CYAN
        )
        return True

    relevance_prompt = load_relevance_prompt(prompt_file)
    full_relevance_prompt = (
        f"Conversation so far:\n{context}\n\n"
        f"User's message: {message.content}\n\n"
        f"Determine if this message is worth replying to. Respond with only 'yes' or 'no'."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=5,
            temperature=0.5,
            messages=[
                {"role": "system", "content": relevance_prompt},
                {"role": "user", "content": full_relevance_prompt},
            ],
        )

        decision = response.choices[0].message.content.strip().lower()
        return decision == "yes"
    except Exception as e:
        log_error(f"Error during relevance check: {e}")
        return False
