#!/usr/bin/env python3
"""Knowledge gap analysis — find thin specialties and missing coverage."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from collections import Counter

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)

# Count documents per specialty
doc_counts = Counter()
claim_counts = Counter()
for doc in kb.library_documents():
    doc_counts[doc.specialty_id] += 1
    claim_counts[doc.specialty_id] += len(doc.claims) if hasattr(doc, 'claims') else 0

# Get all registered specialties
all_specialties = {}
for d in r.directors():
    for s in r.specialties_by_director(d.director_id):
        all_specialties[s.specialty_id] = s

# Find gaps
print("=== KNOWLEDGE GAP ANALYSIS ===")
print()
print(f"Total specialties: {len(all_specialties)}")
print(f"Specialties with docs: {len(doc_counts)}")
print(f"Specialties without docs: {len(all_specialties) - len(doc_counts)}")
print()

# Specialties with no documents
no_docs = [sid for sid in all_specialties if sid not in doc_counts]
if no_docs:
    print("--- Specialties with NO documents ---")
    for sid in no_docs[:20]:
        s = all_specialties[sid]
        print(f"  {sid}: {s.canonical_name if s else '?'}")
    print()

# Thinnest specialties (1-2 docs)
thin = [(sid, doc_counts[sid]) for sid in doc_counts if doc_counts[sid] <= 2]
thin.sort(key=lambda x: x[1])
print(f"--- Thinnest specialties (1-2 docs): {len(thin)} ---")
for sid, count in thin[:15]:
    s = all_specialties.get(sid)
    claims = claim_counts.get(sid, 0)
    print(f"  {sid}: {count} docs, {claims} claims — {s.canonical_name if s else '?'}")
print()

# Thickest specialties
thick = doc_counts.most_common(10)
print("--- Top 10 specialties by document count ---")
for sid, count in thick:
    s = all_specialties.get(sid)
    name = s.canonical_name if s else "?"
    claims = claim_counts.get(sid, 0)
    print(f"  {sid}: {count} docs, {claims} claims — {name}")
print()

# Per-director summary
print("--- Per-director summary ---")
for d in r.directors():
    specs = r.specialties_by_director(d.director_id)
    total_docs = sum(doc_counts.get(s.specialty_id, 0) for s in specs)
    total_claims = sum(claim_counts.get(s.specialty_id, 0) for s in specs)
    empty = sum(1 for s in specs if s.specialty_id not in doc_counts)
    print(f"  {d.director_id:30s} {len(specs):3d} specs, {total_docs:3d} docs, {total_claims:5d} claims, {empty} empty")
print()

# Recommendations
print("=== RECOMMENDATIONS ===")
if no_docs:
    print(f"  1. {len(no_docs)} specialties have zero documents — consider populating")
if thin:
    print(f"  2. {len(thin)} specialties have only 1-2 documents — consider deepening")
print(f"  3. Average docs per specialty: {sum(doc_counts.values()) / len(doc_counts):.1f}")
print(f"  4. Average claims per specialty: {sum(claim_counts.values()) / len(claim_counts):.1f}")
