import requests
import time

# === Get list of models from Ollama ===
def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            return [model["name"] for model in response.json().get("models", [])]
        else:
            print("Failed to fetch model list.")
            return []
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return []

# === Run benchmark on selected model ===
def benchmark_model(model_name, prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    print(f"\nRunning benchmark on '{model_name}'...")
    start_time = time.time()
    response = requests.post(url, json=data)
    end_time = time.time()

    if response.status_code != 200:
        print("Error:", response.text)
        return

    result = response.json()
    tokens = result.get("eval_count", 0)
    duration = end_time - start_time
    tokens_per_second = tokens / duration if duration > 0 else 0

    print("\n--- Results ---")
    print("Response:\n", result.get("response", "").strip())
    print("\nMetrics:")
    print(f"Tokens generated: {tokens}")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Tokens per second: {tokens_per_second:.2f}")

# === Main interactive menu ===
def main():
    print("🔍 Benchmark Ollama Models - Tokens/sec Test\n")

    models = get_ollama_models()
    if not models:
        print("No models found. Please pull at least one model using 'ollama pull <model>'.")
        return

    print("Available Models:")
    for i, model in enumerate(models):
        print(f"{i + 1}. {model}")

    choice = int(input("\nEnter the number of the model you want to test: ")) - 1
    if choice < 0 or choice >= len(models):
        print("Invalid selection.")
        return

    selected_model = models[choice]

    prompt = input("\nEnter your prompt: ")

    benchmark_model(selected_model, prompt)

# === Run the app ===
if __name__ == "__main__":
    main()
