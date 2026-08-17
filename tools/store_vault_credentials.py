#!/usr/bin/env python3
"""Store system credentials in the identity vault."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.identity import IdentityService

identity = IdentityService(Path("identity"))

# Unlock the vault with the generated passphrase
PASSPHRASE = "YgcgDo@zwEmgCBx&6y8$"

if not identity.unlock_vault(PASSPHRASE):
    print("ERROR: Could not unlock vault. Check passphrase.")
    sys.exit(1)

print("=== VAULT UNLOCKED ===")
print()

# Store SIOS system credentials and configuration
credentials = {
    "sios_creator_passphrase": PASSPHRASE,
    "sios_creator_id": "4670b4cf48fed7c5",
    "ollama_endpoint": "http://127.0.0.1:11434",
    "anubis_model": "qwen2.5-coder:7b",
    "anubis_socket": "/tmp/anubis.sock",
    "sios_root": "/opt/sios-live",
    "successor_id": "144f7f638118138b",
}

for key, value in credentials.items():
    ok = identity.vault_store(key, value)
    status = "stored" if ok else "failed"
    print(f"  {key}: {status}")

print()
print(f"Vault keys: {identity.vault_keys()}")
print(f"Vault unlocked: {identity.vault_is_unlocked()}")

# Lock the vault
identity.lock_vault()
print()
print("Vault locked. Credentials encrypted at rest.")
print()
print(f"Identity stats: {identity.stats()}")
