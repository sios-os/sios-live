#!/usr/bin/env python3
"""Run a self-development mission to exercise the loop."""
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

task = "Write a function that takes a list of numbers and returns the sum of all even numbers in the list"
skill_name = "sum_even_numbers"

print(f"=== MISSION: {skill_name} ===")
print(f"Task: {task}")
print(f"Model: qwen2.5-coder:7b")
print()

result = loop.run_mission(task, skill_name)

print()
print(f"=== RESULT ===")
print(result.summary())
print()
for i, attempt in enumerate(result.attempts):
    print(f"  Attempt {attempt.n}:")
    print(f"    passed: {attempt.passed}")
    print(f"    ruling: {attempt.ruling[:80] if attempt.ruling else 'none'}")
    if attempt.sandbox:
        print(f"    sandbox ok: {attempt.sandbox.ok}")
        print(f"    exit code: {attempt.sandbox.exit_code}")
        if attempt.sandbox.stdout:
            print(f"    stdout: {attempt.sandbox.stdout[:200]}")
        if attempt.sandbox.stderr:
            print(f"    stderr: {attempt.sandbox.stderr[:200]}")
    print()

print(f"Skills in library: {library.names()}")
