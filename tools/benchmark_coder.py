#!/usr/bin/env python3
"""Benchmark qwen2.5-coder:14b vs llama3.1:8b for coding tasks."""
import json, sys, time, urllib.request

OLLAMA = "http://127.0.0.1:11434"

def generate(model, prompt, timeout=120):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 8192},
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
        load_time = data.get("load_duration", 0) / 1e9
        prompt_tokens = data.get("prompt_eval_count", 0)
        return {
            "model": model,
            "elapsed": round(elapsed, 1),
            "tokens": tokens,
            "tokens_per_sec": round(tps, 1),
            "load_time": round(load_time, 1),
            "response": text,
        }
    except Exception as exc:
        elapsed = time.time() - start
        return {"model": model, "error": str(exc), "elapsed": round(elapsed, 1)}

# A more complex coding task — multi-function with edge cases
COMPLEX_TASK = """Write a Python module with two functions:

1. `merge_sorted_lists(a, b)` - Merge two sorted lists into one sorted list.
2. `group_by_key(items, key_func)` - Group items by a key function, returning a dict.

Include comprehensive tests covering:
- Empty inputs
- Single element
- Duplicate keys
- Mixed types

Format your response as:

### SKILL
```python
def merge_sorted_lists(a, b):
    ...

def group_by_key(items, key_func):
    ...
```

### TESTS
```python
def test_merge_sorted_lists():
    ...

def test_group_by_key():
    ...
```
"""

print("=== qwen2.5-coder:14b ===")
r1 = generate("qwen2.5-coder:14b", COMPLEX_TASK, timeout=120)
if "error" in r1:
    print(f"ERROR: {r1['error']}  ({r1['elapsed']}s)")
else:
    print(f"Time: {r1['elapsed']}s  Tokens: {r1['tokens']}  TPS: {r1['tokens_per_sec']}  Load: {r1['load_time']}s")
    print(f"Response length: {len(r1['response'])} chars")
    print(f"Preview:\n{r1['response'][:500]}")

print("\n=== llama3.1:8b ===")
r2 = generate("llama3.1:8b", COMPLEX_TASK, timeout=120)
if "error" in r2:
    print(f"ERROR: {r2['error']}  ({r2['elapsed']}s)")
else:
    print(f"Time: {r2['elapsed']}s  Tokens: {r2['tokens']}  TPS: {r2['tokens_per_sec']}  Load: {r2['load_time']}s")
    print(f"Response length: {len(r2['response'])} chars")
    print(f"Preview:\n{r2['response'][:500]}")

print("\n=== Comparison ===")
if "error" not in r1 and "error" not in r2:
    print(f"qwen2.5-coder:14b:  {r1['tokens_per_sec']} tok/s  ({r1['tokens']} tokens in {r1['elapsed']}s)")
    print(f"llama3.1:8b:        {r2['tokens_per_sec']} tok/s  ({r2['tokens']} tokens in {r2['elapsed']}s)")
    ratio = r1['tokens_per_sec'] / r2['tokens_per_sec'] if r2['tokens_per_sec'] > 0 else 0
    print(f"Speed ratio: {ratio:.2f}x")
    print(f"Response length ratio: {len(r1['response']) / max(len(r2['response']), 1):.2f}x")
