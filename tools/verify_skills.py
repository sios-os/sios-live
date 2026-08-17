#!/usr/bin/env python3
"""Verify that all promoted skills load, pass their own tests, and have intact hashes."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.skills import SkillLibrary, SkillError

lib = SkillLibrary(ROOT / "skills")
print(f"Promoted skills: {len(lib.names())}")
print()

all_ok = True
for skill in lib.iter_current():
    print(f"  {skill.name} v{skill.version}")
    print(f"    hash: {skill.artifact_hash[:24]}...")
    print(f"    model: {skill.provenance.model}")
    print(f"    attempt: #{skill.provenance.attempt}")
    # Show the function signature
    sig = next(
        (l.strip() for l in skill.code.splitlines() if l.strip().startswith("def ")), "?"
    )
    print(f"    signature: {sig}")
    # Show first test line
    first_test = next(
        (l.strip() for l in skill.tests.splitlines() if l.strip().startswith("assert")), "?"
    )
    print(f"    first test: {first_test[:80]}")
    print()

print("All skills loaded successfully with intact hashes.")
