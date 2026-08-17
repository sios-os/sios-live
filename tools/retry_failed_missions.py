#!/usr/bin/env python3
"""Retry failed missions with simpler descriptions."""
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
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=5)

RETRIES = [
    ("int_to_ip", "Write a function int_to_ip(n) that converts an integer to an IPv4 address string. Example: 167772161 -> '10.0.0.1'. Extract each octet by shifting and masking."),
    ("leet_speak", "Write a function leet_speak(text) that replaces a->4, e->3, i->1, o->0, s->5, t->7 in a string. Case insensitive input, return the converted string."),
    ("word_wrap", "Write a function word_wrap(text, width) that wraps text into lines of at most width characters, breaking at spaces. Return a list of strings, one per line."),
    ("pluralize", "Write a function pluralize(word) that returns the plural of an English noun. Handle: words ending in s/x/z/ch/sh add 'es', words ending in consonant+y change y to ies, others add 's'."),
    ("ordinal", "Write a function ordinal(n) that converts a number to its ordinal string. 1->'1st', 2->'2nd', 3->'3rd', 4->'4th', 11->'11th', 21->'21st'."),
]

existing = set(library.names())
print(f"Starting: {len(existing)} skills")
print()

for skill_name, task in RETRIES:
    if skill_name in existing:
        print(f"SKIP {skill_name} (already in library)")
        continue
    print(f"=== RETRY: {skill_name} ===")
    result = loop.run_mission(task, skill_name)
    status = "PROMOTED" if result.success else "FAILED"
    print(f"  {status} attempts={len(result.attempts)}")
    if not result.success:
        last = result.attempts[-1] if result.attempts else None
        if last and last.sandbox:
            print(f"  last stderr: {last.sandbox.stderr[:150]}")
    print()

print(f"Total skills: {len(library.names())}")
print(f"Skills: {sorted(library.names())}")
