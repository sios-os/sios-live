#!/usr/bin/env python3
"""Investigate unverified claims and re-run verification with fixed heuristic."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.verification import ClaimIndex, ClaimVerifier

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
idx = ClaimIndex()
idx.build_from_library(kb)

# Find unverified claims
all_claims = idx.all_claims()
unverified = [c for c in all_claims if c.get("verification_status", "unverified") == "unverified"]
print(f"Total claims: {len(all_claims)}")
print(f"Unverified: {len(unverified)}")
print()

# Show sample unverified claims
print("--- Sample Unverified Claims ---")
for c in unverified[:10]:
    print(f"  [{c.get('claim_type', '?')}] {c.get('text', '')[:100]}")
    print(f"    Doc: {c.get('doc_id', '')}")
    print()

# Check if they share a pattern
print("--- Analysis ---")
types = {}
for c in unverified:
    t = c.get("claim_type", "unknown")
    types[t] = types.get(t, 0) + 1
print(f"  By type: {types}")

# Check doc distribution
docs = {}
for c in unverified:
    d = c.get("doc_id", "")
    docs[d] = docs.get(d, 0) + 1
print(f"  Unique docs with unverified claims: {len(docs)}")
top_docs = sorted(docs.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"  Top docs:")
for doc_id, count in top_docs:
    doc = kb.get_document(doc_id)
    title = doc.title if doc else "?"
    print(f"    {count:3d} claims - {title[:60]}")
print()

# Re-run verification with fixed heuristic
print("=== RE-RUNNING VERIFICATION (fixed negation heuristic) ===")
verifier = ClaimVerifier(idx)
results = verifier.verify_all(kb)
print()
print(f"  Total: {results['total_claims']}")
print(f"  Verified: {results['verified']}")
print(f"  Corroborated: {results['corroborated']}")
print(f"  Contradicted: {results['contradicted']}")
print(f"  Unverified: {results['unverified']}")
print()

# Check if the previously contradicted claim is now fixed
contradicted = [c for c in idx.all_claims() if c.get("verification_status") == "contradicted"]
print(f"  Contradicted claims after fix: {len(contradicted)}")
for c in contradicted:
    print(f"    {c.get('text', '')[:100]}")
