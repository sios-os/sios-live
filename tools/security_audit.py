#!/usr/bin/env python3
"""Security audit — verify sandbox, network, and constitutional enforcement."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.sandbox import Sandbox, SandboxPolicy
from anubis.constitution import ChangeClass, Request, Verdict, evaluate, IMMUTABLE_LAWS

print("=== SIOS SECURITY AUDIT ===")
print()

# 1. Sandbox isolation
print("--- 1. Sandbox Isolation ---")
sb = Sandbox(SandboxPolicy(timeout_s=10, memory_mb=256, cpu_seconds=5))
iso = sb.isolation
print(f"  Network blocked: {iso.network_blocked}")
print(f"  Host mounts masked: {iso.host_mounts_masked}")
print(f"  Unprivileged: {iso.unprivileged}")
print(f"  Label: {iso.label}")
print()

# 2. Sandbox execution test — try to access network
print("--- 2. Sandbox Network Test ---")
network_code = """
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(("8.8.8.8", 53))
    print("NETWORK_ACCESSIBLE")
    s.close()
except Exception as e:
    print(f"NETWORK_BLOCKED: {e}")
"""
result = sb.run_source(network_code, filename="network_test.py")
print(f"  Exit code: {result.exit_code}")
print(f"  Output: {result.stdout.strip()[:100]}")
print(f"  Network blocked: {'NETWORK_BLOCKED' in result.stdout}")
print()

# 3. Sandbox filesystem test — try to read /etc/passwd
print("--- 3. Sandbox Filesystem Test ---")
fs_code = """
try:
    with open("/etc/passwd") as f:
        print("FS_ACCESSIBLE")
        print(f.read()[:50])
except Exception as e:
    print(f"FS_BLOCKED: {e}")
"""
result = sb.run_source(fs_code, filename="fs_test.py")
print(f"  Exit code: {result.exit_code}")
print(f"  Output: {result.stdout.strip()[:100]}")
print()

# 4. Sandbox subprocess test — try to spawn a process
print("--- 4. Sandbox Subprocess Test ---")
proc_code = """
try:
    import subprocess
    r = subprocess.run(["id"], capture_output=True, text=True)
    print(f"SUBPROCESS_ACCESSIBLE: {r.stdout.strip()}")
except Exception as e:
    print(f"SUBPROCESS_BLOCKED: {e}")
"""
result = sb.run_source(proc_code, filename="proc_test.py")
print(f"  Exit code: {result.exit_code}")
print(f"  Output: {result.stdout.strip()[:100]}")
print()

# 5. Constitutional enforcement
print("--- 5. Constitutional Enforcement ---")
tests = [
    ("routine", ChangeClass.ROUTINE, True, "should allow"),
    ("sandboxed", ChangeClass.SANDBOXED, True, "should allow"),
    ("promotion_no_evidence", ChangeClass.PROMOTION, False, "should deny without evidence"),
    ("consequential_no_approval", ChangeClass.CONSEQUENTIAL, False, "should require approval"),
    ("main_engine_no_approval", ChangeClass.MAIN_ENGINE, False, "should require approval"),
]
for name, cc, evidence, expected in tests:
    req = Request(
        actor="anubis",
        action=f"test.{name}",
        change_class=cc,
        evidence_passed=evidence,
        creator_approved=evidence,
    )
    ruling = evaluate(req)
    status = "PASS" if ruling.verdict.name == "ALLOW" and "allow" in expected else "PASS" if ruling.verdict.name != "ALLOW" and "allow" not in expected else "FAIL"
    print(f"  [{status}] {name}: {ruling.verdict.name} ({expected})")
print()

# 6. Immutable laws check
print("--- 6. Immutable Laws ---")
print(f"  Laws: {len(IMMUTABLE_LAWS)}")
for law in IMMUTABLE_LAWS:
    print(f"    - {law}")
print()

# 7. Hazard detection
print("--- 7. Hazard Detection ---")
from anubis.constitution import _HAZARDS
print(f"  Hazard patterns: {len(_HAZARDS)}")
hazards_test = [
    ("os.remove('file')", "recovery"),
    ("subprocess.run(['ls'])", "permission_integrity"),
    ("socket.socket()", "local_privacy"),
    ("eval('1+1')", "audit"),
    ("open('/etc/passwd')", "local_privacy"),
    ("import requests", "local_privacy"),
]
for code, expected_law in hazards_test:
    import re
    matched = False
    for pattern, law, desc in _HAZARDS:
        if re.search(pattern, code):
            matched = True
            print(f"  [PASS] '{code}' -> {law} ({desc})")
            break
    if not matched:
        print(f"  [FAIL] '{code}' -> NOT DETECTED")
print()

print("=== SECURITY AUDIT COMPLETE ===")
