#
#
# Author: Elias Sjödin
# Created: 2024-12-31

from datetime import datetime

conversation_history = {}
user_interaction_context = {}

def add_to_history(server_id, channel_id, author, content, history_limit):
    if server_id not in conversation_history:
        conversation_history[server_id] = {}
    if channel_id not in conversation_history[server_id]:
        conversation_history[server_id][channel_id] = []

    conversation_history[server_id][channel_id].append(f"{author}: {content}")

    # Limit history size
    if len(conversation_history[server_id][channel_id]) > history_limit:
        conversation_history[server_id][channel_id].pop(0)


def get_conversation_context(server_id, channel_id, max_messages):
    if server_id in conversation_history and channel_id in conversation_history[server_id]:
        history = conversation_history[server_id][channel_id]
        return "\n".join(history[-max_messages:])
    return ""


def update_user_interaction(server_id, channel_id, user_id, bot_reply):
    if server_id not in user_interaction_context:
        user_interaction_context[server_id] = {}
    if channel_id not in user_interaction_context[server_id]:
        user_interaction_context[server_id][channel_id] = {}

    user_interaction_context[server_id][channel_id][user_id] = {
        "last_reply": bot_reply,
        "timestamp": datetime.now(),
    }


def get_last_user_interaction(server_id, channel_id, user_id):
    return user_interaction_context.get(server_id, {}).get(channel_id, {}).get(user_id)
