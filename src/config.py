#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

with open(CONFIG_PATH, "r") as f:
    cfg = json.load(f)

MODEL = cfg["model"]
REPLY_COOLDOWN = cfg["reply_cooldown"]
QUEUE_COOLDOWN = cfg["queue_cooldown"]
CONTEXT_MESSAGE_COUNT = cfg["context_message_count"]
HISTORY_LIMIT = cfg["history_limit"]
REPLY_TO_BOTS = cfg["reply_to_bots"]
TESTING_MODE = cfg["testing_mode"]
TESTING_USER_IDS = cfg["testing_user_ids"]
SERVERS = cfg["servers"]
MIN_CHARACTERS_TO_REPLY_TO = cfg["min_characters_to_reply_to"]
MAX_CHARACTERS_TO_REPLY_TO = cfg["max_characters_to_reply_to"]
MAX_HISTORY_MESSAGE_LENGTH = cfg["max_history_message_length"]
