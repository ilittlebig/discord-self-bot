# Handles OpenAI interactions and message relevance detection
#
# Author: Elias Sjödin
# Created: 2024-12-31

import re
import discord
import os
import string
import random
import datetime
from datetime import timedelta
from logger import log_info, log_custom, log_error, log_warning
from openai import OpenAI
from colorama import Fore
from config import MODEL, OPENAI_API_KEY, REPLY_TO_BOTS, RANDOM_ENGAGEMENT

client = OpenAI(api_key=OPENAI_API_KEY)

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


def sanitize_response(response: str) -> str:
    if not response:
        return None
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


async def categorize_message(message):
    try:
        prompt = (
            "You are a message categorization assistant. "
            "Analyze the following message and categorize it as one of these: "
            "'critical' (if it accuses the bot of being fake, a bot, an AI, or NPC), "
            "'normal' (if it's general conversation). "
            "Provide only the category name as output.\n\n"
            f"Message: {message.content}"
        )

        response = await get_categorization_response(prompt)
        category = response.lower().strip()

        if category not in {"critical", "normal"}:
            log_warning(f"AI returned an invalid category: {category}. Defaulting to 'normal'.")
            return "normal"

        log_info(f"AI categorized message '{message.content[:30]}...' as {category}.")
        return category
    except Exception as e:
        log_error(f"Error in AI categorization: {e}")
        return "normal"


async def get_categorization_response(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=10,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        log_error(f"Error during AI categorization: {e}")
        return "normal"


async def get_ai_response(prompt: str, author: str, context: str, system_prompt: str) -> str:
    try:
        # Occasionally introduce typos or text shortcuts to appear more human
        typo_instructions = ""
        if random.random() < 0.15:  # 15% chance for typo instructions
            typo_options = [
                "Occasionally make small typos like missing a letter or swapping two letters.",
                "Sometimes use text shortcuts like 'u' instead of 'you' or 'rn' instead of 'right now'.",
                "Occasionally skip apostrophes in contractions like 'dont' instead of 'don't'.",
                "Sometimes make a small spelling error in a longer word."
            ]
            typo_instructions = random.choice(typo_options) + " "
        
        content_prompt = (
            "Conversation so far:\n"
            f"{context}\n\n"
            "These messages represent authentic human interactions. "
            "Match the phrasing of these messages to blend naturally into the conversation.\n\n"
            f"User: {prompt}\n\n"
            f"You are replying to the user: {author}\n\n"
            f"{typo_instructions}Keep your response short and casual. "
            "FINAL REMINDER: You NEVER capitalize words randomly in the middle of sentences. "
            "Capitalize only proper nouns or the first word of a sentence. "
            "Any deviation from this will be considered invalid."
        )

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,
            temperature=0.9,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_prompt},
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


