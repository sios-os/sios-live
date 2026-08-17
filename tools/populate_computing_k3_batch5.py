#!/usr/bin/env python3
"""Populate Computing K3 content - Batch 5 (final)."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth, SourceTier
from anubis.knowledge import KnowledgeBase, PopulationPipeline
from anubis.knowledge_content.computing_k3_batch5 import COMPUTING_K3_BATCH5


def main() -> None:
    root = Path(".")
    registry = Registry(root / "registry")
    knowledge = KnowledgeBase(root / "knowledge", registry)
    pipeline = PopulationPipeline(registry, knowledge)

    src_id = "src_sios_computing_k3"
    print("=== K3 Batch 5 (final): Remaining 13 specialties ===\n")
    total_promoted = 0
    for spec_id, docs in COMPUTING_K3_BATCH5.items():
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

    for spec_id in COMPUTING_K3_BATCH5:
        registry.update_specialty_depth(spec_id, KnowledgeDepth.K3)

    print(f"\nTotal K3 batch 5 documents promoted: {total_promoted}")

    # Final verification
    print("\n=== FINAL VERIFICATION ===")
    kstats = knowledge.stats()
    print(f"Library docs total: {kstats['library_size']}")
    print(f"Quarantine docs: {kstats['quarantine_size']}")
    print(f"Total claims: {kstats['total_claims']}")
    rstats = registry.stats()
    print(f"Depth distribution: {rstats['depth_distribution']}")

    # Count K3 specialties
    k3_count = sum(1 for s in registry.specialties() if s.knowledge_depth >= KnowledgeDepth.K3)
    k1_count = sum(1 for s in registry.specialties() if s.knowledge_depth == KnowledgeDepth.K1)
    k0_count = sum(1 for s in registry.specialties() if s.knowledge_depth == KnowledgeDepth.K0)
    print(f"\nComputing director status:")
    print(f"  K3 (advanced): {k3_count} specialties")
    print(f"  K1 (oriented): {k1_count} specialties")
    print(f"  K0 (registered): {k0_count} specialties")

    # Test retrievals
    print("\n=== Retrieval tests ===")
    queries = [
        "Python pytest testing",
        "SQL database query optimization",
        "neural network training PyTorch",
        "Docker Kubernetes deployment",
        "Linux system administration",
        "quantum computing qubit",
        "Godot game development",
        "cryptography AES encryption",
    ]
    for q in queries:
        results = knowledge.retrieve(q, limit=2)
        print(f"\n  '{q}':")
        for r in results:
            print(f"    [{r.specialty_id}] {r.title}")

    print("\nDone. All Computing specialties populated to K3.")


if __name__ == "__main__":
    main()
