#!/usr/bin/env python3
"""ANUBIS self-development missions with qwen2.5-coder:7b.

Tests the code specialist model on increasingly complex tasks:
  1. Simple function (baseline)
  2. Multi-function module
  3. Function with edge cases
  4. Data structure manipulation
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.loop import AnubisRuntime  # noqa: E402
from anubis.model import OllamaAdapter  # noqa: E402

GOLD = "\033[38;5;179m"
BLUE = "\033[38;5;39m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
OFF = "\033[0m"


def rule(char="=", n=72):
    print(char * n, flush=True)


def banner():
    rule()
    print(f"{GOLD}  S I O S{OFF}  ::  {BLUE}ANUBIS self-development (qwen2.5-coder){OFF}")
    print(f"{DIM}  the model proposes; the Constitution decides{OFF}")
    rule()


MISSIONS = [
    (
        "slugify",
        "Convert a string to a URL-safe slug: lowercase, replace any run of "
        "non-alphanumeric characters with a single hyphen, strip leading and "
        "trailing hyphens. Empty string returns empty string.",
    ),
    (
        "camel_to_snake",
        "Convert a camelCase string to snake_case. Insert underscore before "
        "each uppercase letter and lowercase it. Handle consecutive capitals "
        "(e.g. 'HTMLElement' -> 'html_element'). Empty string returns empty.",
    ),
    (
        "word_frequency",
        "Count word frequencies in a string. Return a dict mapping each "
        "lowercase word to its count. Words are separated by whitespace. "
        "Punctuation attached to words should be stripped. Empty string "
        "returns empty dict.",
    ),
    (
        "chunk_list",
        "Split a list into chunks of a given size. Return a list of lists. "
        "The last chunk may be smaller than size. If size <= 0, raise "
        "ValueError. Empty input list returns empty list.",
    ),
]


def main() -> int:
    banner()

    model_name = "qwen2.5-coder:7b"
    adapter = OllamaAdapter(model_name, require_tools=False)
    try:
        health = adapter.health()
    except Exception as exc:
        print(f"{RED}cannot reach the model: {exc}{OFF}")
        return 1
    if not health["model_present"]:
        print(f"{RED}model {model_name} is not pulled{OFF}")
        return 1

    runtime = AnubisRuntime.create(ROOT, adapter, max_attempts=5)

    print(f"  model    : {model_name}  (ollama {health['version']})")
    print(f"  sandbox  : {runtime.sandbox.isolation.label}")
    print(f"  ledger   : {runtime.ledger.path.relative_to(ROOT)} "
          f"({runtime.ledger.length} existing entries)")
    print(f"  skills   : {len(runtime.library.names())} already promoted")
    rule("-")
    print()

    t0 = time.monotonic()
    promoted, failed = [], []

    for i, (name, task) in enumerate(MISSIONS, 1):
        print(f"{BLUE}[mission {i}/{len(MISSIONS)}]{OFF} {GOLD}{name}{OFF}")
        print(f"{DIM}  {task}{OFF}")
        print(f"{DIM}  working...{OFF}", flush=True)

        result = runtime.loop.run_mission(task, name)

        for a in result.attempts:
            if a.promoted:
                tag = f"{GREEN}promoted{OFF}"
            elif a.parse_error:
                tag = f"{RED}unparseable{OFF}"
            elif a.ruling:
                tag = f"{RED}gate denied{OFF}"
            elif a.passed:
                tag = f"{GREEN}tests passed{OFF}"
            else:
                tag = f"{RED}tests failed{OFF}"
            detail = ""
            if a.sandbox:
                detail = f" {DIM}({a.sandbox.duration_s:.2f}s in sandbox){OFF}"
            print(f"    attempt {a.n}: {tag}{detail}")
            if not a.passed and not a.promoted:
                first = a.failure_text().strip().splitlines()
                if first:
                    snippet = next(
                        (l for l in first if "Error" in l or "assert" in l), first[0]
                    )
                    print(f"      {DIM}-> {snippet.strip()[:100]}{OFF}")

        if result.success:
            s = result.skill
            promoted.append(s)
            print(f"    {GREEN}PROMOTED{OFF} {s.name} v{s.version} "
                  f"{DIM}{s.artifact_hash[:12]}{OFF}  {result.duration_s:.0f}s")
            sig = next(
                (l.strip() for l in s.code.splitlines() if l.strip().startswith("def ")),
                "?",
            )
            print(f"    {DIM}{sig}{OFF}")
        else:
            failed.append(name)
            print(f"    {RED}NOT PROMOTED{OFF}: {result.denied_reason}  "
                  f"{result.duration_s:.0f}s")
        print()

    # ---------------------------------------------------------------- report
    rule()
    print(f"{GOLD}Result{OFF}")
    rule("-")
    elapsed = time.monotonic() - t0
    print(f"  promoted     : {len(promoted)}/{len(MISSIONS)}")
    if failed:
        print(f"  not promoted : {', '.join(failed)}")
    print(f"  elapsed      : {elapsed:.0f}s")
    print()

    print(f"{GOLD}Skill library{OFF}")
    rule("-")
    for s in runtime.library.iter_current():
        print(f"  {s.name} v{s.version}  {DIM}{s.description[:52]}{OFF}")
    print()

    print(f"{GOLD}Evidence ledger{OFF}")
    rule("-")
    ok, msg = runtime.ledger.verify()
    print(f"  entries      : {runtime.ledger.length}")
    print(f"  integrity    : {GREEN if ok else RED}{msg}{OFF}")
    print(f"  head         : {runtime.ledger.head[:24]}...")

    corpus = list(runtime.ledger.training_records())
    print(f"  training set : {len(corpus)} verified-good exemplars")
    rule()

    return 0 if promoted else 1


if __name__ == "__main__":
    sys.exit(main())
