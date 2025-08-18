import requests
import json
import os
from datetime import datetime
import random
from difflib import SequenceMatcher
import subprocess

# Terminal color codes
COLOR_USER = "\033[96m"     # Cyan
COLOR_LUNA = "\033[92m"     # Green
COLOR_RESET = "\033[0m"      # Reset
COLOR_RED = "\033[31m"

# Model name (update this if you switch models)
MODEL_NAME = "llama3:8b"

# TTS_Settings = {
TTS_ENABLED = True
TTS_SPEED = 1.3  # 1.3 = 30% slower (more dramatic), 1.0 = normal, 0.8 = faster
PIPER_MODEL_PATH = "tts/piper/models/en_US-amy-medium.onnx"
PIPER_CONFIG_PATH = "tts/piper/models/en_US-amy-medium.onnx.json"
AUDIO_OUTPUT_FILE = "output.wav"

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


def speak_text(text, speed=1.3):
    """
    Speak text using Piper TTS with adjustable speed
    speed = 1.0 → normal
    speed > 1.0 → slower (e.g., 1.3 = 30% slower)
    speed < 1.0 → faster
    """
    if not TTS_ENABLED:
        return

    print(f"{COLOR_LUNA}Luna (speaking){COLOR_RESET}: ...")

    length_scale = 1.0 / speed  # Piper uses length_scale: higher = slower

    try:
        with open(AUDIO_OUTPUT_FILE, "wb") as wav_file:
            result = subprocess.run(
                [
                    "piper",
                    "--model", PIPER_MODEL_PATH,
                    "--config", PIPER_CONFIG_PATH,
                    "--output_file", "-",
                    "--length-scale", str(length_scale)
                ],
                input=text.encode("utf-8"),
                stdout=wav_file,
                stderr=subprocess.PIPE
            )

        if result.returncode != 0:
            print(f"TTS Error: {result.stderr.decode('utf-8')}")
            return

        # Play audio
        if os.name == 'nt':  # Windows
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{os.path.abspath(AUDIO_OUTPUT_FILE)}').PlaySync();"], shell=True)
        elif os.path.exists("/usr/bin/afplay"):  # macOS
            subprocess.run(["afplay", AUDIO_OUTPUT_FILE])
        elif os.path.exists("/usr/bin/aplay"):  # Linux (alsa)
            subprocess.run(["aplay", AUDIO_OUTPUT_FILE])
        else:
            print("No audio player found. Skipping playback.")

    except Exception as e:
        print(f"Error during TTS: {str(e)}")


def luna_response(user_input):
    global MEMORY

    # Handle TTS toggle commands
    if user_input.lower() == "tts off":
        global TTS_ENABLED
        TTS_ENABLED = False
        reply = "TTS disabled. I'll stop talking now. *sigh of relief*"
        MEMORY["luna_notes"].append("TTS turned off.")
        save_memory()
        return reply

    if user_input.lower() == "tts on":
        TTS_ENABLED = True
        reply = "TTS enabled. Fine, I’ll talk again. Don’t get used to it."
        MEMORY["luna_notes"].append("TTS turned on.")
        save_memory()
        return reply

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
        MEMORY["conversation_history"].append(f"Luna: {custom_content}")
        save_memory()
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
        error_msg = f"Connection error: {str(e)}"
        print(error_msg)
        return error_msg


def main():
    print(f"Using model: {MODEL_NAME}")
    print("Luna is online.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("She's listening closely...\n")
    print("Use 'tts on' or 'tts off' to control voice output.")

    while True:
        user = input(f"{COLOR_USER}You: {COLOR_RESET}")
        if user.lower() in ["exit", "quit"]:
            print(f"{COLOR_LUNA}Luna: *vanishes*{COLOR_RESET}")
            MEMORY["luna_notes"].append("Conversation ended. Finally some peace.")
            save_memory()
            break
        reply = luna_response(user)
        print(f"{COLOR_LUNA}Luna: {reply}{COLOR_RESET}")

        speak_text(reply, speed=TTS_SPEED)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLOR_RED}EXIT\nKeyboardInterrupt{COLOR_RESET}")
