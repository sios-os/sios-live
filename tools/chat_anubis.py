#!/usr/bin/env python3
"""Direct chat test with ANUBIS."""
import json, socket, sys

SOCKET_PATH = "/tmp/anubis.sock"

def chat(message):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    s.send(json.dumps({"cmd": "chat", "message": message}).encode())
    s.settimeout(120)
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    raw = data.decode("utf-8").strip()
    print(f"  [debug] raw response length: {len(raw)}")
    print(f"  [debug] raw response first 200: {raw[:200]}")
    result = json.loads(raw)
    print(f"  [debug] parsed type: {type(result).__name__}")
    return result

print("=== CHAT WITH ANUBIS ===")
print()

# Chat 1
print("Me: Hello ANUBIS, who are you?")
r = chat("Hello ANUBIS, who are you?")
print(f"ANUBIS: {r.get('response', '(empty)')}")
print(f"  model={r.get('model')} tokens={r.get('tokens')} duration={r.get('duration_s')}s")
print(f"  grounded={r.get('knowledge_grounded')} citations={r.get('knowledge_citations')}")
if r.get("error"):
    print(f"  ERROR: {r['error']}")
print()

# Chat 2
print("Me: What is object-oriented programming?")
r = chat("What is object-oriented programming?")
print(f"ANUBIS: {r.get('response', '(empty)')}")
print(f"  model={r.get('model')} tokens={r.get('tokens')} duration={r.get('duration_s')}s")
print(f"  grounded={r.get('knowledge_grounded')} citations={r.get('knowledge_citations')}")
if r.get("error"):
    print(f"  ERROR: {r['error']}")
print()

# Chat 3
print("Me: What skills do you have?")
r = chat("What skills do you have in your library?")
print(f"ANUBIS: {r.get('response', '(empty)')}")
print(f"  model={r.get('model')} tokens={r.get('tokens')} duration={r.get('duration_s')}s")
if r.get("error"):
    print(f"  ERROR: {r['error']}")
print()

print("=== CHAT COMPLETE ===")
