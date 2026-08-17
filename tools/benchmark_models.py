#!/usr/bin/env python3
"""Benchmark qwen3.6 vs llama3.1:8b for a coding task."""
import json, subprocess, sys, time, urllib.request

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
        tps = data.get("eval_count", 0) / elapsed if elapsed > 0 else 0
        return {
            "model": model,
            "elapsed": round(elapsed, 1),
            "tokens": tokens,
            "tokens_per_sec": round(tps, 1),
            "response": text[:500],
        }
    except Exception as exc:
        elapsed = time.time() - start
        return {"model": model, "error": str(exc), "elapsed": round(elapsed, 1)}

CODING_TASK = """Write a Python function called `merge_sorted_lists` that takes two sorted lists and merges them into one sorted list. Include a test function with at least 3 test cases. Format:

### SKILL
```python
def merge_sorted_lists(a, b):
    ...
```

### TESTS
```python
def test_merge_sorted_lists():
    ...
```
"""

print("=== Benchmark: qwen3.6:latest ===")
r1 = generate("qwen3.6:latest", CODING_TASK, timeout=180)
print(f"Time: {r1.get('elapsed', '?')}s  Tokens: {r1.get('tokens', '?')}  TPS: {r1.get('tokens_per_sec', '?')}")
if "error" in r1:
    print(f"ERROR: {r1['error']}")
else:
    print(f"Response preview:\n{r1['response'][:300]}")

print("\n=== Benchmark: llama3.1:8b ===")
r2 = generate("llama3.1:8b", CODING_TASK, timeout=60)
print(f"Time: {r2.get('elapsed', '?')}s  Tokens: {r2.get('tokens', '?')}  TPS: {r2.get('tokens_per_sec', '?')}")
if "error" in r2:
    print(f"ERROR: {r2['error']}")
else:
    print(f"Response preview:\n{r2['response'][:300]}")

print("\n=== Summary ===")
if "error" not in r1 and "error" not in r2:
    print(f"qwen3.6:   {r1['tokens_per_sec']} tok/s  ({r1['elapsed']}s for {r1['tokens']} tokens)")
    print(f"llama3.1:  {r2['tokens_per_sec']} tok/s  ({r2['elapsed']}s for {r2['tokens']} tokens)")
    speedup = r1['tokens_per_sec'] / r2['tokens_per_sec'] if r2['tokens_per_sec'] > 0 else 0
    print(f"Speed ratio: {speedup:.2f}x")
