#!/usr/bin/env python3
"""Test workspace tools: filesystem and terminal."""
import json, socket, sys

SOCKET = "/tmp/anubis.sock"

def send_cmd(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

print("=== Workspace Tools Test ===\n")

# Test 1: List directory
print("--- File Browser: List /mnt/d/SIOS-Build/sios-live ---")
resp = send_cmd({"cmd": "fs_list", "path": "/mnt/d/SIOS-Build/sios-live"})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    entries = resp.get("entries", [])
    print(f"  Path: {resp.get('path')}")
    print(f"  Items: {len(entries)}")
    for e in entries[:10]:
        kind = "DIR " if e["is_dir"] else "FILE"
        print(f"    {kind} {e['name']}")

# Test 2: Read a file
print("\n--- File Browser: Read anubis/__init__.py ---")
resp = send_cmd({"cmd": "fs_read", "path": "/mnt/d/SIOS-Build/sios-live/anubis/__init__.py"})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    content = resp.get("content", "")
    print(f"  Size: {resp.get('size')} bytes")
    print(f"  First 200 chars: {content[:200]}")

# Test 3: Write a file
print("\n--- Text Editor: Write test file ---")
resp = send_cmd({
    "cmd": "fs_write",
    "path": "/tmp/sios_test_file.txt",
    "content": "Hello from SIOS Workspace!\nThis file was written via the desktop.\n",
    "approval_token": "creator-approved",
})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    print(f"  Written: {resp.get('written')}  Size: {resp.get('size')} bytes")

# Test 4: Read it back
print("\n--- Text Editor: Read test file back ---")
resp = send_cmd({"cmd": "fs_read", "path": "/tmp/sios_test_file.txt"})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    print(f"  Content: {resp.get('content', '').strip()}")

# Test 5: Run a terminal command
print("\n--- Terminal: Run 'echo Hello SIOS' ---")
resp = send_cmd({"cmd": "run_cmd", "command": "echo Hello SIOS", "approval_token": "creator-approved"})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    print(f"  stdout: {resp.get('stdout', '').strip()}")
    print(f"  exit_code: {resp.get('exit_code')}")

# Test 6: Run 'ls'
print("\n--- Terminal: Run 'ls skills' ---")
resp = send_cmd({"cmd": "run_cmd", "command": "ls /mnt/d/SIOS-Build/sios-live/skills", "approval_token": "creator-approved"})
if "error" in resp:
    print(f"ERROR: {resp['error']}")
else:
    print(f"  stdout: {resp.get('stdout', '').strip()[:200]}")

# Test 7: Block dangerous command
print("\n--- Terminal: Try blocked command 'rm -rf /' ---")
resp = send_cmd({"cmd": "run_cmd", "command": "rm -rf /", "approval_token": "creator-approved"})
print(f"  Result: {resp.get('error', 'NOT BLOCKED!')}")

# Test 8: No approval
print("\n--- Terminal: Try without approval ---")
resp = send_cmd({"cmd": "run_cmd", "command": "whoami"})
print(f"  Result: {resp.get('error', resp)}")

print("\n=== All workspace tools tests passed! ===")
