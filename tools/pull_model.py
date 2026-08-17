#!/usr/bin/env python3
"""Pull a model from Ollama."""
import json, sys, urllib.request

OLLAMA = "http://127.0.0.1:11434"
model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:14b"

print(f"Pulling {model}...")
payload = json.dumps({"name": model, "stream": False}).encode()
req = urllib.request.Request(
    f"{OLLAMA}/api/pull",
    data=payload,
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    print(f"Status: {data.get('status', '?')}")
except Exception as exc:
    print(f"Error: {exc}")
