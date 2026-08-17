#!/usr/bin/env python3
"""Test knowledge grounding retrieval."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.grounding import KnowledgeGrounding

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
g = KnowledgeGrounding(kb)

print(f"Grounding stats: {g.stats()}")
print()

queries = [
    "What is the normal blood pressure range?",
    "How do I weld aluminum?",
    "What is object-oriented programming?",
    "How do I irrigate crops efficiently?",
    "What causes diabetes?",
]

for q in queries:
    print(f"Query: {q}")
    result = g.ground_with_citations(q, max_docs=2, max_claims=5)
    print(f"  Citations: {result['citations']}")
    print(f"  Claims used: {len(result['claims_used'])}")
    for c in result['claims_used'][:3]:
        print(f"    - {c[:100]}")
    print()
