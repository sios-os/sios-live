#!/usr/bin/env python3
"""Test persistent memory and mission-from-chat."""
import json, os, socket, subprocess, sys, time

SOCKET = "/tmp/anubis.sock"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAEMON = os.path.join(ROOT, "tools", "anubis_daemon.py")

def daemon_running() -> bool:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(SOCKET)
        s.close()
        return True
    except (ConnectionRefusedError, FileNotFoundError):
        return False

def send_cmd(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

# Start daemon if not running
daemon_proc = None
if not daemon_running():
    print("Starting daemon...")
    daemon_proc = subprocess.Popen(
        [sys.executable, DAEMON],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=ROOT,
    )
    for _ in range(30):
        time.sleep(1)
        if daemon_running():
            break
    else:
        print("ERROR: daemon did not start")
        sys.exit(1)
    print("Daemon up\n")

print("=== Memory + Mission Chat Test ===\n")

# Test 1: Tell ANUBIS our name
print("Creator: My name is Storm")
resp = send_cmd({"cmd": "chat", "message": "My name is Storm"})
print(f"ANUBIS: {resp.get('response', resp.get('error', '?'))[:200]}")
print()

# Test 2: Ask if ANUBIS remembers
print("Creator: What's my name?")
resp = send_cmd({"cmd": "chat", "message": "What's my name?"})
print(f"ANUBIS: {resp.get('response', resp.get('error', '?'))[:200]}")
print()

# Test 3: Request a mission (no approval)
print("Creator: Write me a function that checks if a string is a palindrome")
resp = send_cmd({"cmd": "chat", "message": "Write me a function that checks if a string is a palindrome"})
print(f"ANUBIS: {resp.get('response', resp.get('error', '?'))[:300]}")
if resp.get("mission_request"):
    print(f"  -> Mission detected: task={resp.get('task')}, skill={resp.get('skill_name')}")
    print(f"  -> Needs approval: {resp.get('needs_approval')}")
print()

# Test 4: Same mission with approval
print("Creator: [approving mission]")
resp = send_cmd({
    "cmd": "chat",
    "message": "Write me a function that checks if a string is a palindrome",
    "approval_token": "creator-approved",
})
print(f"ANUBIS: {resp.get('response', resp.get('error', '?'))[:300]}")
if resp.get("mission_launched"):
    mid = resp.get("mission_id")
    print(f"  -> Mission launched: {mid}")
    # Poll for completion
    for _ in range(60):
        time.sleep(3)
        poll = send_cmd({"cmd": "poll", "mission_id": mid})
        status = poll.get("status", "?")
        print(f"  -> Poll: {status}", end="")
        if status in ("complete", "failed", "error"):
            print(f"  success={poll.get('success')}  attempts={poll.get('attempts')}")
            break
        print(" (still running...)")
    else:
        print("  -> Timed out waiting")
print()

# Test 5: Check memory files
from pathlib import Path
root = Path("/mnt/d/SIOS-Build/sios-live/memory")
print("=== Memory files ===")
for f in root.iterdir():
    print(f"  {f.name}: {f.stat().st_size} bytes")
    if f.suffix == ".json":
        print(f"    {f.read_text()[:200]}")

# Clean up daemon if we started it
if daemon_proc:
    daemon_proc.terminate()
    daemon_proc.wait(timeout=5)
    print("\nDaemon stopped.")
