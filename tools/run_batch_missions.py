#!/usr/bin/env python3
"""Run multiple self-dev missions to grow the skill library."""
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
    ("is_palindrome", "Write a function that checks if a string is a palindrome"),
    ("factorial", "Write a function that computes the factorial of a non-negative integer"),
    ("fibonacci", "Write a function that returns the nth Fibonacci number"),
    ("is_prime", "Write a function that checks if a number is prime"),
    ("gcd", "Write a function that computes the greatest common divisor of two numbers"),
    ("reverse_words", "Write a function that reverses the order of words in a sentence"),
    ("count_words", "Write a function that counts the number of words in a string"),
    ("title_case", "Write a function that converts a string to title case"),
    ("flatten_list", "Write a function that flattens a nested list of arbitrary depth"),
    ("merge_sorted", "Write a function that merges two sorted lists into one sorted list"),
]

existing = set(library.names())
print(f"Starting skill library: {len(existing)} skills")
print(f"Existing: {sorted(existing)}")
print()

results = []
for skill_name, task in MISSIONS:
    if skill_name in existing:
        print(f"SKIP {skill_name} (already in library)")
        results.append((skill_name, "skipped", 0))
        continue
    print(f"=== MISSION: {skill_name} ===")
    print(f"  Task: {task}")
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
print(f"Skills: {sorted(library.names())}")
