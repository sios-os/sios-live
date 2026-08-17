#!/usr/bin/env python3
"""ANUBIS's first real self-development missions.

Live inference. Each mission has ANUBIS author a capability for himself, run it
under containment, verify it against its own tests, and -- only on passing
evidence -- promote it into his permanent skill library.
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
    print(f"{GOLD}  S I O S{OFF}  ::  {BLUE}ANUBIS self-development{OFF}")
    print(f"{DIM}  the model proposes; the Constitution decides{OFF}")
    rule()


MISSIONS = [
    (
        "reverse_string",
        "Reverse a string. The function must accept str and return the "
        "reversed string. Handle empty string and unicode characters.",
    ),
    (
        "count_vowels",
        "Count the number of vowels (a, e, i, o, u) in a string. Case "
        "insensitive. Return an integer count.",
    ),
    (
        "dedupe_preserving_order",
        "Remove duplicates from a list while preserving the order of first "
        "appearance. Must handle unhashable elements by falling back to a "
        "slower comparison.",
    ),
    (
        "parse_duration",
        "Parse a duration string like '2h30m', '45s', or '1h' into an integer "
        "number of seconds. Support h, m, and s units in any combination. "
        "Raise ValueError on invalid input.",
    ),
]


def main() -> int:
    banner()

    model_name = "llama3.1:8b"
    adapter = OllamaAdapter(model_name, require_tools=True)
    try:
        health = adapter.health()
    except Exception as exc:  # noqa: BLE001
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
            # Show what it learned from, when it had to retry.
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
    print(f"  {DIM}(this is the corpus for weight training after the GPU upgrade){OFF}")
    rule()

    return 0 if promoted else 1


if __name__ == "__main__":
    sys.exit(main())
