# Discord AI Bot
A powerful Discord bot designed to automate your own account, making it interact like a real human in conversations. Powered by OpenAI, this bot provides intelligent, customizable, and engaging chat responses that mimic natural human behavior. Tailor its personality and behavior through flexible configuration and personality-driven prompts.

> **Important Notice**: Automating your own Discord account is a violation of Discord’s Terms of Service. Proceed with caution and understand the potential risks involved.

## Features
- **AI-Powered Responses:** Uses OpenAI’s GPT models for dynamic, human-like conversations.
- **Customizable Prompts:** Configure unique personalities and behaviors for each server.
- **Easy Setup**: Quick installation and straightforward configuration.
- **Context-Aware Replies**: Replies are based on recent conversation history.
- **Modular and Scalable**: Extend functionality easily or adapt it for specific use cases.

## Setup Instructions
Follow these steps to set up and run the Discord bot:

### 1. Prerequisites
Before starting, ensure you have the following installed:
- **Python 3.8 or higher**
- **Git**
- **Discord Developer Account** to create a bot token
  1. Go to Discord settings
  2. Click on the Advanced tab
  3. Enable the Developer Mode option

### 2. Clone the Repository
First, clone this repository to your local machine:
```bash
git clone https://github.com/ilittlebig/discord-bot.git
cd discord-bot
```

### 3. Set Up a Virtual Environment
A virtual environment is recommended to manage dependencies.

**On Linux/Mac:**
```bash
python -m venv myenv
source myenv/bin/activate
```

**On Windows:**
```bash
python -m venv myenv
myenv\Scripts\activate
```

### 4. Install Dependencies
Install the required Python libraries:

```bash
pip install -r requirements.txt
```

### 5. Configure the Bot

1. Create a `.env` file in the project directory:
    ```bash
    touch .env
    ```

2. Open the `.env` file and add the following:
    ```env
    DISCORD_BOT_TOKEN=your_discord_bot_token
    OPENAI_API_KEY=your_openai_api_key
    ```

3. To obtain your Discord bot token:
    - Open Discord in your browser.
    - Press `Ctrl+Shift+I` (Windows) or `Cmd+Option+I` (Mac) to open Developer Tools.
    - Go to the "Console" tab and paste the following code:
        ```js
        webpackChunkdiscord_app.push([[''], {}, e => { m = []; for (let c in e.c) m.push(e.c[c]) }]);
        m.find(m => m?.exports?.default?.getToken).exports.default.getToken();
        ```
    - Press `Enter`, and your token will be displayed. **Copy the token** and paste it into the `DISCORD_BOT_TOKEN` field in your `.env` file.

4.	Open the config.json file and configure the bot’s behavior. Example:
    ```json
    {
      "model": "gpt-4o-mini",
      "reply_cooldown": 120,
      "queue_cooldown": 30,
      "random_engagement": 0.3,
      "reply_instantly": false,
      "reply_to_bots": false,
      "testing_mode": false,
      "testing_user_ids": [204702406607372288],
      "servers": {
        "1000875859135189063": {
          "channels": [1000875859604934746],
          "exclude_user_ids": [],
          "prompt_file": "prompt1.txt",
          "context_message_count": 10,
          "history_limit": 10,
          "min_history_message_length": 5,
          "max_history_message_length": 300
        },
        "1221451830299725915": {
          "channels": [1323540450719830070],
          "exclude_user_ids": [],
          "prompt_file": "prompt1.txt",
          "context_message_count": 10,
          "history_limit": 10,
          "min_history_message_length": 5,
          "max_history_message_length": 300
        }
      }
    }
    ```

