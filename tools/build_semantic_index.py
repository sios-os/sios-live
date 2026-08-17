#!/usr/bin/env python3
"""Build the semantic embedding index for the knowledge library."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.semantic import SemanticIndex

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
idx = SemanticIndex()

print("=== BUILDING SEMANTIC INDEX ===")
print(f"  Model: nomic-embed-text (768-dim)")
print(f"  Documents: {kb.stats()['library_size']}")
print()

stats = idx.build(kb, batch_size=25)
print()
print(f"  Built: {stats['built']}")
print(f"  Skipped (cached): {stats['skipped']}")
print(f"  Total: {stats['total']}")
print()
print(f"  Index stats: {idx.stats()}")

# Test a few queries
print()
print("=== SEMANTIC SEARCH TESTS ===")
queries = [
    "object oriented programming",
    "blood pressure medication",
    "ancient egyptian burial practices",
    "how to weld steel",
    "diabetes treatment",
]
for q in queries:
    results = idx.search(q, top_k=3)
    print(f"\n  Query: '{q}'")
    for r in results:
        print(f"    [{r.score:.3f}] {r.title} ({r.specialty_id})")
