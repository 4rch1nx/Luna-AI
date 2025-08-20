import requests
import json
import os
from datetime import datetime
import random
from difflib import SequenceMatcher

# Terminal color codes
COLOR_USER = "\033[96m"     # Blue
COLOR_LUNA = "\033[92m"     # Magenta
COLOR_RESET = "\033[0m"      # Reset

# Model name (update this if you switch models)
MODEL_NAME = "llama3:8b"

# Load system prompt once at startup
try:
    with open("luna_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print("Error: 'luna_prompt.txt' not found!")
    exit(1)

# Memory file path
MEMORY_FILE = "memory.json"

# Load or create memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        try:
            MEMORY = json.load(f)
        except json.JSONDecodeError:
            print("Memory file is corrupt. Starting fresh.")
            MEMORY = {
                "conversation_history": [],
                "user_info": {},
                "luna_notes": [],
                "knowledge": ""
            }
else:
    MEMORY = {
        "conversation_history": [],
        "user_info": {},
        "luna_notes": [],
        "knowledge": ""
    }

# Load knowledge file (from PDF or TXT)
KNOWLEDGE_FILE = "user_knowledge.txt"
try:
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as kf:
        MEMORY["knowledge"] = kf.read()
except FileNotFoundError:
    pass


def save_memory():
    """Save current memory to file"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(MEMORY, f, indent=2)


def extract_user_info(user_input):
    """Try to extract basic user info from input"""
    lower = user_input.lower()

    if "my name is " in lower:
        name = lower.split("my name is ")[1].split(".")[0].strip().capitalize()
        MEMORY["user_info"]["name"] = name
        MEMORY["luna_notes"].append(f"User's name is {name}. Annoying, but easy to remember.")

    elif "i like " in lower:
        like = lower.split("i like ")[1].split(".")[0].strip()
        MEMORY["user_info"]["likes"] = like
        MEMORY["luna_notes"].append(f"User likes {like}. Predictable.")

    elif "i love " in lower:
        love = lower.split("i love ")[1].split(".")[0].strip()
        MEMORY["user_info"]["likes"] = love
        MEMORY["luna_notes"].append(f"User loves {love}. How original.")

    elif "i am " in lower or "i'm " in lower:
        desc = lower.replace("i am ", "").replace("i'm ", "").split(".")[0].strip()
        MEMORY["user_info"]["description"] = desc
        MEMORY["luna_notes"].append(f"User describes themselves as '{desc}'. Lame.")


def log_request_response(prompt, response):
    """Log the full prompt and AI response to a log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"""---
[{timestamp}]
== PROMPT ==
{prompt}

== RESPONSE ==
{response}
"""

    with open("web_logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


def generate_pun(topic):
    """Generate a pun based on a given topic"""
    pun_templates = [
        f"Why did the {topic} go to therapy? It had too many issues!",
        f"I told my {topic} a joke... it didn't laugh. Must be a hardware issue.",
        f"The {topic} said, 'I byte off more than I can chew.'",
        f"Never trust a {topic}—they might take things for a byte.",
        f"If you {topic}, do it with passion... or don’t. I won’t judge. Much.",
    ]
    return random.choice(pun_templates)


def generate_limerick(topic):
    """Generate a limerick about a given topic"""
    limerick_templates = [
        f"There once was a {topic} so grand,\nWho lived in a digital land.\nWith a joke and a rhyme,\nIt danced through space and time,\nAnd laughed like a bot gone mad!"
    ]
    return random.choice(limerick_templates)


def remove_repeated_start(reply, threshold=0.4):
    """Avoid repeating the same opening line"""
    lines = reply.strip().split('\n')
    first_line = lines[0].strip()

    for msg in MEMORY["conversation_history"]:
        if msg.startswith("Luna:"):
            old_reply = msg[len("Luna: "):]
            if SequenceMatcher(None, first_line, old_reply).ratio() > threshold:
                return '\n'.join(lines[1:]) if len(lines) > 1 else "(Hmm...)"

    return '\n'.join(lines)


def luna_response(user_input):
    global MEMORY

    # Add user message to history
    MEMORY["conversation_history"].append(f"User: {user_input}")

    # Keep only last 5 messages
    if len(MEMORY["conversation_history"]) > 5:
        MEMORY["conversation_history"].pop(0)

    # Try to extract facts
    extract_user_info(user_input)

    # Check if user asked for a pun or limerick
    lower_input = user_input.lower()
    custom_content = ""

    if "pun" in lower_input or "joke" in lower_input:
        topic = lower_input.replace("make me a pun about ", "") \
                          .replace("tell me a pun about ", "") \
                          .replace("generate a pun about ", "") \
                          .strip()
        if not topic:
            topic = "something"
        custom_content += f"\n[Custom Pun]\n{generate_pun(topic)}\n"

    elif "limerick" in lower_input:
        topic = lower_input.replace("make me a limerick about ", "") \
                          .replace("tell me a limerick about ", "") \
                          .replace("generate a limerick about ", "") \
                          .strip()
        if not topic:
            topic = "something"
        custom_content += f"\n[Custom Limerick]\n{generate_limerick(topic)}\n"

    # If there's custom content, return it and skip AI call
    if custom_content:
        log_request_response("Custom Feature Triggered", custom_content)
        return custom_content.strip()

    # Build full prompt with history + user info + knowledge
    history_str = "\n".join(MEMORY["conversation_history"])
    user_info_str = "\n".join([f"{k}: {v}" for k, v in MEMORY["user_info"].items()])
    luna_notes_str = "\n".join(MEMORY["luna_notes"])
    knowledge_str = MEMORY["knowledge"]

    full_prompt = f"""{SYSTEM_PROMPT}

== Knowledge ==
{knowledge_str}

== User Info ==
{user_info_str}

== Notes ==
{luna_notes_str}

== Previous Messages ==
{history_str}

Now respond to:"""

    full_prompt_for_log = full_prompt  # Save for logging

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "stream": False
            }
        )

        ai_reply = response.json().get("response", "No response")

        # Avoid repetition
        ai_reply = remove_repeated_start(ai_reply)

        # Log request and response
        log_request_response(full_prompt_for_log, ai_reply)

        # Add AI reply to history
        MEMORY["conversation_history"].append(f"Luna: {ai_reply}")
        save_memory()
        return ai_reply

    except Exception as e:
        return f"Connection error: {str(e)}"


def main():
    print(f"Using model: {MODEL_NAME}")
    print("Luna is online.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("She's listening closely...\n")

    while True:
        user = input(f"{COLOR_USER}You: {COLOR_RESET}")
        if user.lower() in ["exit", "quit"]:
            print(f"{COLOR_LUNA}Luna: *vanishes*{COLOR_RESET}")
            MEMORY["luna_notes"].append("Conversation ended. Finally some peace.")
            save_memory()
            break
        reply = luna_response(user)
        print(f"{COLOR_LUNA}Luna: {reply}{COLOR_RESET}")


if __name__ == "__main__":
    main()
