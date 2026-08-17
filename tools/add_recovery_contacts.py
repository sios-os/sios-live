#!/usr/bin/env python3
"""Add recovery contacts to the Creator identity."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.identity import IdentityService

identity = IdentityService(Path("identity"))

if not identity.is_enrolled():
    print("ERROR: No active Creator enrolled.")
    sys.exit(1)

creator = identity.get_creator()
print(f"Creator: {creator.display_name}")
print()

# Add recovery contacts
contacts = [
    {"name": "Ethan Pace", "relationship": "Family", "method": "in_person"},
    {"name": "ANUBIS Vault Backup", "relationship": "System", "method": "encrypted_backup"},
]

creator.recovery_contacts = contacts
identity._save()

print("=== RECOVERY CONTACTS ADDED ===")
for i, c in enumerate(contacts):
    print(f"  {i+1}. {c['name']} ({c['relationship']}) — {c['method']}")
print()
print("Recovery ladder (in order):")
for i, step in enumerate(creator.recovery_ladder):
    print(f"  {i+1}. {step}")
print()
print(f"Identity stats: {identity.stats()}")
