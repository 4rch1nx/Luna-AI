# test_tts.py
import requests
import subprocess
import os

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

def speak_text(text, speed=1.0):
    """
    Speak text with adjustable speed
    speed = 1.0 → normal
    speed > 1.0 → slower (e.g., 1.3 = 30% slower)
    speed < 1.0 → faster (e.g., 0.8 = 20% faster)
    """
    print(f"🔊 Luna speaking ({'faster' if speed < 1 else 'slower' if speed > 1 else 'normally'})...")

    model_path = "tts/piper/models/en_US-amy-medium.onnx"
    config_path = "tts/piper/models/en_US-amy-medium.onnx.json"

    length_scale = 1.0 / speed

    with open("output.wav", "wb") as wav_file:
        result = subprocess.run(
            [
                "piper",
                "--model", model_path,
                "--config", config_path,
                "--output_file", "-",
                "--length-scale", str(length_scale)   # ← Control speed here!
            ],
            input=text.encode(),
            stdout=wav_file,
            stderr=subprocess.PIPE
        )

    if result.returncode != 0:
        print("❌ Piper error:", result.stderr.decode())
        return

    print("🎤 Playing audio...")
    subprocess.run(["afplay", "output.wav"])

if __name__ == "__main__":
    print("🎙️ Luna AI VTuber is ready! Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        ai_text = get_ai_response(f"Respond naturally as a friendly AI named Luna: {user_input}")
        print("Luna:", ai_text)

        speak_text(ai_text, speed=1.3)
