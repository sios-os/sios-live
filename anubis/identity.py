"""SIOS Identity Service.

Implements Phase 21 of the 50-Phase Build Plan:
  - Creator enrollment (one-time)
  - Successor enrollment and acceptance
  - Identity vault (encrypted local storage)
  - Contact continuity and lawful recovery ladder
  - Enrollment acceptance gates

The identity service is the foundation for all authority in SIOS.
No component grants itself authority — authority is derived from
the Creator's enrolled identity and explicit consent.

Security notes:
  - Credentials are stored encrypted at rest using a local key
  - The local key is derived from a passphrase set during enrollment
  - No credentials are ever exposed to ANUBIS, DEMON, models, or agents
  - No SSN is collected
  - No covert tracking or unauthorized location access
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CreatorIdentity:
    """The Creator's enrolled identity."""
    creator_id: str
    display_name: str = ""
    enrolled_at: float = 0.0
    enrollment_version: str = "1.0"
    # Recovery
    recovery_contacts: list[dict[str, str]] = field(default_factory=list)
    recovery_ladder: list[str] = field(default_factory=list)
    # Preferences
    preferred_name: str = ""
    language: str = "en"
    accessibility_needs: list[str] = field(default_factory=list)
    # Status
    active: bool = True
    revoked: bool = False
    last_active: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "creator_id": self.creator_id,
            "display_name": self.display_name,
            "enrolled_at": self.enrolled_at,
            "enrollment_version": self.enrollment_version,
            "recovery_contacts": self.recovery_contacts,
            "recovery_ladder": self.recovery_ladder,
            "preferred_name": self.preferred_name,
            "language": self.language,
            "accessibility_needs": self.accessibility_needs,
            "active": self.active,
            "revoked": self.revoked,
            "last_active": self.last_active,
        }


@dataclass
class SuccessorIdentity:
    """A successor who may inherit control under defined conditions."""
    successor_id: str
    display_name: str = ""
    relationship: str = ""
    enrolled_at: float = 0.0
    consent_given: bool = False
    consent_at: float = 0.0
    activation_conditions: list[str] = field(default_factory=list)
    active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "successor_id": self.successor_id,
            "display_name": self.display_name,
            "relationship": self.relationship,
            "enrolled_at": self.enrolled_at,
            "consent_given": self.consent_given,
            "consent_at": self.consent_at,
            "activation_conditions": self.activation_conditions,
            "active": self.active,
        }


class IdentityVault:
    """Encrypted local storage for credentials and secrets.

    Uses a simple encryption scheme derived from a passphrase.
    This is NOT a substitute for proper hardware-backed encryption
    in a production system, but provides local-only protection
    for the private Creator edition.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._vault_file = self.root / "vault.enc"
        self._key: bytes | None = None
        self._data: dict[str, Any] = {}

    def _derive_key(self, passphrase: str) -> bytes:
        """Derive an encryption key from a passphrase."""
        salt = b"sios_identity_vault_v1"
        return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100000, 32)

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption (obfuscation at rest)."""
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def unlock(self, passphrase: str) -> bool:
        """Unlock the vault with a passphrase."""
        self._key = self._derive_key(passphrase)
        if self._vault_file.exists():
            encrypted = self._vault_file.read_bytes()
            decrypted = self._xor_encrypt(encrypted, self._key)
            try:
                self._data = json.loads(decrypted.decode("utf-8"))
                return True
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._key = None
                return False
        else:
            # New vault
            self._data = {}
            return True

    def lock(self) -> None:
        """Lock the vault."""
        self._key = None
        self._data = {}

    def rotate_passphrase(self, old_passphrase: str, new_passphrase: str) -> bool:
        """Rotate the vault passphrase. Requires the old passphrase.

        Decrypts with the old key, re-encrypts with the new key.
        Returns True on success, False if old passphrase is wrong.
        """
        if not self.unlock(old_passphrase):
            return False
        # Save data with old key, then re-encrypt with new key
        data = self._data
        old_key = self._key
        new_key = self._derive_key(new_passphrase)
        encrypted = self._xor_encrypt(
            json.dumps(data, indent=2).encode("utf-8"), new_key
        )
        self._vault_file.write_bytes(encrypted)
        self._key = new_key
        self._data = data
        return True

    def is_unlocked(self) -> bool:
        return self._key is not None

    def store(self, key: str, value: Any) -> bool:
        """Store a value in the vault."""
        if not self.is_unlocked():
            return False
        self._data[key] = value
        self._save()
        return True

    def retrieve(self, key: str) -> Any:
        """Retrieve a value from the vault."""
        if not self.is_unlocked():
            return None
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        """Delete a value from the vault."""
        if not self.is_unlocked():
            return False
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def keys(self) -> list[str]:
        """List all keys in the vault."""
        if not self.is_unlocked():
            return []
        return list(self._data.keys())

    def _save(self) -> None:
        """Save the vault to disk (encrypted)."""
        if not self.is_unlocked():
            return
        data = json.dumps(self._data, indent=2).encode("utf-8")
        encrypted = self._xor_encrypt(data, self._key)
        self._vault_file.write_bytes(encrypted)
        os.chmod(self._vault_file, 0o600)


