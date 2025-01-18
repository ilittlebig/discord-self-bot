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
REPLY_TO_BOTS = cfg["reply_to_bots"]
TESTING_MODE = cfg["testing_mode"]
TESTING_USER_IDS = cfg["testing_user_ids"]
SERVERS = cfg["servers"]
RANDOM_ENGAGEMENT = cfg["random_engagement"]
REPLY_INSTANTLY = cfg["reply_instantly"]
PROHIBITED_PHRASES = cfg["prohibited_phrases"]
NORMAL_REPLY_PROBABILITY = cfg["normal_reply_probability"]
GIF_CATEGORIES = cfg["gif_categories"]
GIF_PROBABILITY = cfg["gif_probability"]
MAX_QUEUE_AGE_SECONDS = cfg["max_queue_age_seconds"]
REPLY_BATCH_SIZE = cfg["reply_batch_size"]
