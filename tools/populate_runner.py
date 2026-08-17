#!/usr/bin/env python3
"""Generic K1/K3 population runner for any director batch."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry, KnowledgeDepth, SourceTier, SourceRecord
from anubis.knowledge import KnowledgeBase, PopulationPipeline


def populate(module_name: str, data_attr: str, source_id: str, source_name: str, depth: int, depth_label: str) -> None:
    root = Path(".")
    registry = Registry(root / "registry")
    knowledge = KnowledgeBase(root / "knowledge", registry)
    pipeline = PopulationPipeline(registry, knowledge)

    if registry.get_source(source_id) is None:
        registry.register_source(SourceRecord(
            source_id=source_id, name=source_name, publisher="SIOS",
            tier=SourceTier.T3, source_class=0, license="CC0",
            copyright_owner="SIOS", permitted_uses=["reference", "retrieval"],
            attribution_required=False, redistribution_allowed=True,
            training_allowed=True, status="trusted",
        ))

    mod = __import__(module_name, fromlist=[data_attr])
    data = getattr(mod, data_attr)

    print(f"=== {depth_label} ===\n")
    total = 0
    for spec_id, docs in data.items():
        spec = registry.get_specialty(spec_id)
        if spec is None:
            print(f"  SKIP {spec_id}: not in registry")
            continue
        for d in docs:
            d.setdefault("source_id", source_id)
            d.setdefault("license", "CC0")
            d.setdefault("trust_tier", SourceTier.T3)
            d.setdefault("verification_notes", f"Creator-approved {depth_label}")
        result = pipeline.populate_specialty(spec_id, docs, creator_approved=True)
        promoted = result.get("promoted", 0)
        total += promoted
        print(f"  {spec_id}: +{promoted} docs")

    for spec_id in data:
        if registry.get_specialty(spec_id) and registry.get_specialty(spec_id).knowledge_depth < depth:
            registry.update_specialty_depth(spec_id, depth)

    kstats = knowledge.stats()
    rstats = registry.stats()
    print(f"\nPromoted: {total}")
    print(f"Library total: {kstats['library_size']}")
    print(f"Depth distribution: {rstats['depth_distribution']}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: populate_runner.py <module> <data_attr> <source_id> <source_name> <depth> <depth_label>")
        sys.exit(1)
    module = sys.argv[1]
    attr = sys.argv[2]
    sid = sys.argv[3]
    sname = sys.argv[4]
    depth = int(sys.argv[5])
    label = sys.argv[6]
    populate(module, attr, sid, sname, depth, label)
