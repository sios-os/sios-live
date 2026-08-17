#!/usr/bin/env python3
"""See what the model actually outputs for a multi-file task."""
import json, urllib.request

OLLAMA = "http://127.0.0.1:11434"

PROJECT_PROMPT = """\
You are ANUBIS, writing a multi-file Python project. You may write multiple \
files that import from each other.

Constraints:
- Python 3 standard library ONLY.
- No network, subprocess, or file access.

Output EXACTLY this format:

<<<FILE: main.py>>>
```python
def your_function(...):
    ...
```
<<<FILE: helpers.py>>>
```python
def helper_function(...):
    ...
```
<<<TESTS>>>
```python
from main import your_function
from helpers import helper_function

_r = your_function(...)
print("actual: " + str(_r))
assert _r == expected
print("TESTS PASSED")
```
<<<END>>>

Rules:
- The first file (main.py) has the primary function.
- Additional files are optional.
- Tests must import from modules and use plain assert.
- Final line must be: print("TESTS PASSED")
- NEVER guess expected values. Print actual values before asserting.
"""

task = """Build a CSV utilities module with two files: main.py with a function `parse_csv_line(line, delimiter=',')` that splits a CSV line handling quoted fields, and helpers.py with a function `strip_quotes(field)` that removes surrounding quotes from a field. The main module should import strip_quotes from helpers."""

payload = json.dumps({
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "system", "content": PROJECT_PROMPT},
        {"role": "user", "content": f"Capability to build: {task}\nName the primary function: parse_csv_line"},
    ],
    "stream": False,
    "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 2000},
}).encode()

req = urllib.request.Request(
    f"{OLLAMA}/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req, timeout=120) as resp:
    data = json.loads(resp.read())

msg = data.get("message", {})
print("=== RAW MODEL OUTPUT ===")
print(msg.get("content", ""))
print("=== END ===")
print(f"\nTokens: {data.get('eval_count', 0)}  Time: {data.get('total_duration', 0)/1e9:.1f}s")
