#!/usr/bin/env python3
"""Exercise the Court with a mock Main Engine change."""
import sys
sys.path.insert(0, ".")
import hashlib
from pathlib import Path
from anubis.governance import Court, CourtVerdict

court = Court(Path("court"))

print("=== COURT EXERCISE: Model Upgrade ===")
print()

# Simulate a Main Engine change: upgrading from qwen2.5-coder:7b to qwen2.5-coder:14b
artifact = "model_upgrade_qwen25_coder_14b_v1"
artifact_hash = hashlib.sha256(artifact.encode()).hexdigest()
description = "Upgrade ANUBIS model from qwen2.5-coder:7b to qwen2.5-coder:14b for improved code generation"

print(f"  Artifact: {artifact}")
print(f"  Hash: {artifact_hash[:24]}...")
print(f"  Description: {description}")
print()

# Step 1: Submit for review
print("--- Step 1: Submit for Court review ---")
review_id = court.submit_for_review(artifact_hash, description)
print(f"  Review ID: {review_id}")
print(f"  Status: submitted")
print()

# Step 2: Court renders verdict (PROBATION — cautious approach)
print("--- Step 2: Court renders verdict ---")
ok = court.render_verdict(
    review_id,
    CourtVerdict.PROBATION,
    conditions=[
        "must pass all 149 unit tests",
        "must maintain sandbox isolation",
        "must not degrade response quality",
        "rollback plan required",
    ],
    probation_days=30,
)
print(f"  Verdict: PROBATION (30 days)")
print(f"  Conditions:")
for c in court.get_review(review_id).conditions:
    print(f"    - {c}")
print()

# Step 3: Check promotion status before Creator approval
print("--- Step 3: Check promotion (before Creator approval) ---")
status = court.can_promote(review_id)
print(f"  Can promote: {status['can_promote']}")
print(f"  Reason: {status.get('reason', 'n/a')}")
print()

# Step 4: Creator (Storm) grants approval
print("--- Step 4: Creator grants approval ---")
result = court.grant_creator_approval(review_id, artifact_hash)
print(f"  Result: {result}")
print()

# Step 5: Check promotion status after Creator approval
print("--- Step 5: Check promotion (after Creator approval, during probation) ---")
status = court.can_promote(review_id)
print(f"  Can promote: {status['can_promote']}")
print(f"  Reason: {status.get('reason', 'ready')}")
print()

# Step 6: Show Court stats
print("--- Step 6: Court stats ---")
stats = court.stats()
print(f"  Total reviews: {stats['total_reviews']}")
print(f"  Verdict distribution: {stats['verdict_distribution']}")
print(f"  Creator approved: {stats['creator_approved']}")
print(f"  On probation: {stats['on_probation']}")
print()

# Step 7: Show all reviews
print("--- Step 7: All Court reviews ---")
for r in court.reviews():
    print(f"  {r.review_id[:16]}... | {CourtVerdict(r.verdict).name} | approved={r.creator_approved} | {r.description[:60]}")
print()

print("=== COURT EXERCISE COMPLETE ===")
print()
print("The Court is now functional. Main Engine changes require:")
print("  1. Court review (verdict: approved/probation/rejected/deferred)")
print("  2. Creator approval bound to exact artifact hash")
print("  3. Probation period (30 days) before full promotion")
print("  4. Rollback capability if problems emerge")
