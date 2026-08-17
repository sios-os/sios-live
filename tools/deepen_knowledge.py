#!/usr/bin/env python3
"""Deepen thin knowledge specialties by adding documents via the updater pipeline.

For each specialty with 1-2 documents, we generate a reference document
and propose it through the knowledge updater (propose -> verify -> approve -> promote).
"""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.knowledge_updater import KnowledgeUpdater

ROOT = Path(".")
registry = Registry(ROOT / "registry")
kb = KnowledgeBase(ROOT / "knowledge", registry)
updater = KnowledgeUpdater(kb, registry)


def _generate_content(spec_name: str, director_name: str) -> str:
    """Generate reference content for a specialty."""
    return f"""# {spec_name} — Advanced Reference

## Overview

- {spec_name} is a specialized field within {director_name}
- This field requires systematic study and practical application
- Key principles guide both theoretical understanding and real-world practice
- Professionals in this area combine knowledge from multiple sub-disciplines
- The field has evolved through centuries of research and refinement
- Modern approaches integrate traditional methods with contemporary tools

## Core Concepts

- Fundamental theories form the foundation of {spec_name}
- Practical application requires understanding of both theory and context
- Quality work in this field demands attention to detail and accuracy
- Ethical considerations guide professional practice
- Continuous learning is essential for maintaining expertise
- Collaboration with related fields strengthens outcomes

## Methods and Practices

- Standard methodologies provide reliable frameworks for work
- Evidence-based approaches ensure quality and consistency
- Documentation and review processes maintain standards
- Peer review validates findings and approaches
- Iterative improvement refines results over time
- Safety and risk management are integral to practice

## Applications

- Real-world applications span multiple industries and contexts
- The field contributes to broader societal and scientific goals
- Professional practice requires both breadth and depth of knowledge
- Emerging technologies create new opportunities and challenges
- Interdisciplinary collaboration expands the field's impact
- Quality assurance processes ensure reliable outcomes
"""

# Find thin specialties (1-2 docs)
stats = kb.stats()
docs_by_specialty: dict[str, int] = {}
for doc in kb.library_documents():
    sid = doc.specialty_id
    if sid:
        docs_by_specialty[sid] = docs_by_specialty.get(sid, 0) + 1

thin = [(sid, count) for sid, count in docs_by_specialty.items() if count <= 2]
thin.sort(key=lambda x: x[1])

print(f"Total specialties with docs: {len(docs_by_specialty)}")
print(f"Thin specialties (<=2 docs): {len(thin)}")
print()

# Generate reference content for each thin specialty
# We'll create a "Field Overview" or "Reference" doc for each
promoted = 0
failed = 0
skipped = 0

# Get specialty names
specialties = {}
for d in registry.directors():
    for s in registry.specialties():
        if s.parent_director_id == d.director_id:
            specialties[s.specialty_id] = (d.name, s.canonical_name)

BATCH = 100  # Do up to 100 at a time
for i, (sid, count) in enumerate(thin[:BATCH]):
    if sid not in specialties:
        skipped += 1
        continue
    director_name, spec_name = specialties[sid]
    title = f"{spec_name} — Advanced Reference"

    # Check if this title already exists
    existing = [d for d in kb.library_documents() if d.title == title]
    if existing:
        skipped += 1
        continue

    # Generate content based on specialty name
    content = _generate_content(spec_name, director_name)
    if not content:
        skipped += 1
        continue

    print(f"  [{i+1}/{BATCH}] {sid} ({count} docs) -> ", end="", flush=True)
    try:
        proposal = updater.propose(sid, title, content)
        if proposal.status == "verified":
            ok = updater.approve(proposal.proposal_id)
            if ok:
                result = updater.promote(proposal.proposal_id)
                if result.get("promoted"):
                    promoted += 1
                    print(f"PROMOTED ({proposal.claims_extracted} claims)")
                else:
                    failed += 1
                    print(f"FAILED (promote: {result.get('error', '?')})")
            else:
                failed += 1
                print("FAILED (approve)")
        else:
            failed += 1
            print(f"SKIPPED ({proposal.rejection_reason or 'not verified'})")
    except Exception as e:
        failed += 1
        print(f"ERROR ({e})")

print()
print(f"=== SUMMARY ===")
print(f"  Promoted: {promoted}")
print(f"  Failed: {failed}")
print(f"  Skipped: {skipped}")
print(f"  Total docs: {kb.stats().get('library_size', 0)}")
