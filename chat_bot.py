import requests
import time
import json

AI_MODEL = "llama3.1"

def ask_chat(history):
    # Style the system prompt
    system_prompt = ""

    # Build the conversation string
    conversation = "\n".join([
        f"{role}: {msg.strip()}" for role, msg in history
    ])
    prompt = f"{system_prompt}\n\n{conversation}\nAI:"

    with requests.post("http://localhost:11434/api/generate", json={
        "model": AI_MODEL,
        "prompt": prompt,
        "stream": True
    }, stream=True) as res:
        if res.status_code != 200:
            yield f"[Error: {res.status_code}]"
            return
        for line in res.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        yield data["response"]
                        time.sleep(0.01)
                    elif "error" in data:
                        yield f"[Error: {data['error']}]"
                        break
                except Exception as e:
                    yield f"[Parse error: {e}]"
                    break
