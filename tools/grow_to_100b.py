#!/usr/bin/env python3
"""Grow to 100 skills."""
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

EXTRA = [
    ("reverse_words", "Write a function that reverses the order of words in a sentence"),
    ("count_lines", "Write a function that counts the number of lines in a string"),
    ("tab_to_spaces", "Write a function that converts tabs to spaces in a string given a tab width"),
    ("spaces_to_tab", "Write a function that converts leading spaces to tabs given a tab width"),
    ("truncate_string", "Write a function that truncates a string to a max length and appends an ellipsis if truncated"),
    ("wrap_text", "Write a function that wraps text to a given line width, breaking at word boundaries"),
    ("is_anagram", "Write a function that checks if two strings are anagrams of each other"),
    ("is_palindrome_str", "Write a function that checks if a string is a palindrome, ignoring spaces and case"),
    ("count_words_in_string", "Write a function that counts the number of words in a string"),
    ("extract_numbers", "Write a function that extracts all numbers from a string and returns them as a list of floats"),
    ("validate_ip_address", "Write a function that validates whether a string is a valid IPv4 address"),
    ("validate_email", "Write a function that validates whether a string is a valid email address"),
    ("validate_url", "Write a function that validates whether a string is a valid HTTP or HTTPS URL"),
    ("generate_password", "Write a function that generates a random password of a given length with optional special characters"),
    ("shuffle_string", "Write a function that shuffles the characters of a string randomly"),
]

existing = set(library.names())
new = [(n, t) for n, t in EXTRA if n not in existing]
print(f"Current: {len(existing)}, New missions: {len(new)}")

promoted = 0
for name, task in new:
    print(f"  {name}...", end=" ", flush=True)
    result = loop.run_mission(task, name)
    if result.success:
        promoted += 1
        print(f"PROMOTED (v{result.skill.version})")
    else:
        print(f"FAILED")

print(f"\nPromoted: {promoted}, Total skills: {len(library.names())}")
