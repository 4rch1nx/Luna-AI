import os

# Terminal color codes
COLOR_USER = "\033[96m"     # Cyan
COLOR_LUNA = "\033[92m"     # Green
COLOR_RED = "\033[31m"      # Red
COLOR_BLUE = "\033[34m"
COLOR_YELLOW = "\033[33m"
COLOR_PURPLE = "\033[35m"

COLOR_RESET = "\033[0m"     # Reset

# Model name (update this if you switch models)
MODEL_NAME = "llama3:8b"
AI_STREAM = False
LUNA_PROMPT_FILE = "luna_prompt.txt"

# Memory file path
MEMORY_FILE = "memory.json"
LONG_MEMORY_FILE = "long_memory.json"

# Load knowledge file (from PDF or TXT)
KNOWLEDGE_FILE = "user_knowledge.txt"


# TTS_Settings
TTS_ENABLED = True
TTS_SPEED = 1.3
TTS_VOICE = "Amy" # Amy, voice2, voice3
MODELS_PATHS = {
    "Amy": "tts/piper/models/en_US-amy-medium.onnx",
    "voice2": "tts/piper/models/voice2.onnx",
    "voice3": "tts/custom/Alina/file"
}
CONFIG_PATHS = {
    "Amy": "tts/piper/models/en_US-amy-medium.onnx.json",
    "voice2": "tts/piper/models/voice2.onnx.json",
    "voice3": "tts/custom/Alina/file"
}

PIPER_MODEL_PATH = MODELS_PATHS[TTS_VOICE]
PIPER_CONFIG_PATH = CONFIG_PATHS[TTS_VOICE]
AUDIO_OUTPUT_FILE = "output.wav"


def validate_tts_paths():
    if not os.path.exists(PIPER_MODEL_PATH):
        print(f"{COLOR_RED}TTS model not found: {PIPER_MODEL_PATH}{COLOR_RESET}")
        return False
    if not os.path.exists(PIPER_CONFIG_PATH):
        print(f"{COLOR_RED}TTS config not found: {PIPER_CONFIG_PATH}{COLOR_RESET}")
        return False
    print(f"{COLOR_LUNA}TTS validation complete.{COLOR_RESET}")
    return True
