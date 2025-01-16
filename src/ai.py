#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import re
import discord
import os
import string
import random
from logger import log_info, log_custom, log_error
from openai import OpenAI
from colorama import Fore
from config import MODEL, OPENAI_API_KEY, REPLY_TO_BOTS, RANDOM_ENGAGEMENT

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


def is_only_emojis(text: str) -> bool:
    text_no_discord_emotes = re.sub(r"<a?:\w+:\d+>", "", text)
    text_no_standard_emojis = re.sub(r"[\U0001F300-\U0001FAFF]+", "", text_no_discord_emotes)
    text_stripped = text_no_standard_emojis.strip()
    return len(text_stripped) == 0


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


async def get_ai_response(prompt: str, author: str, context: str, system_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation so far:\n{context}\n\nUser: {prompt}\n\nYou are replying to the user: {author}"},
            ]
        )

        reply = response.choices[0].message.content.strip()
        sanitized_reply = sanitize_response(reply)
        return sanitized_reply if sanitized_reply else "https://tenor.com/view/dyinginside-suffering-dead-old-man-gif-22047061"
    except Exception as e:
        log_error(f"Error during AI generation: {e}")
        return "https://tenor.com/view/dyinginside-suffering-dead-old-man-gif-22047061"


def generate_relevance_prompt(last_bot_reply: str, user_message: str, bot_mentioned: bool) -> str:
    mention_text = "The bot was mentioned in the message." if bot_mentioned else "The bot was not mentioned in the message."
    return (
        f"The bot's last reply: {last_bot_reply}\n"
        f"The user's new message: {user_message}\n"
        f"{mention_text}\n"
        f"Does this message require a meaningful reply? If the user's message asks about the bot being a bot, "
        f"or if it directly mentions the bot in a question, reply with 'yes'. Otherwise, reply with 'no'. "
        f"Answer only with 'yes' or 'no'."
    )


async def is_response_needed(last_reply: str, user_message: str, bot_mentioned: bool) -> bool:
    prompt = generate_relevance_prompt(last_reply, user_message, bot_mentioned)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,
            temperature=0.5,
            messages=[
                {"role": "system", "content": "You are an assistant helping decide if a response is necessary."},
                {"role": "user", "content": prompt},
            ],
        )
        decision = response.choices[0].message.content.strip().lower()
        if decision.startswith("yes"):
            log_info("AI determined that a response is needed.")
            return True
        else:
            log_info("AI determined that no response is needed.")
            return False
    except Exception as e:
        log_error(f"Error during AI relevance check: {e}")
        return False


async def is_message_relevant(message: discord.Message, context: str, prompt_file: str, bot_user_id: int) -> bool:
    is_direct_reply = (
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author
        and message.reference.resolved.author.id == bot_user_id
    )

    if is_only_emojis(message.content.strip()):
        log_custom(
            "RELEVANCE",
            "Message contains only emojis/emotes. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if "welcome" in message.content.strip().lower() and not message.author.bot:
        log_custom(
            "RELEVANCE",
            "Message is most likely a welcoming message. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if message.content.strip().startswith('.'):
        log_custom(
            "RELEVANCE",
            "Message starts with '.'. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False
    if message.content.strip().startswith('?'):
        log_custom(
            "RELEVANCE",
            "Message starts with '?'. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False
    if message.content.strip().startswith('-'):
        log_custom(
            "RELEVANCE",
            "Message starts with '-'. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False
    if message.content.strip().startswith('/'):
        log_custom(
            "RELEVANCE",
            "Message starts with '/'. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False
    if message.content.strip().startswith('!'):
        log_custom(
            "RELEVANCE",
            "Message starts with '!'. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if is_direct_reply:
        log_custom(
            "RELEVANCE",
            "Message is a direct reply to the bot. Automatically deemed relevant.",
            Fore.CYAN
        )
        return True, False

    if message.author.bot and not REPLY_TO_BOTS:
        log_custom(
            "RELEVANCE",
            "Message is from a bot, and REPLY_TO_BOTS is set to False. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if message.content.strip().startswith("http://") or message.content.strip().startswith("https://"):
        log_custom(
            "RELEVANCE",
            "Message contains only a link. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if message.attachments and not message.content.strip():
        log_custom(
            "RELEVANCE",
            "Message contains only attachments. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if message.reference is not None and message.reference.resolved is not None:
        if message.reference.resolved.author.id != bot_user_id:
            log_custom(
                "RELEVANCE",
                "Message is a reply to someone else. Deemed irrelevant.",
                Fore.CYAN
            )
            return False, False

    is_bot_mentioned = any(user.id == bot_user_id for user in message.mentions)
    if not is_bot_mentioned and message.mentions:
        log_custom(
            "RELEVANCE",
            "Message mentions other users but not the bot. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    if is_bot_mentioned:
        log_custom(
            "RELEVANCE",
            "Message contains an @ mention to the bot. Automatically deemed relevant.",
            Fore.CYAN
        )
        return True, False

    if random.random() < RANDOM_ENGAGEMENT:
        log_custom(
            "RELEVANCE",
            "Message selected for random engagement.",
            Fore.CYAN
        )
        return True, True

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
        return decision == "yes", False
    except Exception as e:
        log_error(f"Error during relevance check: {e}")
        return False, False


async def determine_gif_category(context: str, user_message: str, system_prompt: str) -> str:
    gif_system_prompt = (
        "You are a friendly assistant. Sometimes it's fun or empathetic to respond with a GIF.\n"
        "Given the conversation context and the user's last message, decide one of these categories:\n"
        " - none (if no GIF is suitable)\n"
        " - happy\n"
        " - sad\n"
        " - confused\n"
        " - angry\n"
        " - awkward\n"
        " - (or any custom label you want to add)\n"
        "Only respond with exactly one category (or 'none')."
    )

    prompt = (
        f"Conversation so far:\n{context}\n\n"
        f"User's message: {user_message}\n\n"
        f"Decide if a GIF is appropriate and if so, pick the best single category.\n"
        f"Reply ONLY with 'none' or one of the known categories (happy, sad, confused, angry, awkward)."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=20,
            temperature=0.7,
            messages=[
                {"role": "system", "content": gif_system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        category_decision = response.choices[0].message.content.strip().lower()
        return category_decision
    except Exception as e:
        log_error(f"Error during GIF category determination: {e}")
        return "none"
