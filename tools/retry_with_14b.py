#!/usr/bin/env python3
"""Retry failed skills with the 14b model."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.loop import SelfDevelopmentLoop
from anubis.model import OllamaAdapter
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.sandbox import Sandbox, SandboxPolicy

ROOT = Path(".")
model = OllamaAdapter("qwen2.5-coder:14b", require_tools=False)
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
sandbox = Sandbox(SandboxPolicy(timeout_s=60, memory_mb=1024, cpu_seconds=30))
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=3)

FAILED = [
    ("date_to_day_of_year", "Write a function that converts a date (year, month, day) to the day of the year (1-366)"),
    ("day_of_year_to_date", "Write a function that converts a day of the year (1-366) and a year back to a date (year, month, day)"),
    ("weekday", "Write a function that returns the day of the week (0=Sunday) for a given year, month, and day using Zeller's congruence"),
    ("parse_bytes", "Write a function that parses a human-readable byte string like '1.5KB' or '2.3 MB' into a byte count integer"),
    ("distance_convert", "Write a function that converts between meters, kilometers, miles, and feet given a value, from_unit, and to_unit"),
    ("weight_convert", "Write a function that converts between kilograms, grams, pounds, and ounces given a value, from_unit, and to_unit"),
    ("repeat_string", "Write a function that repeats a string n times with a separator between each repetition"),
    ("pad_string", "Write a function that pads a string to a given length with a specified character, on the left or right side"),
    ("replace_all", "Write a function that replaces all occurrences of a substring with another in a string"),
    ("split_by_delimiter", "Write a function that splits a string by a delimiter and returns a list of parts"),
    ("mode_list", "Write a function that returns the most common value in a list of numbers. If there are ties, return all modes."),
    ("percentile", "Write a function that calculates the nth percentile of a list of numbers using linear interpolation"),
    ("quartiles", "Write a function that returns Q1, Q2 (median), and Q3 of a list of numbers"),
    ("spaces_to_tab", "Write a function that converts leading spaces to tabs given a tab width"),
    ("wrap_text", "Write a function that wraps text to a given line width, breaking at word boundaries and returning a list of lines"),
    ("validate_url", "Write a function that validates whether a string is a valid HTTP or HTTPS URL using urllib.parse"),
    ("leet_speak", "Write a function that converts text to leet speak (a->4, e->3, i->1, o->0, s->5, t->7)"),
    ("word_wrap", "Write a function that wraps a string to a given width, returning a list of lines, breaking at word boundaries"),
]

existing = set(library.names())
to_retry = [(n, t) for n, t in FAILED if n not in existing]
print(f"Current skills: {len(existing)}")
print(f"Skills to retry: {len(to_retry)}")
print(f"Model: qwen2.5-coder:14b")
print()

promoted = 0
failed = 0
for name, task in to_retry:
    print(f"  {name}...", end=" ", flush=True)
    result = loop.run_mission(task, name)
    if result.success:
        promoted += 1
        print(f"PROMOTED (v{result.skill.version})")
    else:
        failed += 1
        print(f"FAILED ({result.denied_reason or 'unknown'})")

print()
print(f"=== SUMMARY ===")
print(f"  Promoted: {promoted}")
print(f"  Failed: {failed}")
print(f"  Total skills: {len(library.names())}")
