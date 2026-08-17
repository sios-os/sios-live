#!/usr/bin/env python3
"""Test all new daemon commands."""
import json, socket, sys

SOCKET = "/tmp/anubis.sock"

def send(cmd):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET)
    s.sendall((json.dumps(cmd) + "\n").encode())
    data = s.recv(65536).decode()
    s.close()
    return json.loads(data)

print("=== New Module Tests ===\n")

# Registry
r = send({"cmd": "registry_stats"})
print(f"Registry: {r['directors']} directors, {r['specialties']} specialties, {r['verifiers']} verifiers")

# Directors
r = send({"cmd": "list_directors"})
print(f"Directors listed: {len(r['directors'])}")

# Knowledge
r = send({"cmd": "knowledge_stats"})
print(f"Knowledge: {r['library_size']} library docs, {r['quarantine_size']} quarantined")

# Identity
r = send({"cmd": "identity_stats"})
print(f"Identity: enrolled={r['enrolled']}, vault_unlocked={r['vault_unlocked']}")

# Court
r = send({"cmd": "court_stats"})
print(f"Court: {r['total_reviews']} reviews")

# Policy
r = send({"cmd": "policy_stats"})
print(f"Policy: {r['active_mandates']} mandates, {r['total_transactions']} transactions")

# Capability
r = send({"cmd": "capability_stats"})
print(f"Capability: {r['total_tokens']} tokens")

# Network
r = send({"cmd": "network_stats"})
print(f"Network: policy={r['policy']}, {r['rules']} rules, {r['approved_endpoints']} endpoints")

# Hardening
r = send({"cmd": "hardening_stats"})
print(f"Hardening: {r['kernel_params']} kernel params, {r['open_findings']} open findings")

# Recovery
r = send({"cmd": "recovery_stats"})
print(f"Recovery: {r['total_drills']} drills, {r['recovery_steps']} steps")

# A/B
r = send({"cmd": "ab_stats"})
print(f"A/B: {r}")

# Egyptology
r = send({"cmd": "egyptology_stats"})
print(f"Egyptology: {r['total_signs']} signs, {r['total_words']} words")

# Egyptology lookup
r = send({"cmd": "egyptology_lookup", "word": "nsw"})
print(f"Egyptology 'nsw': {r.get('translation', r.get('error', '?'))}")

r = send({"cmd": "egyptology_lookup", "sign": "A1"})
print(f"Egyptology 'A1': {r.get('description', r.get('error', '?'))}")

# Packages
r = send({"cmd": "package_stats"})
print(f"Packages: {r['total_packages']} installed")

# Financial
r = send({"cmd": "financial_stats"})
print(f"Financial: {r['total_entries']} entries, balance={r['total_balance']}")

# Knowledge search
r = send({"cmd": "knowledge_search", "query": "python"})
print(f"Knowledge search 'python': {len(r.get('results', []))} results")

print("\n=== All new module tests passed! ===")
