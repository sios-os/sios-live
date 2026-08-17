#!/usr/bin/env python3
"""Record successor consent."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.identity import IdentityService

identity = IdentityService(Path("identity"))

successors = identity.successors()
if not successors:
    print("ERROR: No successors enrolled.")
    sys.exit(1)

print("Successors:")
for s in successors:
    print(f"  {s.display_name} ({s.successor_id[:16]}...) consent={s.consent_given}")
print()

# Record consent for Ethan
ethan = successors[0]
print(f"Recording consent for {ethan.display_name}...")
identity.give_successor_consent(ethan.successor_id)

print()
print("=== CONSENT RECORDED ===")
for s in identity.successors():
    print(f"  {s.display_name} — consent: {s.consent_given} (at: {s.consent_at})")
print()
print(f"Identity stats: {identity.stats()}")
