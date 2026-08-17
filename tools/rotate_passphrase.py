#!/usr/bin/env python3
"""Rotate the Creator vault passphrase."""
import sys
import secrets
import string
sys.path.insert(0, ".")
from pathlib import Path
from anubis.identity import IdentityService

ROOT = Path(".")
identity = IdentityService(ROOT / "identity")

# Read old passphrase from environment (set by the caller)
import os
old_pass = os.environ.get("OLD_PASSPHRASE", "")
if not old_pass:
    print("ERROR: OLD_PASSPHRASE environment variable not set")
    sys.exit(1)

# Generate a new random passphrase
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
new_pass = "".join(secrets.choice(alphabet) for _ in range(24))

# Rotate
ok = identity.rotate_vault_passphrase(old_pass, new_pass)
if ok:
    print("PASSPHRASE ROTATED SUCCESSFULLY")
    print()
    print(f"New passphrase: {new_pass}")
    print()
    print("STORE THIS SECURELY. It will not be shown again.")
    print("The old passphrase no longer works.")

    # Verify the new passphrase works
    ok2 = identity.unlock_vault(new_pass)
    if ok2:
        keys = identity.vault_keys()
        print(f"Vault unlocked with new passphrase. {len(keys)} keys present.")
    else:
        print("WARNING: New passphrase failed verification!")
else:
    print("ERROR: Old passphrase is incorrect. Rotation failed.")
    sys.exit(1)
