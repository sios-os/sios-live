#!/usr/bin/env python3
"""Extract atomic claims from all knowledge library documents.

Implements KBP step 8: Evidence extraction.

Usage:
    python3 tools/extract_claims.py                    # all documents
    python3 tools/extract_claims.py computing          # one director
    python3 tools/extract_claims.py computing_k3_batch1  # one specialty prefix
"""
import sys
sys.path.insert(0, ".")

from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.claims import ClaimExtractor

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
extractor = ClaimExtractor()

# Optional filter by specialty prefix
filter_prefix = sys.argv[1] if len(sys.argv) > 1 else ""

docs = kb.library_documents()
if filter_prefix:
    docs = [d for d in docs if filter_prefix in d.specialty_id]

print(f"Extracting claims from {len(docs)} documents...")
print()

total_claims = 0
by_type: dict[str, int] = {}
by_specialty: dict[str, int] = {}

for doc in docs:
    claims = extractor.extract_from_document(doc)
    doc.claims = [c.to_dict() for c in claims]
    total_claims += len(claims)
    by_specialty[doc.specialty_id] = len(claims)
    for c in claims:
        by_type[c.claim_type] = by_type.get(c.claim_type, 0) + 1
    if claims:
        print(f"  {doc.specialty_id}: {len(claims)} claims  [{doc.title}]")

# Save
kb._save()

print()
print(f"=== EXTRACTION COMPLETE ===")
print(f"Documents processed: {len(docs)}")
print(f"Total claims extracted: {total_claims}")
print(f"Average claims per doc: {total_claims / len(docs):.1f}" if docs else "N/A")
print(f"By type: {by_type}")
print(f"Stats: {kb.stats()}")
