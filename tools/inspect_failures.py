#!/usr/bin/env python3
"""Inspect failed attempts in the evidence ledger to understand model failures."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "evidence" / "ledger.jsonl"

with LEDGER.open() as f:
    for line in f:
        e = json.loads(line)
        if e["action"] == "attempt.executed" and not e["payload"].get("passed"):
            p = e["payload"]
            print(f"--- {p['skill']} attempt {p['attempt']} ---")
            print("CODE:")
            print(p["code"][:600])
            print("TESTS:")
            print(p["tests"][:400])
            print("STDOUT:", repr(p["stdout"][:200]))
            print("STDERR:", repr(p["stderr"][:300]))
            print()
