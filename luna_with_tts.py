import requests
import json
import os
from datetime import datetime
import time
import random
from difflib import SequenceMatcher
import subprocess
import re
import argparse

from settings import *


def startup():
    print("Starting up")

    print(f"Loading Luna prompt from {COLOR_USER}'{LUNA_PROMPT_FILE}'{COLOR_RESET}...")
    global SYSTEM_PROMPT
    try:
        with open(LUNA_PROMPT_FILE, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
        print(f"{COLOR_LUNA}Luna prompt loaded.{COLOR_RESET}")
    except FileNotFoundError:
        print(f"{COLOR_RED}Error: {COLOR_USER}'{LUNA_PROMPT_FILE}'{COLOR_RESET} not found!\nExiting{COLOR_RESET}")
        exit(1)

    print()

    global MEMORY
    print(f"Loading Luna's short memory from {COLOR_USER}'{MEMORY_FILE}'{COLOR_RESET}...")
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try:
                MEMORY = json.load(f)
            except json.JSONDecodeError:
                print(f"{COLOR_RED}Short memory file is corrupt. Starting fresh.{COLOR_RESET}")
                MEMORY = {
                    "conversation_history": [],
                    "user_info": {},
                    "luna_notes": [],
                    "knowledge": ""
                }
    else:
        print(f"{COLOR_YELLOW}No short memory. Starting fresh.{COLOR_RESET}")
        MEMORY = {
            "conversation_history": [],
            "user_info": {},
            "luna_notes": [],
            "knowledge": ""
        }

    print(f"{COLOR_LUNA}Luna's short memory loaded.{COLOR_RESET}")

    print()

    print(f"Loading custom knowledge from {COLOR_USER}'{KNOWLEDGE_FILE}'{COLOR_RESET}...")
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as kf:
            MEMORY["knowledge"] = kf.read()
        print(f"{COLOR_LUNA}Custom knowledge loaded.{COLOR_RESET}")
    except FileNotFoundError:
        print(f"{COLOR_YELLOW}No custom knowledge loaded. Skipping...{COLOR_RESET}")

    print()

    print("Validating TTS...")
    validate_tts_paths()
    print()

    print(f"Using AI model: {COLOR_PURPLE}{MODEL_NAME}{COLOR_RESET}")
    print(f"Filter: {COLOR_BLUE}built-in{COLOR_RESET}")
    print()
    print(f"TTS: {COLOR_LUNA}Enabled{COLOR_RESET}" if TTS_ENABLED == True else f"TTS: {COLOR_RED}Disabled{COLOR_RESET}")
    print(f"TTS speed: {TTS_SPEED}")
    print(f"TTS voice: {COLOR_PURPLE}{TTS_VOICE}{COLOR_RESET}")
    print()
    print(f"Commands: '{COLOR_USER}exit{COLOR_RESET}' or '{COLOR_USER}quit{COLOR_RESET}' to end the conversation, '{COLOR_USER}tts on{COLOR_RESET}' or '{COLOR_USER}tts off{COLOR_RESET}' to control voice output.")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-tts", action="store_true", help="Disable TTS")
    parser.add_argument("--model", type=str, default=MODEL_NAME, help="Model name")
    return parser.parse_args()


def save_memory():
    """Save current memory to file"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(MEMORY, f, indent=2)


def update_long_memory():
    if len(MEMORY["conversation_history"]) > 10:
        summary = summarize_conversation(MEMORY["conversation_history"])
        with open(LONG_MEMORY_FILE, "w") as f:
            json.dump({"summary": summary}, f)


def extract_user_info(user_input):
    lower = user_input.lower().strip()

    if match := re.search(r"my name is ([\w\s]+)", lower):
        name = match.group(1).strip().split('.')[0].capitalize()
        MEMORY["user_info"]["name"] = name
        MEMORY["luna_notes"].append(f"User's name is {name}. Annoying, but easy to remember.")

    elif match := re.search(r"i (?:like|love) ([\w\s]+)", lower):
        like = match.group(1).strip().split('.')[0]
        MEMORY["user_info"]["likes"] = like
        MEMORY["luna_notes"].append(f"User {'loves' if 'love' in match.group(0) else 'likes'} {like}. How original.")


def log_request_response(prompt, response):
    timestamp = datetime.now()
    date_str = timestamp.strftime("%d-%m-%Y")
    log_file = f"logs/{date_str}.log"

    os.makedirs("logs", exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp.strftime('%H:%M:%S')}]\n{prompt}\n\n{response}\n---\n\n")


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


def remove_repeated_start(reply, threshold=0.7):
    lines = reply.strip().split('\n')
    if not lines:
        return reply

    first_line = lines[0].strip()
    for msg in MEMORY["conversation_history"]:
        if msg.startswith("Luna:"):
            old_reply = msg[len("Luna: "):].strip().split('\n')[0]
            if SequenceMatcher(None, first_line, old_reply).ratio() > threshold:
                return '\n'.join(lines[1:]) or "(Hmm...)"
    return reply


def clean_response(text):
    """Remove unwanted formatting tags like <response>, </response>, etc."""
    # Remove <response>...</response> blocks
    text = re.sub(r"</?response[^>]*>", "", text, flags=re.IGNORECASE)
    # Remove extra whitespace and newlines
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return text.strip()


def speak_text(text, speed=TTS_SPEED):
    """
    Speak text using Piper TTS with adjustable speed
    speed = 1.0 → normal
    speed > 1.0 → faster (e.g., 1.3 = 30% faster)
    speed < 1.0 → slower
    """
    if not TTS_ENABLED:
        return

    print(f"{COLOR_LUNA}Luna (speaking){COLOR_RESET}: ...")

    length_scale = 1.0 / speed

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
            print(f"{COLOR_RED}TTS Error: {COLOR_RESET}{result.stderr.decode('utf-8')}")
            return

        # Play audio
        if os.name == 'nt':  # Windows
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{os.path.abspath(AUDIO_OUTPUT_FILE)}').PlaySync();"], shell=True)
        elif os.path.exists("/usr/bin/afplay"):  # macOS
            subprocess.run(["afplay", AUDIO_OUTPUT_FILE])
        elif os.path.exists("/usr/bin/aplay"):  # Linux
            subprocess.run(["aplay", AUDIO_OUTPUT_FILE])
        else:
            print(f"{COLOR_YELLOW}No audio player found. Skipping playback.{COLOR_RESET}")

    except Exception as e:
        print(f"{COLOR_RED}Error during TTS:\n{COLOR_RESET}{str(e)}")


def luna_response(user_input):
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
        match = re.search(r"(?:pun|joke)\s+(?:about|on|for)\s+([^\.\!\?]+)", lower_input)
        topic = match.group(1).strip() if match else "something"
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

<knowledge>
{knowledge_str}
</knowledge>

<user_info>
{user_info_str}
</user_info>

<notes>
{luna_notes_str}
</notes>

<history>
{history_str}
</history>

Respond to the latest message.
"""

    full_prompt_for_log = full_prompt

    for attempt in range(3):
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": MODEL_NAME,
                    "prompt": full_prompt,
                    "stream": AI_STREAM
                }
            )

            ai_reply = response.json().get("response", "No response")
            ai_reply = clean_response(ai_reply)
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
        else:
            print(f"{COLOR_RED}Sorry, I couldn't connect to the AI. Is Ollama running?{COLOR_RESET}")
            return "Someone tell Andrew there is a problem with my AI."


def main():
    args = parse_args()
    if args.no_tts:
        TTS_ENABLED = False

    startup()

    while True:
        user = input(f"{COLOR_USER}You: {COLOR_RESET}")
        """
        if user.lower() == "help":
            return (
                "Available commands:\n" 
                "  - exit / quit: End chat\n"
                "  - tts on / off: Toggle voice\n"
                "  - pun about X: Get a pun\n"
                "  - limerick about X: Get a limerick\n"
                "  - help: Show this message"
            )
        """
        if user.lower() in ["exit", "quit"]:
            print(f"{COLOR_YELLOW}Stopping...{COLOR_RESET}")
            save_memory()
            break
        reply = luna_response(user)
        print(f"{COLOR_LUNA}Luna: {reply}{COLOR_RESET}")

        speak_text(reply)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLOR_RED}EXIT\nKeyboardInterrupt{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}STOPPED{COLOR_RESET}")
