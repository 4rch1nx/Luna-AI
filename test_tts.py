# luna_vtuber.py
import requests
import subprocess
import os

# Step 1: Ask Ollama for response (non-streaming)
def get_ai_response(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Step 2: Use Piper to speak the text
def speak_text(text):
    # Save speech to audio file
    with open("output.wav", "wb") as f:
        subprocess.run(
            ["piper", "--model", "en_US-amy-medium"],
            input=text.encode(),
            stdout=f
        )
    
    # Play audio (VTube Studio will detect it)
    print("🎤 Playing audio...")
    subprocess.run(["afplay", "output.wav"])  # macOS
    # On Linux: ["aplay", "output.wav"]
    # On Windows: ["powershell", "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).SpeakFile('output.wav')"]

# Step 3: Main loop
if __name__ == "__main__":
    print("🎙️ Luna AI VTuber is ready! Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        # Get AI response
        ai_text = get_ai_response(f"Respond naturally as a friendly AI named Luna: {user_input}")
        print("Luna:", ai_text)

        # Speak it → triggers VTube Studio lip sync
        speak_text(ai_text)
