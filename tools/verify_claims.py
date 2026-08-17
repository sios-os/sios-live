#!/usr/bin/env python3
"""Verify claim extraction results."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from collections import Counter

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)

stats = kb.stats()
print(f"Stats: {stats}")
print()

# Sample claims from a few documents
docs = kb.library_documents()
samples = [d for d in docs if d.specialty_id in ("computing_programming", "health_cardiology", "trades_welding_metalworking", "agriculture_soil_science")]
for doc in samples:
    print(f"=== {doc.specialty_id}: {doc.title} ===")
    print(f"  Claims: {len(doc.claims)}")
    for c in doc.claims[:5]:
        print(f"  [{c.get('claim_type', '?')}] (conf={c.get('confidence', 0):.2f}) {c.get('text', '')[:120]}")
    print()

# Aggregate by director
print("=== Claims by director ===")
for d in r.directors():
    specs = r.specialties_by_director(d.director_id)
    spec_ids = {s.specialty_id for s in specs}
    matching = [doc for doc in docs if doc.specialty_id in spec_ids]
    total = sum(len(doc.claims) for doc in matching)
    print(f"  {d.director_id}: {total} claims across {len(matching)} docs")

# Aggregate by type
print()
print("=== Claims by type ===")
all_claims = [c for doc in docs for c in doc.claims]
type_counts = Counter(c.get("claim_type", "unknown") for c in all_claims)
print(f"  {dict(type_counts)}")
print(f"  Total: {len(all_claims)}")
