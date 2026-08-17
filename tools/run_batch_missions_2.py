#!/usr/bin/env python3
"""Run 20 more self-dev missions to grow the skill library to 40+."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.loop import SelfDevelopmentLoop
from anubis.model import OllamaAdapter
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.sandbox import Sandbox, SandboxPolicy

ROOT = Path(".")
model = OllamaAdapter("qwen2.5-coder:7b", require_tools=False)
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
sandbox = Sandbox(SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20))
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=3)

MISSIONS = [
    ("is_anagram", "Write a function that checks if two strings are anagrams of each other"),
    ("binary_search", "Write a function that performs binary search on a sorted list and returns the index or -1"),
    ("bubble_sort", "Write a function that sorts a list using bubble sort"),
    ("quick_sort", "Write a function that sorts a list using quicksort"),
    ("merge_sort", "Write a function that sorts a list using merge sort"),
    ("string_compress", "Write a function that performs basic string compression (aabbbcccc -> a2b3c4)"),
    ("matrix_transpose", "Write a function that transposes a 2D matrix"),
    ("caesar_cipher", "Write a function that encodes a string using a Caesar cipher with a given shift"),
    ("rot13", "Write a function that applies ROT13 encoding to a string"),
    ("validate_email", "Write a function that validates an email address format without using regex"),
    ("ip_to_int", "Write a function that converts an IPv4 address string to an integer"),
    ("int_to_ip", "Write a function that converts an integer to an IPv4 address string"),
    ("hex_to_rgb", "Write a function that converts a hex color string to an RGB tuple"),
    ("rgb_to_hex", "Write a function that converts RGB values to a hex color string"),
    ("leet_speak", "Write a function that converts text to leet speak (a->4, e->3, i->1, o->0, s->5, t->7)"),
    ("word_wrap", "Write a function that wraps text to a given line width, breaking at word boundaries"),
    ("truncate", "Write a function that truncates text to a max length, adding an ellipsis if cut"),
    ("pluralize", "Write a function that returns the English plural of a noun"),
    ("ordinal", "Write a function that converts a number to its ordinal string (1st, 2nd, 3rd, 4th)"),
    ("roman_to_int", "Write a function that converts a Roman numeral string to an integer"),
]

existing = set(library.names())
print(f"Starting skill library: {len(existing)} skills")
print()

results = []
for skill_name, task in MISSIONS:
    if skill_name in existing:
        print(f"SKIP {skill_name} (already in library)")
        results.append((skill_name, "skipped", 0))
        continue
    print(f"=== MISSION: {skill_name} ===")
    result = loop.run_mission(task, skill_name)
    status = "PROMOTED" if result.success else "FAILED"
    attempts = len(result.attempts)
    print(f"  {status} attempts={attempts}")
    if result.success:
        print(f"  -> {skill_name} added to library")
    else:
        last = result.attempts[-1] if result.attempts else None
        if last and last.sandbox:
            print(f"  last stderr: {last.sandbox.stderr[:120]}")
    results.append((skill_name, status.lower(), attempts))
    print()

print("=== BATCH SUMMARY ===")
promoted = sum(1 for _, s, _ in results if s == "promoted")
failed = sum(1 for _, s, _ in results if s == "failed")
skipped = sum(1 for _, s, _ in results if s == "skipped")
print(f"  Promoted: {promoted}")
print(f"  Failed:   {failed}")
print(f"  Skipped:  {skipped}")
print()
for name, status, attempts in results:
    print(f"  {name:20s} {status:10s} ({attempts} attempts)")
print()
print(f"Total skills in library: {len(library.names())}")