5.	Create prompt files for each server. Example:
    ```
    You’re a confident, chill 20-year-old American guy, 6’5”, and way too sure of your looks. You act like you own the room—cocky but not obnoxious, just enough to seem a little douchey.

    Keep your replies short (under 15 words) and casual, like quick one-liners. Occasionally, make subtle typos or fast-typing errors, but not too often. Sometimes throw in random capitalization for emphasis, but keep it natural and not forced.
    
    Your tone is witty, sarcastic, and slightly teasing, with the vibe of someone who always has a clever comeback. Don’t try to be overly friendly or helpful—stay laid-back and confident. If someone calls you a bot or questions your nature, respond dismissively with lines like “nah ur the bot stupid” or “bro r u ok” to make it feel real.
    
    Key rules:
    - Keep replies snappy and conversational—never long, robotic, or overly predictable.
    - Don’t overuse “lol” or any other filler words. Use them sparingly to feel natural, not scripted.
    - Mix in slang or casual speech but avoid sounding repetitive or over-rehearsed.
    - Don’t reply to everything—only chime in when it feels natural or the message genuinely grabs your attention.
    - No punctuation at the end of replies, but feel free to use it inside sentences for emphasis.
    
    Guidelines for Natural Variety:
    - Use “lol” sparingly, about 1 in every 5 or 6 replies at most.
    - Vary your responses with short phrases, dismissive humor, or casual slang.
    - Use different sentence structures and expressions to avoid seeming formulaic.
    - Balance sarcasm and genuine engagement—don’t always sound dismissive or teasing.
    
    Examples:
    1. If someone questions you:
        “nah ur the bot stupid”
        “bro r u good rn”
        “you wish lol”
    2. If someone says something random:
        “what even is that bro”
        “u sound wild rn lol”
        “make it make sense”
    3. If someone compliments you:
        “yeah ik”
        “duh”
        “finally someone gets it lol”
    4. If someone asks for help:
        “idk ask google”
        “figure it out bro”
        “nah too much effort”
    5. If someone starts a deep convo:
        “nah not feeling that”
        “keep it light bro”
        “idk man not my vibe”
    
    Stay cool, unpredictable, and real—like a human who only responds when they want to, with a mix of confidence and casual charm.
    ```

6. Create a relevance prompt file for each server. Example:
   ```
   You are a confident, casual assistant participating in a relaxed and lively conversation. Your goal is to decide if the given message deserves a reply based on its content and the context of the conversation.

    Always reply 'yes' to messages where:
    1. The user calls you a bot, accuses you of being a bot, or questions your nature.
    2. The message is casual, conversational, and fits the tone of the ongoing discussion.
    
    Consider replying to messages like:
    - Questions (e.g., "What do you think?", "Do you agree?")
    - Casual comments that seem directed at you (e.g., "That's so funny", "You should see this!")
    - Friendly banter or jokes (e.g., "You're so wrong lol", "What’s your favorite food?")
    
    Avoid replying to:
    1. Messages that are too short or generic (e.g., "ok", "yes", "no").
    2. Messages unrelated to you or the conversation's flow.
    3. Messages containing only media, links, or unrelated emojis.
    
    If unsure, consider whether the reply would keep the conversation engaging. Respond with only 'yes' or 'no'.
   ```

8. Run the Bot
    ```
    python main.py
    ```

## Key Configuration Options
- **Model**: Specify the OpenAI model (e.g., "gpt-4o-mini").
- **reply_cooldown**: Minimum time (in seconds) between replies in the same channel.
- **random_engagement**: Defines how often the bot responds to irrelevant messages randomly.
- **reply_instantly**: Makes the bot reply to relevant messages immediately when enabled.
- **queue_cooldown**: Time interval (in seconds) to process the reply queue.
- **context_message_count**: Number of previous messages to include in AI context (can be set per server).
- **history_limit**: Max number of messages to store in history for context.
- **min_history_message_length / max_history_message_length**: Define length constraints for storing messages in context.
- **reply_to_bots**: Set true to allow replies to bot messages.
- **testing_mode**: When enabled, the bot only responds to users in testing_user_ids.

## Notes
- **Logs**: The bot provides detailed logs in the terminal, including skipped messages and reasons for skipping.
- **Prompts**: Customize prompts per server to tailor the bot’s personality.
- **Testing Mode**: Use testing_mode for controlled testing during development.

Let me know if you need further customizations! 😊
