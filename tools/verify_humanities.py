#!/usr/bin/env python3
"""Verify Humanities director completion."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth
from anubis.knowledge import KnowledgeBase

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)

print("=== Humanities Director Status ===\n")
for s in r.specialties_by_director("humanities"):
    docs = [d for d in kb.library_documents() if d.specialty_id == s.specialty_id]
    depth_name = KnowledgeDepth(s.knowledge_depth).name
    print(f"  {s.canonical_name}: {depth_name}, {len(docs)} docs")

print(f"\n=== Overall ===")
kstats = kb.stats()
print(f"Library total: {kstats['library_size']}")
rstats = r.stats()
print(f"Depth distribution: {rstats['depth_distribution']}")

# Test retrievals
print("\n=== Retrieval tests ===")
for q in ["Plato Aristotle philosophy", "French Revolution timeline", "Homer Shakespeare canon", "Buddhism Hinduism comparison", "radiocarbon dating excavation", "UNESCO World Heritage museum", "archival fonds provenance"]:
    results = kb.retrieve(q, limit=2)
    print(f"\n  '{q}':")
    for doc in results:
        print(f"    [{doc.specialty_id}] {doc.title}")
