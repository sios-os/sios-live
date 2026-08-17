#!/usr/bin/env python3
"""Verify qwen2.5-coder:7b supports tool calling."""
import json, sys, urllib.request

OLLAMA = "http://127.0.0.1:11434"

# Check if the model supports tools
payload = json.dumps({
    "model": "qwen2.5-coder:7b",
    "messages": [
        {"role": "user", "content": "What is 2+2? Use the calculate tool."}
    ],
    "stream": False,
    "tools": [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"]
            }
        }
    }],
    "options": {"temperature": 0, "num_ctx": 2048},
}).encode()

req = urllib.request.Request(
    f"{OLLAMA}/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    msg = data.get("message", {})
    tool_calls = msg.get("tool_calls", [])
    print(f"Model: qwen2.5-coder:7b")
    print(f"Tool calls: {len(tool_calls)}")
    if tool_calls:
        for tc in tool_calls:
            fn = tc.get("function", {})
            print(f"  -> {fn.get('name', '?')}({fn.get('arguments', {})})")
        print("TOOLS: SUPPORTED")
    else:
        print(f"Content: {msg.get('content', '')[:200]}")
        print("TOOLS: NOT DETECTED (model responded with text instead)")
except Exception as exc:
    print(f"ERROR: {exc}")
