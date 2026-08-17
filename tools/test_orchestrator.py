#!/usr/bin/env python3
"""Test the multi-agent orchestrator with cross-disciplinary queries."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.grounding import KnowledgeGrounding
from anubis.orchestrator import MultiAgentOrchestrator

ROOT = Path(".")
registry = Registry(ROOT / "registry")
kb = KnowledgeBase(ROOT / "knowledge", registry)
grounding = KnowledgeGrounding(kb)
orch = MultiAgentOrchestrator(registry, kb, grounding)

print("=== MULTI-AGENT ORCHESTRATOR TEST ===")
print()

QUERIES = [
    "How do I build a medical device that uses AI to diagnose patients?",
    "What are the ethical implications of artificial intelligence in society?",
    "Design a sustainable farm using modern technology",
    "How does the human brain process language?",
    "Build a secure web application with a database",
]

for query in QUERIES:
    print(f"Query: {query}")
    result = orch.orchestrate(query, max_directors=3)
    print(f"  Directors consulted: {result.directors_consulted}")
    for c in result.contributions:
        print(f"    - {c.director_name}: {c.perspective[:120]}...")
        if c.citations:
            print(f"      Sources: {', '.join(c.citations[:2])}")
    print()

print("=== ORCHESTRATOR TEST COMPLETE ===")
