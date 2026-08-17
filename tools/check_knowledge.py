#!/usr/bin/env python3
"""Check what ANUBIS currently knows."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth
from anubis.knowledge import KnowledgeBase
from anubis.skills import SkillLibrary

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)

print("=== REGISTRY ===")
stats = r.stats()
print(f"Directors: {stats['directors']}")
print(f"Specialties: {stats['specialties']}")
print(f"Verifiers: {stats['verifiers']}")
print(f"Regulated: {stats['regulated_specialties']}")
print(f"Sources: {stats['sources']}")
print(f"Depth distribution: {stats['depth_distribution']}")
print()

print("=== KNOWLEDGE BASE ===")
kstats = kb.stats()
print(f"Library docs: {kstats['library_size']}")
print(f"Quarantine docs: {kstats['quarantine_size']}")
print(f"Total claims: {kstats['total_claims']}")
print()

print("=== SKILLS (learned by writing code) ===")
lib = SkillLibrary(Path("skills"))
for s in lib.iter_current():
    print(f"  {s.name} v{s.version}: {s.description[:60]}")
print(f"Total skills: {sum(1 for _ in lib.iter_current())}")
print()

print("=== SPECIALTIES BY DEPTH ===")
for depth in range(5):
    specs = r.specialties_at_depth(depth)
    if specs:
        name = KnowledgeDepth(depth).name
        print(f"{name} ({len(specs)} specialties):")
        for s in specs[:5]:
            print(f"  {s.canonical_name} ({s.parent_director_id})")
        if len(specs) > 5:
            print(f"  ... and {len(specs)-5} more")
print()

print("=== ALL DIRECTORS ===")
for d in r.directors():
    spec_count = len(d.specialty_ids)
    print(f"  {d.name}: {spec_count} specialties")
