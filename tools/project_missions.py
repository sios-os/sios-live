#!/usr/bin/env python3
"""Test multi-file project missions with qwen2.5-coder:7b.

These tasks require multiple files with imports — the kind of software
that doesn't fit in a single function.
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
    print(f"{GOLD}  S I O S{OFF}  ::  {BLUE}ANUBIS multi-file projects{OFF}")
    print(f"{DIM}  the model proposes; the Constitution decides{OFF}")
    rule()


PROJECT_MISSIONS = [
    (
        "csv_parser",
        "Build a CSV parser module with a function `parse_csv_line(line, "
        "delimiter=',')` that splits a CSV line handling quoted fields "
        "containing delimiters, and a helper `strip_quotes(field)` that "
        "removes surrounding quotes. Test with 'a,b,c' and "
        "'\"quoted\",unquoted,\"has,comma\"'.",
    ),
    (
        "text_stats",
        "Build a text statistics module with `text_stats(text)` that "
        "returns a dict with 'words', 'chars', 'lines', and "
        "'avg_word_len' keys. Include helper functions `count_words(text)` "
        "and `count_lines(text)`. Test with 'hello world\\nfoo bar baz'.",
    ),
    (
        "stack_queue",
        "Build a Stack and Queue data structure module. Implement a "
        "`Stack` class with push, pop, peek, and is_empty methods. "
        "Implement a `Queue` class with enqueue, dequeue, front, and "
        "is_empty methods. Test both classes thoroughly.",
    ),
    (
        "json_config",
        "Build a JSON config parser module with `load_config(json_str)` "
        "that parses JSON and returns a dict, `get_value(config, key, "
        "default=None)` that safely gets a nested value using dot notation "
        "(e.g. 'a.b.c'), and `merge_configs(base, override)` that deep-"
        "merges two dicts. Test all three functions.",
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

    for i, (name, task) in enumerate(PROJECT_MISSIONS, 1):
        print(f"{BLUE}[project {i}/{len(PROJECT_MISSIONS)}]{OFF} {GOLD}{name}{OFF}")
        print(f"{DIM}  {task[:120]}...{OFF}")
        print(f"{DIM}  working...{OFF}", flush=True)

        result = runtime.loop.run_project_mission(task, name)

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
            n_files = len(s.files) + 1
            print(f"    {GREEN}PROMOTED{OFF} {s.name} v{s.version} "
                  f"{DIM}{s.artifact_hash[:12]}{OFF}  {result.duration_s:.0f}s  "
                  f"({n_files} files)")
            sig = next(
                (l.strip() for l in s.code.splitlines() if l.strip().startswith("def ")),
                "?",
            )
            print(f"    {DIM}{sig}{OFF}")
            if s.files:
                print(f"    {DIM}extra files: {', '.join(s.files.keys())}{OFF}")
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
    print(f"  promoted     : {len(promoted)}/{len(PROJECT_MISSIONS)}")
    if failed:
        print(f"  not promoted : {', '.join(failed)}")
    print(f"  elapsed      : {elapsed:.0f}s")
    print()

    print(f"{GOLD}Skill library{OFF}")
    rule("-")
    for s in runtime.library.iter_current():
        n_files = len(s.files) + 1
        print(f"  {s.name} v{s.version}  [{n_files}f]  {DIM}{s.description[:48]}{OFF}")
    print()

    print(f"{GOLD}Evidence ledger{OFF}")
    rule("-")
    ok, msg = runtime.ledger.verify()
    print(f"  entries      : {runtime.ledger.length}")
    print(f"  integrity    : {GREEN if ok else RED}{msg}{OFF}")
    rule()

    return 0 if promoted else 1


if __name__ == "__main__":
    sys.exit(main())
