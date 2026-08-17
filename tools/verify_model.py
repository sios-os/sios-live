#!/usr/bin/env python3
"""Live verification that the model layer actually works.

Not a unit test -- this hits real inference. Run it whenever the model or the
hardware changes.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.model import (  # noqa: E402
    MODELS,
    OllamaAdapter,
    build_adapter,
    detect_vram_gb,
    select_model,
)


def line(t=""):
    print(t, flush=True)


def main() -> int:
    line("=" * 66)
    line("ANUBIS model layer verification")
    line("=" * 66)

    vram = detect_vram_gb()
    line(f"detected VRAM      : {vram:.1f} GB" if vram else "detected VRAM      : unknown")
    auto = select_model(vram)
    line(f"auto-selected      : {auto}")
    line(f"  -> {MODELS[auto].note}")
    line("")

    line("registered models:")
    for name, s in MODELS.items():
        fits = "fits" if vram and s.min_vram_gb <= vram else "too big"
        flags = ",".join(
            f for f, on in (("tools", s.tools), ("think", s.thinking), ("vision", s.vision)) if on
        ) or "none"
        line(f"  {name:<18} {s.params:<8} vram>={s.min_vram_gb:>4.1f}GB  [{flags}]  {fits}")
    line("")

    # Force llama3.1:8b -- the user's stated choice and the 6 GB primary.
    adapter = OllamaAdapter("llama3.1:8b", require_tools=True)

    line("--- health ---")
    try:
        h = adapter.health()
    except Exception as exc:  # noqa: BLE001
        line(f"FAIL: {exc}")
        return 1
    line(f"ollama {h['version']} @ {h['endpoint']}")
    line(f"model {h['model']} present={h['model_present']}")
    if not h["model_present"]:
        line("FAIL: model not pulled")
        return 1
    line("")

    # --- Test 1: plain generation -----------------------------------------
    line("--- test 1: generation ---")
    c = adapter.generate(
        "Reply with exactly one word: OK",
        system="You follow instructions literally and reply minimally.",
        max_tokens=16,
    )
    line(f"reply     : {c.text!r}")
    line(f"tokens    : {c.prompt_tokens} in / {c.completion_tokens} out")
    line(f"speed     : {c.tokens_per_s:.1f} tok/s  ({c.duration_s:.2f}s)")
    if not c.text:
        line("FAIL: empty response")
        return 1
    line("PASS")
    line("")

    # --- Test 2: tool calling ---------------------------------------------
    # This is the load-bearing capability. If it fails, the loop cannot work.
    line("--- test 2: tool calling ---")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_python_tests",
                "description": "Execute a Python test suite in the sandbox and return results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "Name of the skill whose tests should run.",
                        }
                    },
                    "required": ["skill_name"],
                },
            },
        }
    ]
    c2 = adapter.chat(
        [
            {
                "role": "system",
                "content": "You are ANUBIS. When a tool can accomplish the request, call it.",
            },
            {
                "role": "user",
                "content": "Please run the tests for the skill named 'checksum_file'.",
            },
        ],
        tools=tools,
        temperature=0.0,
    )
    if not c2.tool_calls:
        line(f"FAIL: no tool call. text={c2.text[:200]!r}")
        return 1
    call = c2.tool_calls[0]
    fn = call.get("function", {})
    line(f"tool      : {fn.get('name')}")
    line(f"arguments : {json.dumps(fn.get('arguments'))}")
    line(f"speed     : {c2.tokens_per_s:.1f} tok/s")
    if fn.get("name") != "run_python_tests":
        line(f"FAIL: wrong tool selected: {fn.get('name')}")
        return 1
    line("PASS")
    line("")

    # --- Test 3: code generation shape ------------------------------------
    line("--- test 3: code generation ---")
    c3 = adapter.generate(
        "Write a Python function `slugify(text: str) -> str` that lowercases text "
        "and replaces any run of non-alphanumeric characters with a single hyphen, "
        "stripping leading/trailing hyphens. Use only the standard library. "
        "Output only the code, no prose, no markdown fences.",
        system="You are a precise Python engineer. Output only valid Python source.",
        temperature=0.1,
        max_tokens=400,
    )
    code = c3.text
    line(f"generated {len(code)} chars, {c3.completion_tokens} tokens "
         f"@ {c3.tokens_per_s:.1f} tok/s")
    # Verify it is syntactically valid Python -- the loop depends on this.
    stripped = code.replace("```python", "").replace("```", "").strip()
    try:
        compile(stripped, "<generated>", "exec")
    except SyntaxError as exc:
        line(f"FAIL: generated code is not valid Python: {exc}")
        line(stripped[:400])
        return 1
    line("generated code compiles")
    line("PASS")
    line("")

    line("=" * 66)
    line("ALL CHECKS PASSED -- model layer ready")
    line("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
