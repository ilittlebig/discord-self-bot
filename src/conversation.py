#
#
# Author: Elias Sjödin
# Created: 2024-12-31

conversation_history = {}

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