async def is_response_needed(
    last_reply: str,
    user_message: str,
    bot_mentioned: bool,
    display_name: str,
    is_direct_reply: bool
) -> bool:
    lower_msg = user_message.lower()
    lower_name = display_name.lower()

    # Always respond to direct replies or mentions
    if is_direct_reply or bot_mentioned:
        return True
        
    # Always respond to messages that might be questioning if the bot is a bot
    always_reply_keywords = [
        "are you a bot",
        "you're a bot",
        "are you an npc",
        "you're an npc",
        "are you real",
        "are you ai",
        "are you human",
        "are you fake",
        "you're fake",
        "you're not real"
    ]

    if any(kw in lower_msg for kw in always_reply_keywords):
        return True
    if lower_name in lower_msg and any(phrase in lower_msg for phrase in ["is a bot", "is an npc", "is fake", "is ai"]):
        return True
        
    # Respond to questions directed at anyone
    question_starters = ["what", "how", "why", "when", "where", "who", "can", "could", "would", "should", "is", "are", "do", "does", "did"]
    if any(lower_msg.strip().startswith(starter) for starter in question_starters) and "?" in lower_msg:
        return True
        
    # Respond to messages that seem to be seeking engagement
    engagement_phrases = ["anyone", "somebody", "someone", "guys", "y'all", "everyone", "anybody", "thoughts", "opinion", "what do you think"]
    if any(phrase in lower_msg for phrase in engagement_phrases):
        return True

    direct_reply_text = "The user is replying directly to one of the bot's messages." if is_direct_reply else "The user is NOT replying directly."
    mention_text = f"The bot was {'mentioned' if bot_mentioned else 'NOT mentioned'} in the message."

    system_content = (
        "You are an assistant deciding if a response to a user's message is necessary. "
        "Your primary goal is to identify when the bot should reply meaningfully. "
        f"The bot's display name is '{display_name}'. Answer 'yes' if the user's message clearly requires a response. "
        "This includes any of the following: "
        "- The user asks a question, directly or indirectly (e.g., starts with 'can', 'what', 'why', 'how', or similar). "
        "- The user makes a request (e.g., 'say [something]', 'tell me [something]', 'do [something]'). "
        "- The user accuses the bot of being a bot or tests its humanity (e.g., 'are you a bot?', 'say this exact thing'). "
        "- The user explicitly addresses or mentions the bot in a meaningful way. "
        "- The message is interesting, provocative, or would naturally invite a response in human conversation. "
        "- The message contains strong opinions or statements that would typically prompt reactions. "
        "Answer 'no' only if the message is completely random, irrelevant, or clearly not meant to engage anyone."
    )

    user_content = (
        f"The bot's last reply: {last_reply}\n"
        f"The user's new message: {user_message}\n\n"
        f"{direct_reply_text}\n"
        f"{mention_text}\n\n"
        f"Does this message require a meaningful reply? If the user's message asks about the bot being a bot, "
        f"or if it directly mentions the bot in a question, reply with 'yes'. Otherwise, reply with 'no'.\n\n"
        "Answer ONLY with 'yes' or 'no' — do they need a response?"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,
            temperature=0.7,  # Increased from 0.5 to be more likely to say yes
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
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


async def is_message_relevant(
    message: discord.Message,
    context: str,
    display_name: str,
    prompt_file: str,
    bot_user_id: int
) -> bool:
    is_direct_reply = (
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author
        and message.reference.resolved.author.id == bot_user_id
    )

    # Check for multi-line spam messages
    try:
        recent_messages = []
        async for msg in message.channel.history(limit=5, after=datetime.datetime.utcnow() - timedelta(seconds=5)):
            recent_messages.append(msg)
            
        author_messages = [msg for msg in recent_messages if msg.author == message.author]
        
        # If there are multiple messages from the same author in quick succession
        if len(author_messages) > 2:
            log_custom(
                "RELEVANCE",
                f"Detected multi-line spam from {message.author.name} - {len(author_messages)} messages in 5 seconds. Ignoring.",
                Fore.CYAN
            )
            return False, False
    except Exception as e:
        log_error(f"Error checking for multi-line spam: {e}")

    if is_only_emojis(message.content.strip()):
        log_custom(
            "RELEVANCE",
            "Message contains only emojis/emotes. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    # More comprehensive welcome message detection
    welcome_patterns = ["welcome", "welcom", "wlcm", "welc", "joined", "new member", "say hi to"]
    if any(pattern in message.content.strip().lower() for pattern in welcome_patterns) and not message.author.bot:
        log_custom(
            "RELEVANCE",
            "Message appears to be a welcoming message. Deemed irrelevant.",
            Fore.CYAN
        )
        return False, False

    # Check for command prefixes
    command_prefixes = ['.', '?', '-', '/', '!', '$', '>']
    if any(message.content.strip().startswith(prefix) for prefix in command_prefixes):
        log_custom(
            "RELEVANCE",
            f"Message starts with command prefix '{message.content[0]}'. Deemed irrelevant.",
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

    # Point drop detection - avoid responding to these
    point_drop_patterns = [r"\b[a-zA-Z0-9]{5,8}\b", r"\b[,.!?][a-zA-Z0-9]{4,7}\b"]
    if any(re.search(pattern, message.content) for pattern in point_drop_patterns) and len(message.content.strip()) < 10:
        log_custom(
            "RELEVANCE",
            "Message appears to be a point drop response. Ignoring.",
            Fore.CYAN
        )
        return False, False

    # Significantly increased random engagement probability
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
        f"The bot's display name is '{display_name}'. Are they talking to you?\n"
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
        " - flirty\n"
        " - (or any custom label you want to add)\n"
        "Only respond with exactly one category (or 'none')."
    )

    prompt = (
        f"Conversation so far:\n{context}\n\n"
        f"User's message: {user_message}\n\n"
        f"Decide if a GIF is appropriate and if so, pick the best single category.\n"
        f"Reply ONLY with 'none' or one of the known categories (happy, sad, confused, angry, awkward, flirty)."
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
