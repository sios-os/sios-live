#!/usr/bin/env python3
"""Test the DEMON chat endpoint."""
import json, socket, sys, time

SOCKET = "/tmp/anubis.sock"

def send_cmd(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

messages = [
    "Hello ANUBIS. Who are you?",
    "What skills do you have?",
    "Can you write a Python function for me?",
]

print("=== DEMON Chat Test ===\n")
for msg in messages:
    print(f"Creator: {msg}")
    t0 = time.time()
    resp = send_cmd({"cmd": "chat", "message": msg})
    elapsed = time.time() - t0
    if "error" in resp:
        print(f"ERROR: {resp['error']}")
    else:
        print(f"ANUBIS: {resp['response']}")
        print(f"  [{resp.get('model','?')}  {resp.get('tokens','?')} tok  {resp.get('duration_s','?')}s]")
    print()
