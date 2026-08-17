#!/usr/bin/env python3
"""Check knowledge library status."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry, SourceTier
from collections import Counter

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
docs = kb.library_documents()
print(f"Total library docs: {len(docs)}")
print(f"Quarantine: {kb.quarantine_size()}")
print(f"Stats: {kb.stats()}")
print()

# Check by director
for d in r.directors():
    specs = r.specialties_by_director(d.director_id)
    spec_ids = {s.specialty_id for s in specs}
    matching = [doc for doc in docs if doc.specialty_id in spec_ids]
    tiers = Counter(doc.trust_tier for doc in matching)
    print(f"  {d.director_id} ({d.name}): {len(specs)} specs, {len(matching)} docs, tiers={dict(tiers)}")
