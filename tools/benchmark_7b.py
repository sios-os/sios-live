#!/usr/bin/env python3
"""Benchmark qwen2.5-coder:7b vs llama3.1:8b for coding tasks."""
import json, sys, time, urllib.request

OLLAMA = "http://127.0.0.1:11434"

def generate(model, prompt, timeout=90):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 4096},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        elapsed = time.time() - start
        text = data.get("response", "")
        tokens = data.get("eval_count", 0)
        tps = tokens / elapsed if elapsed > 0 else 0
        return {
            "model": model,
            "elapsed": round(elapsed, 1),
            "tokens": tokens,
            "tps": round(tps, 1),
            "response": text,
        }
    except Exception as exc:
        elapsed = time.time() - start
        return {"model": model, "error": str(exc), "elapsed": round(elapsed, 1)}

TASK = """Write a Python function `merge_sorted_lists(a, b)` that merges two sorted lists. Include tests.

### SKILL
```python
def merge_sorted_lists(a, b):
    ...
```

### TESTS
```python
def test_merge():
    ...
```
"""

print("=== qwen2.5-coder:7b ===")
r1 = generate("qwen2.5-coder:7b", TASK)
if "error" in r1:
    print(f"ERROR: {r1['error']}  ({r1['elapsed']}s)")
else:
    print(f"Time: {r1['elapsed']}s  Tokens: {r1['tokens']}  TPS: {r1['tps']}")
    print(f"Response:\n{r1['response'][:600]}")

print("\n=== llama3.1:8b ===")
r2 = generate("llama3.1:8b", TASK)
if "error" in r2:
    print(f"ERROR: {r2['error']}  ({r2['elapsed']}s)")
else:
    print(f"Time: {r2['elapsed']}s  Tokens: {r2['tokens']}  TPS: {r2['tps']}")
    print(f"Response:\n{r2['response'][:600]}")

if "error" not in r1 and "error" not in r2:
    print(f"\n=== Summary ===")
    print(f"qwen2.5-coder:7b: {r1['tps']} tok/s, {r1['tokens']} tokens")
    print(f"llama3.1:8b:      {r2['tps']} tok/s, {r2['tokens']} tokens")
