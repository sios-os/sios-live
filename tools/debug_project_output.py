#!/usr/bin/env python3
"""Capture raw model output from the project mission loop."""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.loop import PROJECT_PROMPT
from anubis.skills import parse_project_proposal

OLLAMA = "http://127.0.0.1:11434"

task = "Build a CSV utilities module with two files: main.py with a function `parse_csv_line(line, delimiter=',')` that splits a CSV line handling quoted fields, and helpers.py with a function `strip_quotes(field)` that removes surrounding quotes from a field. The main module should import strip_quotes from helpers."
skill_name = "parse_csv_line"

user_prompt = f"""Capability to build: {task}
Name the primary function: {skill_name}

Skills you have already promoted (build on these, do not duplicate them):
- reverse_string v1: def reverse_string(s)
- count_vowels v1: def count_vowels(s)
- slugify v1: def slugify(s)
- word_frequency v1: def word_frequency(text)
- chunk_list v1: def chunk_list(lst, size)"""

payload = json.dumps({
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "system", "content": PROJECT_PROMPT},
        {"role": "user", "content": user_prompt},
    ],
    "stream": False,
    "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 2000},
}).encode()

req = urllib.request.Request(
    f"{OLLAMA}/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
)

print("Sending request...")
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    data = json.loads(resp.read())
elapsed = time.time() - t0

msg = data.get("message", {})
content = msg.get("content", "")
print(f"Elapsed: {elapsed:.1f}s  Tokens: {data.get('eval_count', 0)}")
print(f"Content length: {len(content)} chars")
print("\n=== RAW OUTPUT START ===")
print(content)
print("=== RAW OUTPUT END ===")

# Try parsing
print("\n=== PARSING ATTEMPT ===")
try:
    code, tests, files = parse_project_proposal(content)
    print(f"SUCCESS: code={len(code)}c tests={len(tests)}c files={list(files.keys())}")
except Exception as e:
    print(f"FAILED: {e}")

# Show what markers are present
print("\n=== MARKER CHECK ===")
print(f"<<<FILE: present: {'<<<FILE:' in content}")
print(f"<<<TESTS>>> present: {'<<<TESTS>>>' in content}")
print(f"<<<SKILL>>> present: {'<<<SKILL>>>' in content}")
print(f"```python blocks: {content.count('```python')}")
print(f"``` blocks: {content.count('```')}")
