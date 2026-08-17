#!/usr/bin/env python3
"""Test the IPC bridge path that Godot will use: temp file -> bash -> socket -> temp file."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOCKET = "/tmp/anubis.sock"

def send_via_bridge(req: dict) -> dict:
    """Simulate exactly what the Godot IPCBridge does."""
    tmp_in = "/tmp/anubis-ipc-req.json"
    tmp_out = "/tmp/anubis-ipc-resp.json"
    with open(tmp_in, "w") as f:
        f.write(json.dumps(req))
    helper = (
        "python3 -c \""
        "import json,socket;"
        "s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);"
        f"s.connect('{SOCKET}');"
        f"req=open('{tmp_in}').read();"
        "s.sendall((req+chr(10)).encode());"
        "resp=s.recv(65536).decode();"
        f"open('{tmp_out}','w').write(resp);"
        "s.close()\""
    )
    result = subprocess.run(["bash", "-c", helper], capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": f"bridge failed: {result.stderr}"}
    with open(tmp_out) as f:
        text = f.read().strip()
    return json.loads(text)

# Start daemon
daemon = subprocess.Popen(
    [sys.executable, str(ROOT / "tools" / "anubis_daemon.py")],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=str(ROOT), env={**os.environ, "ANUBIS_SOCKET": SOCKET},
)
time.sleep(2)

try:
    print("=== Bridge test: status ===")
    r = send_via_bridge({"cmd": "status"})
    print(json.dumps(r, indent=2))
    assert r.get("daemon") == "running"

    print("\n=== Bridge test: skills ===")
    r = send_via_bridge({"cmd": "skills"})
    print(f"Skills: {r.get('count', 0)}")
    for s in r.get("skills", []):
        print(f"  {s['name']} v{s['version']}  {s['artifact_hash']}")

    print("\n=== Bridge test: ledger ===")
    r = send_via_bridge({"cmd": "ledger"})
    print(f"Entries: {r.get('entries')}")
    print(f"Integrity: {r.get('integrity_ok')}")

    print("\n=== Bridge test: mission (no approval) ===")
    r = send_via_bridge({"cmd": "mission", "task": "test", "skill_name": "test"})
    print(f"Response: {r}")
    assert "approval" in r.get("error", "").lower()

    print("\nALL BRIDGE TESTS PASSED")
finally:
    daemon.terminate()
    daemon.wait(timeout=5)
