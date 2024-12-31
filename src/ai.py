#
#
# Author: Elias Sjödin
# Created: 2024-12-31

import string
from llama_cpp import Llama
from config import MODEL_PATH
from logger import log_error

llm = Llama(model_path=MODEL_PATH)

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


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
    response = response.split("\n")[0].strip()
    response = remove_punctuation(response)
    words = response.split()

    if len(words) < 2 or len(words) > 30:
        return None
    return response


def load_prompt(prompt_file: str) -> str:
    """
    Loads the prompt text from the specified file.
    """
    try:
        with open("prompts/" + prompt_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"Prompt file '{prompt_file}' not found. Please check your configuration.")


async def get_ai_response(prompt: str, context: str, system_prompt: str) -> str:
    """
    Generate a short, single-sentence response using GPT4All locally.
    """
    def build_prompt(sys_prompt, ctx, user_prompt):
         return (
            f"{sys_prompt}\n\n"
            f"Conversation so far:\n{ctx}\n\n"
            f"User: {user_prompt}\n"
            f"Assistant:"
        )

    full_prompt = build_prompt(system_prompt, context, prompt)
    print(full_prompt)
    for attempt in range(5):
        try:
            response_data = llm(full_prompt, max_tokens=50)
            raw_reply = response_data["choices"][0]["text"].strip()
            sanitized_reply = sanitize_response(raw_reply)
            if sanitized_reply:
                return sanitized_reply
        except Exception as e:
            log_error(f"Error during AI generation: {e}")

    return "sorry, can't think of anything to say"
