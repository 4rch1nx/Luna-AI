# vtube-test.py (streaming)
import requests
import json

text = ""
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3:8b",
        "prompt": "Hello, how are you?",
        "stream": True  # ← now we accept streaming
    },
    stream=True  # ← allows reading line-by-line
)

for line in response.iter_lines():
    if line:
        try:
            body = json.loads(line)
            if "response" in body:
                text += body["response"]  # accumulate tokens
            if body.get("done"):
                break
        except json.JSONDecodeError:
            print("Failed to parse line:", line)

print("\nFinal AI Response:", text)
