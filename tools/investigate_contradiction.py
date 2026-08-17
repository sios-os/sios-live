#!/usr/bin/env python3
"""Find and investigate the contradicted claim."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.verification import ClaimIndex

r = Registry(Path("registry"))
kb = KnowledgeBase(Path("knowledge"), r)
idx = ClaimIndex()
idx.build_from_library(kb)

# Find all contradicted claims
contradicted = [c for c in idx.all_claims() if c.get("verification_status") == "contradicted"]
print(f"Contradicted claims: {len(contradicted)}")
print()

for c in contradicted:
    print(f"=== CONTRADICTED CLAIM ===")
    print(f"  Claim ID: {c.get('claim_id', '')}")
    print(f"  Text: {c.get('text', '')}")
    print(f"  Type: {c.get('claim_type', '')}")
    print(f"  Doc ID: {c.get('doc_id', '')}")
    print(f"  Contradiction count: {c.get('contradiction_count', 0)}")
    print(f"  Corroboration count: {c.get('corroboration_count', 0)}")
    print()

    # Find the contradicting claims
    contradicting_ids = c.get("contradicting_ids", [])
    print(f"  Contradicting claim IDs: {contradicting_ids}")
    for cid in contradicting_ids:
        other = idx.get(cid)
        if other:
            print(f"    -> [{other.get('claim_type', '')}] {other.get('text', '')}")
            print(f"       Doc: {other.get('doc_id', '')}")
    print()

    # Find the source document
    doc = kb.get_document(c.get("doc_id", ""))
    if doc:
        print(f"  Source document: {doc.title}")
        print(f"  Specialty: {doc.specialty_id}")
    print()

    # Find corroborating claims
    corroborating_ids = c.get("corroborating_ids", [])
    if corroborating_ids:
        print(f"  Corroborating claims ({len(corroborating_ids)}):")
        for cid in corroborating_ids[:5]:
            other = idx.get(cid)
            if other:
                print(f"    -> [{other.get('claim_type', '')}] {other.get('text', '')[:100]}")
        print()

    # Assessment
    print("  ASSESSMENT:")
    if c.get("contradiction_count", 0) > c.get("corroboration_count", 0):
        print("    This claim has more contradictions than corroboration.")
        print("    This is likely a FALSE POSITIVE from the negation heuristic.")
        print("    The claim may use a word like 'not' or 'no' in a non-negating context.")
    else:
        print("    This claim has corroboration but also some contradictions.")
        print("    May be a nuanced claim with partial truth.")
    print()
