#!/usr/bin/env python3
"""Governance review — verify constitution, ledger, and court integrity."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.constitution import IMMUTABLE_LAWS, Authority, ChangeClass, Verdict, evaluate, Request
from anubis.ledger import Ledger
from anubis.governance import PolicyEngine, CapabilityBroker, Court
from anubis.identity import IdentityService

ROOT = Path(".")

print("=== SIOS GOVERNANCE REVIEW ===")
print()

# 1. Constitution
print("--- Constitution ---")
print(f"Immutable laws: {len(IMMUTABLE_LAWS)}")
for i, law in enumerate(IMMUTABLE_LAWS):
    print(f"  {i+1}. {law}")
print(f"Authorities: {len(list(Authority))}")
for a in Authority:
    print(f"  {a.value}. {a.name}")
print(f"Change classes: {len(list(ChangeClass))}")
for cc in ChangeClass:
    print(f"  {cc.value}. {cc.name}")
print()

# 2. Ledger integrity
print("--- Evidence Ledger ---")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
ok, msg = ledger.verify()
print(f"Entries: {ledger.length}")
print(f"Integrity: {'PASS' if ok else 'FAIL'} - {msg}")
print(f"Head: {ledger.head[:24]}...")
print()

# 3. Identity
print("--- Identity ---")
identity = IdentityService(ROOT / "identity")
stats = identity.stats()
print(f"Stats: {stats}")
print()

# 4. Policy Engine
print("--- Policy Engine ---")
policy = PolicyEngine(ROOT / "policy")
print(f"Stats: {policy.stats()}")
print()

# 5. Capability Broker
print("--- Capability Broker ---")
caps = CapabilityBroker(ROOT / "capabilities")
print(f"Stats: {caps.stats()}")
print()

# 6. Court
print("--- Court ---")
court = Court(ROOT / "court")
print(f"Stats: {court.stats()}")
print()

# 7. Test constitutional evaluation
print("--- Constitutional Test ---")
# Test a routine action
req = Request(
    actor="anubis",
    action="skill.propose",
    change_class=ChangeClass.SANDBOXED,
    capabilities_requested=frozenset({"skill.author"}),
    capabilities_granted=frozenset({"skill.author"}),
)
ruling = evaluate(req)
print(f"Test 1 (sandboxed skill): {ruling.verdict.name} - {ruling.explain()[:80]}")

# Test a consequential action without approval
req2 = Request(
    actor="anubis",
    action="knowledge.modify",
    change_class=ChangeClass.CONSEQUENTIAL,
    capabilities_requested=frozenset({"skill.author"}),
    capabilities_granted=frozenset({"skill.author"}),
)
ruling2 = evaluate(req2)
print(f"Test 2 (consequential, no approval): {ruling2.verdict.name}")

# Test a main engine change
req3 = Request(
    actor="anubis",
    action="model.upgrade",
    change_class=ChangeClass.MAIN_ENGINE,
    capabilities_requested=frozenset({"skill.author"}),
    capabilities_granted=frozenset({"skill.author"}),
)
ruling3 = evaluate(req3)
print(f"Test 3 (main engine, no approval): {ruling3.verdict.name}")
print()

print("=== GOVERNANCE REVIEW COMPLETE ===")
