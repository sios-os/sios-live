#!/usr/bin/env python3
"""Test the ANUBIS daemon socket interface end-to-end."""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCKET = "/tmp/anubis-test.sock"

def send(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data.strip())

# Start daemon with test socket
env = dict(__import__("os").environ)
env["ANUBIS_SOCKET"] = SOCKET
proc = subprocess.Popen(
    [sys.executable, str(ROOT / "tools" / "anubis_daemon.py")],
    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=str(ROOT),
)
time.sleep(2)

try:
    print("=== status ===")
    r = send({"cmd": "status"})
    print(json.dumps(r, indent=2))

    print("\n=== skills ===")
    r = send({"cmd": "skills"})
    print(json.dumps(r, indent=2))

    print("\n=== ledger ===")
    r = send({"cmd": "ledger"})
    print(json.dumps(r, indent=2))

    print("\n=== mission (no approval) ===")
    r = send({"cmd": "mission", "task": "test", "skill_name": "test"})
    print(json.dumps(r, indent=2))

    print("\nALL DAEMON TESTS PASSED")
finally:
    proc.terminate()
    proc.wait(timeout=5)
