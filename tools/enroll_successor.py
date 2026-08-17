#!/usr/bin/env python3
"""Enroll a successor for the Creator."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.identity import IdentityService

identity = IdentityService(Path("identity"))

if not identity.is_enrolled():
    print("ERROR: No active Creator enrolled. Enroll the Creator first.")
    sys.exit(1)

creator = identity.get_creator()
print(f"Creator: {creator.display_name} ({creator.creator_id})")
print()

result = identity.enroll_successor(
    display_name="Ethan Pace",
    relationship="Family",
    activation_conditions=[
        "creator_willing_revocation",
        "creator_unreachable_90d",
        "verified_death",
    ],
)

if "error" in result:
    print(f"ERROR: {result['error']}")
    sys.exit(1)

print("=== SUCCESSOR ENROLLED ===")
print(f"  Name:       Ethan Pace")
print(f"  Relationship: Family")
print(f"  Successor ID: {result['successor_id']}")
print(f"  Status:     {result['status']}")
print()
print("  Activation conditions:")
print("    1. Creator willing revocation")
print("    2. Creator unreachable for 90 days")
print("    3. Verified death")
print()
print("  NOTE: The successor must independently consent before they can activate.")
print("  Use give_successor_consent() when Ethan is ready to accept.")
print()

# Show updated stats
stats = identity.stats()
print(f"Identity stats: {stats}")
print()
print("Successors:")
for s in identity.successors():
    print(f"  {s.display_name} ({s.successor_id[:16]}...)")
    print(f"    Relationship: {s.relationship}")
    print(f"    Consent given: {s.consent_given}")
    print(f"    Activation: {', '.join(s.activation_conditions)}")
