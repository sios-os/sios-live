#!/usr/bin/env python3
"""Populate Computing director knowledge base.

Stage 1: K1 orientation for all 34 computing specialties.
Stage 2: K3 deepening for coding-heavy specialties.
"""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth, SourceTier, SourceRecord
from anubis.knowledge import KnowledgeBase, PopulationPipeline
from anubis.knowledge_content.computing_k1 import COMPUTING_K1


def main() -> None:
    root = Path(".")
    registry = Registry(root / "registry")
    knowledge = KnowledgeBase(root / "knowledge", registry)
    pipeline = PopulationPipeline(registry, knowledge)

    # Register a local source for this content
    src_id = "src_sios_computing_k1"
    if registry.get_source(src_id) is None:
        registry.register_source(SourceRecord(
            source_id=src_id,
            name="SIOS Computing K1 Orientation",
            publisher="SIOS",
            tier=SourceTier.T3,
            source_class=0,  # A - open/authoritative
            license="CC0",
            copyright_owner="SIOS",
            permitted_uses=["reference", "retrieval"],
            attribution_required=False,
            redistribution_allowed=True,
            training_allowed=True,
            status="trusted",
        ))

    print("=== Stage 1: K1 orientation for all 34 Computing specialties ===\n")
    total_promoted = 0
    for spec_id, docs in COMPUTING_K1.items():
        spec = registry.get_specialty(spec_id)
        if spec is None:
            print(f"  SKIP {spec_id}: not in registry")
            continue
        # Add source_id and license to each doc
        for d in docs:
            d.setdefault("source_id", src_id)
            d.setdefault("license", "CC0")
            d.setdefault("trust_tier", SourceTier.T3)
            d.setdefault("verification_notes", "Creator-approved K1 orientation")
        result = pipeline.populate_specialty(spec_id, docs, creator_approved=True)
        promoted = result.get("promoted", 0)
        total_promoted += promoted
        depth = result.get("new_depth", 0)
        depth_name = KnowledgeDepth(depth).name if depth is not None else "?"
        print(f"  {spec_id}: promoted={promoted}, depth={depth_name}")

    print(f"\nTotal K1 documents promoted: {total_promoted}")

    # Verify
    print("\n=== Verification ===")
    kstats = knowledge.stats()
    print(f"Library docs: {kstats['library_size']}")
    print(f"Quarantine docs: {kstats['quarantine_size']}")
    print(f"Total claims: {kstats['total_claims']}")
    rstats = registry.stats()
    print(f"Depth distribution: {rstats['depth_distribution']}")

    # Test retrieval
    print("\n=== Retrieval test: 'python' ===")
    results = knowledge.retrieve("python", limit=3)
    for r in results:
        print(f"  [{r.specialty_id}] {r.title}")

    print("\n=== Retrieval test: 'database transaction ACID' ===")
    results = knowledge.retrieve("database transaction ACID", limit=3)
    for r in results:
        print(f"  [{r.specialty_id}] {r.title}")

    print("\n=== Retrieval test: 'neural network training' ===")
    results = knowledge.retrieve("neural network training", limit=3)
    for r in results:
        print(f"  [{r.specialty_id}] {r.title}")

    print("\nDone.")


if __name__ == "__main__":
    main()
