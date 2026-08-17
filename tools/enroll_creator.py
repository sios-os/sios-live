#!/usr/bin/env python3
"""Enroll the Creator identity."""
import sys
sys.path.insert(0, ".")
import secrets
import string
from pathlib import Path
from anubis.identity import IdentityService

identity = IdentityService(Path("identity"))

if identity.is_enrolled():
    creator = identity.get_creator()
    print(f"Creator already enrolled: {creator.display_name}")
    print(f"Stats: {identity.stats()}")
    sys.exit(0)

# Generate a random passphrase
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
passphrase = "".join(secrets.choice(alphabet) for _ in range(20))

result = identity.enroll_creator(
    display_name="Storm",
    passphrase=passphrase,
    preferred_name="Storm",
)

if "error" in result:
    print(f"ERROR: {result['error']}")
    sys.exit(1)

print("=== CREATOR ENROLLED ===")
print(f"  Display name: {result['display_name']}")
print(f"  Creator ID:   {result['creator_id']}")
print(f"  Enrolled at:  {result['enrolled_at']}")
print()
print("=== VAULT PASSPHRASE (SAVE THIS — shown once) ===")
print(f"  {passphrase}")
print()
print("This passphrase encrypts your identity vault.")
print("Store it somewhere safe. Without it, the vault cannot be unlocked.")
print()
print(f"Identity stats: {identity.stats()}")
