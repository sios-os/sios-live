#!/usr/bin/env python3
"""Populate Computing K3 content - Batch 1.

Covers: computer_science, software_engineering, software_architecture,
operating_systems, databases_information_systems
"""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth, SourceTier, SourceRecord
from anubis.knowledge import KnowledgeBase, PopulationPipeline
from anubis.knowledge_content.computing_k3_batch1 import COMPUTING_K3_BATCH1


def main() -> None:
    root = Path(".")
    registry = Registry(root / "registry")
    knowledge = KnowledgeBase(root / "knowledge", registry)
    pipeline = PopulationPipeline(registry, knowledge)

    src_id = "src_sios_computing_k3"
    if registry.get_source(src_id) is None:
        registry.register_source(SourceRecord(
            source_id=src_id,
            name="SIOS Computing K3 Advanced",
            publisher="SIOS",
            tier=SourceTier.T3,
            source_class=0,
            license="CC0",
            copyright_owner="SIOS",
            permitted_uses=["reference", "retrieval"],
            attribution_required=False,
            redistribution_allowed=True,
            training_allowed=True,
            status="trusted",
        ))

    print("=== K3 Batch 1: Core programming ===\n")
    total_promoted = 0
    for spec_id, docs in COMPUTING_K3_BATCH1.items():
        spec = registry.get_specialty(spec_id)
        if spec is None:
            print(f"  SKIP {spec_id}: not in registry")
            continue
        for d in docs:
            d.setdefault("source_id", src_id)
            d.setdefault("license", "CC0")
            d.setdefault("trust_tier", SourceTier.T3)
            d.setdefault("verification_notes", "Creator-approved K3 advanced")
        result = pipeline.populate_specialty(spec_id, docs, creator_approved=True)
        promoted = result.get("promoted", 0)
        total_promoted += promoted
        print(f"  {spec_id}: +{promoted} docs (total now {sum(1 for d in knowledge.library_documents() if d.specialty_id == spec_id)})")

    print(f"\nTotal K3 batch 1 documents promoted: {total_promoted}")

    # Update depth to K3 for these specialties
    for spec_id in COMPUTING_K3_BATCH1:
        registry.update_specialty_depth(spec_id, KnowledgeDepth.K3)

    print("\n=== Verification ===")
    kstats = knowledge.stats()
    print(f"Library docs: {kstats['library_size']}")
    rstats = registry.stats()
    print(f"Depth distribution: {rstats['depth_distribution']}")

    print("\n=== Retrieval test: 'SOLID principles' ===")
    for r in knowledge.retrieve("SOLID principles", limit=3):
        print(f"  [{r.specialty_id}] {r.title}")

    print("\n=== Retrieval test: 'SQL index optimization' ===")
    for r in knowledge.retrieve("SQL index optimization", limit=3):
        print(f"  [{r.specialty_id}] {r.title}")

    print("\n=== Retrieval test: 'dynamic programming memoization' ===")
    for r in knowledge.retrieve("dynamic programming memoization", limit=3):
        print(f"  [{r.specialty_id}] {r.title}")

    print("\nDone.")


if __name__ == "__main__":
    main()
