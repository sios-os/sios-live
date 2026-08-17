#!/usr/bin/env python3
"""End-to-end daemon test — verify all systems work together."""
import sys
sys.path.insert(0, ".")
import json
import socket
import time
from pathlib import Path

SOCKET_PATH = "/tmp/anubis.sock"

def call_daemon(cmd, **kwargs):
    """Send a command to the daemon and get the response."""
    req = {"cmd": cmd}
    req.update(kwargs)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(30.0)
        s.connect(SOCKET_PATH)
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        data = s.recv(65536).decode("utf-8")
        s.close()
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

# Start the daemon in background
import subprocess
ROOT = Path(".")

# Check if daemon is already running
import os
daemon_running = os.path.exists(SOCKET_PATH)

if not daemon_running:
    print("Starting ANUBIS daemon...")
    proc = subprocess.Popen(
        ["python3", "tools/anubis_daemon.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(ROOT),
    )
    # Wait for socket
    for i in range(15):
        if os.path.exists(SOCKET_PATH):
            break
        time.sleep(1)
    else:
        print("ERROR: Daemon did not start")
        sys.exit(1)
    print("Daemon started.")
else:
    print("Daemon already running.")

print()
print("=== END-TO-END DAEMON TEST ===")
print()

# 1. Status
print("--- 1. Status ---")
resp = call_daemon("status")
print(f"  Daemon: {resp.get('daemon', '?')}")
print(f"  Model: {resp.get('model', '?')} present={resp.get('model_present', False)}")
print(f"  Skills: {resp.get('skills_count', 0)}")
print(f"  Ledger: {resp.get('ledger_entries', 0)}")
print()

# 2. Identity (Creator enrollment)
print("--- 2. Creator Identity ---")
resp = call_daemon("get_identity_stats")
print(f"  Enrolled: {resp.get('enrolled', False)}")
print(f"  Creator: {resp.get('creator_name', '?')}")
print(f"  Successors: {resp.get('successors', 0)}")
print(f"  Consented: {resp.get('consented_successors', 0)}")
print()

# 3. Knowledge library
print("--- 3. Knowledge Library ---")
resp = call_daemon("get_knowledge_stats")
print(f"  Library: {resp.get('library_size', 0)} docs")
print(f"  Claims: {resp.get('total_claims', 0)}")
print(f"  Verified: {resp.get('verified_docs', 0)}")
print()

# 4. Grounding stats
print("--- 4. Grounding System ---")
resp = call_daemon("get_grounding_stats")
print(f"  Library: {resp.get('library_size', 0)}")
print(f"  Claims indexed: {resp.get('claims_indexed', 0)}")
idx_stats = resp.get("index_stats", {})
print(f"  Keywords: {idx_stats.get('keywords_indexed', 0)}")
print(f"  Specialties: {idx_stats.get('specialties_indexed', 0)}")
print()

# 5. Knowledge grounding query
print("--- 5. Knowledge Grounding Query ---")
resp = call_daemon("knowledge_ground", query="object oriented programming")
citations = resp.get("citations", [])
claims = resp.get("claims_used", [])
print(f"  Citations: {len(citations)}")
for c in citations:
    print(f"    - {c}")
print(f"  Claims: {len(claims)}")
print()

# 6. Claim search
print("--- 6. Claim Search ---")
resp = call_daemon("claim_search", query="blood pressure", limit=5)
results = resp.get("results", [])
print(f"  Results: {len(results)}")
for r in results[:3]:
    print(f"    [{r.get('type', '?')}] {r.get('text', '')[:80]}")
print()

# 7. Constitution
print("--- 7. Constitution ---")
resp = call_daemon("get_constitution")
laws = resp.get("immutable_laws", [])
print(f"  Immutable laws: {len(laws)}")
for l in laws[:3]:
    print(f"    - {l}")
print()

# 8. Ledger
print("--- 8. Evidence Ledger ---")
resp = call_daemon("get_ledger")
print(f"  Entries: {resp.get('entries', 0)}")
print(f"  Integrity: {resp.get('integrity_ok', False)}")
print()

# 9. Skills
print("--- 9. Skill Library ---")
resp = call_daemon("get_skills")
skills = resp.get("skills", [])
print(f"  Skills: {len(skills)}")
for s in skills:
    print(f"    {s.get('name', '?')} v{s.get('version', 0)}")
print()

# 10. DEMON chat (knowledge-grounded)
print("--- 10. DEMON Chat (Knowledge-Grounded) ---")
resp = call_daemon("chat", message="What is object-oriented programming?")
if "error" in resp:
    print(f"  Error: {resp['error']}")
else:
    print(f"  Response: {resp.get('response', '')[:200]}...")
    print(f"  Knowledge grounded: {resp.get('knowledge_grounded', False)}")
    print(f"  Citations: {resp.get('knowledge_citations', [])}")
    print(f"  Claims used: {resp.get('claims_used', 0)}")
    print(f"  Model: {resp.get('model', '?')}")
    print(f"  Duration: {resp.get('duration_s', 0)}s")
print()

# 11. Directors
print("--- 11. Knowledge Directors ---")
resp = call_daemon("list_directors")
directors = resp.get("directors", [])
print(f"  Directors: {len(directors)}")
for d in directors:
    print(f"    {d.get('director_id', '?')}: {d.get('name', '?')}")
print()

print("=== END-TO-END TEST COMPLETE ===")
