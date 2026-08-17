#!/usr/bin/env python3
"""Test Ollama embeddings endpoint."""
import json
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:11434/api/embeddings",
    data=json.dumps({"model": "nomic-embed-text", "prompt": "test embedding"}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read())
emb = data.get("embedding", [])
print(f"Embedding dim: {len(emb)}")
print(f"First 5: {emb[:5]}")