class IdentityService:
    """The SIOS identity service.

    Manages Creator enrollment, successor enrollment, and the
    identity vault. All authority in SIOS derives from the
    enrolled Creator identity.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._identity_file = self.root / "identity.json"
        self._successors_file = self.root / "successors.json"
        self._vault = IdentityVault(self.root / "vault")
        self._creator: CreatorIdentity | None = None
        self._successors: dict[str, SuccessorIdentity] = {}
        self._load()

    def _load(self) -> None:
        """Load identity from disk."""
        if self._identity_file.exists():
            data = json.loads(self._identity_file.read_text(encoding="utf-8"))
            self._creator = CreatorIdentity(
                creator_id=data.get("creator_id", ""),
                display_name=data.get("display_name", ""),
                enrolled_at=data.get("enrolled_at", 0.0),
                enrollment_version=data.get("enrollment_version", "1.0"),
                recovery_contacts=data.get("recovery_contacts", []),
                recovery_ladder=data.get("recovery_ladder", []),
                preferred_name=data.get("preferred_name", ""),
                language=data.get("language", "en"),
                accessibility_needs=data.get("accessibility_needs", []),
                active=data.get("active", True),
                revoked=data.get("revoked", False),
                last_active=data.get("last_active", 0.0),
            )
        if self._successors_file.exists():
            for s in json.loads(self._successors_file.read_text(encoding="utf-8")):
                succ = SuccessorIdentity(
                    successor_id=s.get("successor_id", ""),
                    display_name=s.get("display_name", ""),
                    relationship=s.get("relationship", ""),
                    enrolled_at=s.get("enrolled_at", 0.0),
                    consent_given=s.get("consent_given", False),
                    consent_at=s.get("consent_at", 0.0),
                    activation_conditions=s.get("activation_conditions", []),
                    active=s.get("active", False),
                )
                self._successors[succ.successor_id] = succ

    def _save(self) -> None:
        """Save identity to disk."""
        if self._creator:
            self._identity_file.write_text(
                json.dumps(self._creator.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
            os.chmod(self._identity_file, 0o600)
        self._successors_file.write_text(
            json.dumps([s.to_dict() for s in self._successors.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(self._successors_file, 0o600)

    # ------------------------------------------------------------------ enrollment

    def enroll_creator(
        self, display_name: str, passphrase: str,
        preferred_name: str = "", recovery_contacts: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Enroll the Creator. This is a one-time operation.

        Enrollment gates:
          - Cannot enroll if a Creator already exists and is active
          - Passphrase must be at least 8 characters
          - Display name must not be empty
        """
        if self._creator is not None and self._creator.active and not self._creator.revoked:
            return {"error": "Creator already enrolled. Use correction or revocation."}
        if not display_name.strip():
            return {"error": "Display name required"}
        if len(passphrase) < 8:
            return {"error": "Passphrase must be at least 8 characters"}

        creator_id = hashlib.sha256(
            f"creator:{display_name}:{time.time()}".encode()
        ).hexdigest()[:16]

        self._creator = CreatorIdentity(
            creator_id=creator_id,
            display_name=display_name.strip(),
            enrolled_at=time.time(),
            preferred_name=preferred_name or display_name.strip(),
            recovery_contacts=recovery_contacts or [],
            recovery_ladder=["creator_passphrase", "recovery_contacts", "successor"],
            last_active=time.time(),
        )

        # Initialize vault
        self._vault.unlock(passphrase)
        self._vault.store("creator_id", creator_id)
        self._vault.store("enrolled_at", self._creator.enrolled_at)

        self._save()
        return {
            "creator_id": creator_id,
            "display_name": self._creator.display_name,
            "enrolled_at": self._creator.enrolled_at,
            "status": "enrolled",
        }

    def is_enrolled(self) -> bool:
        """Check if a Creator is enrolled."""
        return self._creator is not None and self._creator.active and not self._creator.revoked

    def get_creator(self) -> CreatorIdentity | None:
        return self._creator

    def correct_creator(self, display_name: str = "", preferred_name: str = "") -> bool:
        """Correct Creator identity details (not the ID)."""
        if self._creator is None:
            return False
        if display_name:
            self._creator.display_name = display_name
        if preferred_name:
            self._creator.preferred_name = preferred_name
        self._save()
        return True

    def revoke_creator(self, confirmation: str) -> bool:
        """Revoke Creator identity. Requires explicit confirmation."""
        if self._creator is None:
            return False
        if confirmation != "REVOKE_CREATOR":
            return False
        self._creator.revoked = True
        self._creator.active = False
        self._save()
        return True

    def update_last_active(self) -> None:
        """Update the Creator's last active timestamp."""
        if self._creator:
            self._creator.last_active = time.time()
            self._save()

    # ------------------------------------------------------------------ successors

    def enroll_successor(
        self, display_name: str, relationship: str,
        activation_conditions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Enroll a potential successor."""
        if not self.is_enrolled():
            return {"error": "No active Creator to name a successor"}
        if not display_name.strip():
            return {"error": "Display name required"}
        successor_id = hashlib.sha256(
            f"successor:{display_name}:{time.time()}".encode()
        ).hexdigest()[:16]
        succ = SuccessorIdentity(
            successor_id=successor_id,
            display_name=display_name.strip(),
            relationship=relationship,
            enrolled_at=time.time(),
            activation_conditions=activation_conditions or ["creator_revoked", "creator_unreachable_90d"],
        )
        self._successors[successor_id] = succ
        self._save()
        return {"successor_id": successor_id, "status": "enrolled_pending_consent"}

    def give_successor_consent(self, successor_id: str) -> bool:
        """Record a successor's independent consent."""
        succ = self._successors.get(successor_id)
        if succ is None:
            return False
        succ.consent_given = True
        succ.consent_at = time.time()
        self._save()
        return True

    def successors(self) -> list[SuccessorIdentity]:
        return list(self._successors.values())

    # ------------------------------------------------------------------ vault

    def unlock_vault(self, passphrase: str) -> bool:
        """Unlock the identity vault."""
        return self._vault.unlock(passphrase)

    def rotate_vault_passphrase(self, old_passphrase: str, new_passphrase: str) -> bool:
        """Rotate the vault passphrase. Requires the old passphrase."""
        return self._vault.rotate_passphrase(old_passphrase, new_passphrase)

    def lock_vault(self) -> None:
        """Lock the identity vault."""
        self._vault.lock()

    def vault_store(self, key: str, value: Any) -> bool:
        """Store a credential in the vault."""
        return self._vault.store(key, value)

    def vault_retrieve(self, key: str) -> Any:
        """Retrieve a credential from the vault."""
        return self._vault.retrieve(key)

    def vault_keys(self) -> list[str]:
        """List vault keys (not values)."""
        return self._vault.keys()

    def vault_is_unlocked(self) -> bool:
        return self._vault.is_unlocked()

    # ------------------------------------------------------------------ stats

    def stats(self) -> dict[str, Any]:
        return {
            "enrolled": self.is_enrolled(),
            "creator_name": self._creator.display_name if self._creator else "",
            "enrolled_at": self._creator.enrolled_at if self._creator else 0,
            "successors": len(self._successors),
            "consented_successors": sum(1 for s in self._successors.values() if s.consent_given),
            "vault_unlocked": self.vault_is_unlocked(),
            "vault_keys": len(self.vault_keys()),
        }
