#!/usr/bin/env python3
"""Populate Computing K3 content - Batch 4."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth, SourceTier
from anubis.knowledge import KnowledgeBase, PopulationPipeline
from anubis.knowledge_content.computing_k3_batch4 import COMPUTING_K3_BATCH4


def main() -> None:
    root = Path(".")
    registry = Registry(root / "registry")
    knowledge = KnowledgeBase(root / "knowledge", registry)
    pipeline = PopulationPipeline(registry, knowledge)

    src_id = "src_sios_computing_k3"
    print("=== K3 Batch 4: Game Dev, Embedded, QA, Distributed, Mobile, HCI ===\n")
    total_promoted = 0
    for spec_id, docs in COMPUTING_K3_BATCH4.items():
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
        print(f"  {spec_id}: +{promoted} docs")

    for spec_id in COMPUTING_K3_BATCH4:
        registry.update_specialty_depth(spec_id, KnowledgeDepth.K3)

    print(f"\nTotal K3 batch 4 documents promoted: {total_promoted}")
    kstats = knowledge.stats()
    print(f"Library docs total: {kstats['library_size']}")
    rstats = registry.stats()
    print(f"Depth distribution: {rstats['depth_distribution']}")

    print("\n=== Retrieval: 'Godot GDScript' ===")
    for r in knowledge.retrieve("Godot GDScript", limit=3):
        print(f"  [{r.specialty_id}] {r.title}")

    print("\n=== Retrieval: 'circuit breaker retry' ===")
    for r in knowledge.retrieve("circuit breaker retry", limit=3):
        print(f"  [{r.specialty_id}] {r.title}")

    print("\nDone.")


if __name__ == "__main__":
    main()
