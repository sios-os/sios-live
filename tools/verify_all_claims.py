#!/usr/bin/env python3
"""Build claim index and run verification across all claims.

Implements KBP step 9: Independent verification.
"""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.verification import build_and_verify

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)

print("=== Building claim index and running verification ===")
print()
summary = build_and_verify(kb)

print()
print("=== VERIFICATION COMPLETE ===")
print(f"Index: {summary['index_stats']}")
print(f"Verification: {summary['verification_summary']}")

# Show some sample verified claims
print()
print("=== Sample verified claims ===")
from anubis.verification import ClaimIndex
idx = ClaimIndex()
idx.build_from_library(kb)
verified = [c for c in idx.all_claims() if c.get("verification_status") == "verified"]
for c in verified[:10]:
    print(f"  [{c.get('claim_type')}] (conf={c.get('confidence_adjusted', 0):.2f}) {c.get('text', '')[:100]}")

print()
print("=== Sample contradicted claims ===")
contradicted = [c for c in idx.all_claims() if c.get("verification_status") == "contradicted"]
for c in contradicted[:10]:
    print(f"  [{c.get('claim_type')}] {c.get('text', '')[:100]}")
    print(f"    contradictions: {c.get('contradiction_count', 0)}")
