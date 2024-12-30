import discord
import asyncio
import random

from discord.ext import tasks
from llama_cpp import Llama
from dotenv import load_dotenv

import os
import json
import string

# ---------------------------
# Load Environment Variables
# ---------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ---------------------------
# Load Configuration File
# ---------------------------
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# ---------------------------
# GPT4All / LLaMa Configuration
# ---------------------------
MODEL_PATH = config["model_path"]
llm = Llama(model_path=MODEL_PATH)

# ---------------------------
# Discord Client Initialization
# ---------------------------
client = discord.Client()

# ---------------------------
# Variables & Constants
# ---------------------------
last_message_ids = {}


def load_prompt(prompt_file: str) -> str:
    """
    Loads the prompt text from the specified file.
    """
    try:
        with open(prompt_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"Prompt file '{prompt_file}' not found. Please check your configuration.")


def remove_punctuation(text: str) -> str:
    """
    Removes all punctuation from the given string.
    """
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)


def sanitize_response(response: str) -> str:
    """
    Sanitizes the response to ensure:
      - single-line (split at first newline),
      - single-sentence,
      - no uppercase letters,
      - no punctuation,
      - length constraints (10 <= len <= ~30 words).
    Returns None if it fails, prompting a regeneration attempt.
    """
    response = response.split("\n")[0].strip().lower()
    response = remove_punctuation(response)
    words = response.split()

    if len(words) < 2 or len(words) > 30:
        return None
    return response


async def get_ai_response(prompt: str, context: str, system_prompt: str) -> str:
    """
    Generate a short, single-sentence response using GPT4All locally.
    """
    def build_prompt(sys_prompt, ctx, user_prompt):
        return (
            f"{sys_prompt}\n\n"
            f"recent messages (context):\n{ctx}\n\n"
            f"user: {user_prompt}\n"
            f"assistant (one-sentence reply, no capitals or punctuation):"
        )

    full_prompt = build_prompt(system_prompt, context, prompt)

    for attempt in range(5):
        try:
            response_data = llm(full_prompt, max_tokens=50)
            raw_reply = response_data["choices"][0]["text"].strip()
            sanitized_reply = sanitize_response(raw_reply)
            if sanitized_reply:
                return sanitized_reply
        except Exception as e:
            print(f"Error during AI generation: {e}")

    return "sorry, can't think of anything to say"


@tasks.loop(seconds=config["tasks_loop_seconds"])
async def reply_to_messages():
    """
    Periodically checks the most recent messages in the specified channels and replies.
    """
    global last_message_ids

    try:
        context_message_count = config["context_message_count"]
        history_limit = config["history_limit"]
        reply_to_bots = config["reply_to_bots"]
    except KeyError as e:
        print(f"Missing required configuration: {e}. Please define it in config.json.")
        return

    for server_id, server_config in config["servers"].items():
        try:
            system_prompt = load_prompt(server_config["prompt_file"])

            for channel_id in server_config["channels"]:
                try:
                    guild = discord.utils.get(client.guilds, id=int(server_id))
                    if not guild:
                        print(f"Server with ID {server_id} not found. Skipping...")
                        continue

                    channel = discord.utils.get(guild.text_channels, id=int(channel_id))
                    if not channel:
                        print(f"Channel with ID {channel_id} not found in server {server_id}. Skipping...")
                        continue

                    messages = []
                    async for message in channel.history(limit=history_limit):
                        messages.append(message)

                    if not messages:
                        print(f"No messages found in channel {channel.name} ({channel.id}). Skipping...")
                        continue

                    latest_message = messages[0]
                    print(f"\nProcessing latest message in #{channel.name} ({channel.id}):")
                    print(f"Author: {latest_message.author.name} ({latest_message.author.id})")
                    print(f"Content: {latest_message.content}")

                    if not reply_to_bots and latest_message.author.bot:
                        print(f"Message is from a bot. Skipping...")
                        continue

                    testing_mode = config["testing_mode"]
                    allowed_users = config["testing_user_ids"]

                    already_replied = latest_message.id == last_message_ids.get(channel_id)
                    is_own_message = latest_message.author == client.user
                    if already_replied:
                        print(f"Message already replied to. Skipping...")
                        continue
                    if is_own_message and not testing_mode:
                        print(f"Bot's own message and not in testing mode. Skipping...")
                        continue
                    if testing_mode and latest_message.author.id not in allowed_users:
                        print(f"Testing mode active, and author not in allowed users. Skipping...")
                        continue

                    if latest_message.author.id in server_config["exclude_user_ids"]:
                        print(f"Author is in the excluded user list. Skipping...")
                        continue

                    relevant_messages = messages[1 : context_message_count + 1]
                    context_str = "\n".join(
                        f"{msg.author.name}: {msg.content}" for msg in reversed(relevant_messages)
                    )
                    print(f"\nContext for AI reply (last {context_message_count} messages):")
                    print(context_str)

                    reply = await get_ai_response(latest_message.content, context_str, system_prompt)
                    print(f"\nGenerated AI reply: {reply}")

                    await asyncio.sleep(random.uniform(5.5, 13.5))
                    await latest_message.reply(reply)
                    print(f"Replied to {latest_message.author.name} in #{channel.name}.")

                    last_message_ids[channel_id] = latest_message.id

                except Exception as e:
                    print(f"Error in channel {channel_id}: {e}")

        except Exception as e:
            print(f"Error in server {server_id}: {e}")


@client.event
async def on_ready():
    """Called when the bot has successfully connected to Discord."""
    print(f"Logged in as {client.user}!")
    reply_to_messages.start()


client.run(TOKEN)
