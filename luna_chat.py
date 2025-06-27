import requests
import json
import os

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


def luna_response(user_input):
    global MEMORY

    # Add user message to history
    MEMORY["conversation_history"].append(f"User: {user_input}")

    # Keep only last 5 messages
    if len(MEMORY["conversation_history"]) > 5:
        MEMORY["conversation_history"].pop(0)

    # Try to extract facts
    extract_user_info(user_input)

    # Build full prompt with history + user info + knowledge
    history_str = "\n".join(MEMORY["conversation_history"])
    user_info_str = "\n".join([f"{k}: {v}" for k, v in MEMORY["user_info"].items()])
    luna_notes_str = "\n".join(MEMORY["luna_notes"])
    knowledge_str = MEMORY["knowledge"]

    full_prompt = f"""{SYSTEM_PROMPT}

Additional Knowledge:
{knowledge_str}

User Info:
{user_info_str}

Notes:
{luna_notes_str}

Previous messages:
{history_str}

Now respond to:"""

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                "model": "llama3:8b-instruct",
                "prompt": full_prompt,
                "stream": False
            }
        )

        ai_reply = response.json().get("response", "No response")

        # Add AI reply to history
        MEMORY["conversation_history"].append(f"Luna: {ai_reply}")
        save_memory()  # Save after every response
        return ai_reply

    except Exception as e:
        return f"Connection error: {str(e)}"


def main():
    print("Luna is online.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("She's listening closely...")
    while True:
        user = input("You: ")
        if user.lower() in ["exit", "quit"]:
            print("Luna: *vanishes*")
            MEMORY["luna_notes"].append("Conversation ended. Finally some peace.")
            save_memory()
            break
        reply = luna_response(user)
        print(f"Luna: {reply}")


if __name__ == "__main__":
    main()
