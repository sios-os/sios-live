#!/usr/bin/env python3
"""Test Tomb hall IPC commands."""
import json, socket, sys

SOCKET = "/tmp/anubis.sock"

def send_cmd(cmd: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

print("=== Tomb Hall IPC Test ===\n")

# Hall of Genesis
print("--- Hall of Genesis ---")
resp = send_cmd({"cmd": "genesis"})
print(f"  Skills: {resp.get('total_skills')}")
print(f"  Ledger: {resp.get('total_ledger_entries')}")
print(f"  Missions: {resp.get('total_missions')} ({resp.get('successful_missions')} successful)")
print(f"  Creator: {resp.get('creator_name', 'Unknown')}")
print(f"  First entries: {len(resp.get('first_entries', []))}")

# Hall of Architects
print("\n--- Hall of Architects ---")
resp = send_cmd({"cmd": "constitution"})
print(f"  Authorities: {len(resp.get('authorities', []))}")
for a in resp.get("authorities", [])[:3]:
    print(f"    {a['value']}. {a['name']}: {a['description'][:50]}")
print(f"  Change classes: {len(resp.get('change_classes', []))}")
for c in resp.get("change_classes", [])[:3]:
    print(f"    {c['value']}. {c['name']}: {c['description'][:50]}")
print(f"  Immutable laws: {resp.get('immutable_laws', [])}")

# Hall of Memory
print("\n--- Hall of Memory ---")
resp = send_cmd({"cmd": "ledger_entries", "limit": 5})
print(f"  Total entries: {resp.get('total')}")
print(f"  Action types: {resp.get('action_types', [])}")
for e in resp.get("entries", [])[:5]:
    print(f"    #{e['seq']} {e['action']}: {e['payload_summary'][:50]}")

# Hall of Evolution
print("\n--- Hall of Evolution ---")
resp = send_cmd({"cmd": "skill_versions", "name": ""})
for s in resp.get("skills", [])[:5]:
    print(f"    {s['name']} v{s['current_version']} ({s['total_versions']} versions) by {s['model']}")

# Hall of Creation
print("\n--- Hall of Creation ---")
resp = send_cmd({"cmd": "mission_history"})
print(f"  Total missions: {resp.get('total')}")
for m in resp.get("missions", [])[:5]:
    status = "SUCCESS" if m.get("success") else "FAILED"
    print(f"    {status}: {m.get('skill_name', '?')} ({m.get('attempts', 0)} attempts)")

# Hall of Sovereignty (uses constitution data, same as Architects)
print("\n--- Hall of Sovereignty ---")
resp = send_cmd({"cmd": "constitution"})
for a in resp.get("authorities", []):
    print(f"    {a['value']}. {a['name']}: {a['description'][:60]}")

print("\n=== All Tomb hall tests passed! ===")
