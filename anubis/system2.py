"""SIOS A/B Image Management and Egyptology Support.

Implements Phases 13, 27, and the Egyptology director from the KBP plan:

A/B System Images (Phases 13, 27):
  - Two system slots (A and B) for atomic updates
  - Promotion from inactive slot to active
  - Probation period before full commit
  - Rollback to previous slot on failure
  - Identity and knowledge stores remain independent of A/B slots

Egyptology Director:
  - Hieroglyphic corpus support
  - Sign lists (Gardiner, Manuel de Codage)
  - transliteration support
  - Basic dictionary lookup
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ A/B Images

class SlotStatus(IntEnum):
    INACTIVE = 0      # Not the current boot slot
    ACTIVE = 1        # Current boot slot
    PROBATION = 2     # Active but under probation
    FAILED = 3        # Marked as failed
    UPDATING = 4      # Being updated with new image


@dataclass
class SystemSlot:
    """A system image slot (A or B)."""
    slot_id: str  # "A" or "B"
    version: str = ""
    image_hash: str = ""
    status: int = SlotStatus.INACTIVE
    installed_at: float = 0.0
    last_booted: float = 0.0
    boot_count: int = 0
    probation_until: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "version": self.version,
            "image_hash": self.image_hash,
            "status": SlotStatus(self.status).name,
            "installed_at": self.installed_at,
            "last_booted": self.last_booted,
            "boot_count": self.boot_count,
            "probation_until": self.probation_until,
            "notes": self.notes,
        }


class ABImageManager:
    """Manages A/B system image slots.

    SIOS uses two system slots for atomic updates:
      - Slot A: The currently active system
      - Slot B: The inactive slot used for updates

    When updating:
      1. Write the new image to the inactive slot
      2. Set the inactive slot to PROBATION
      3. Boot from the new slot
      4. If it boots successfully and passes probation, commit
      5. If it fails, roll back to the previous slot

    Identity and knowledge stores are on a separate partition
    that is independent of both A/B slots.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._slots_file = self.root / "ab_slots.json"
        self._slots: dict[str, SystemSlot] = {}
        self._history: list[dict[str, Any]] = []
        self._load()
        # Initialize slots if empty
        if not self._slots:
            self._slots["A"] = SystemSlot(slot_id="A", status=SlotStatus.ACTIVE, installed_at=time.time())
            self._slots["B"] = SystemSlot(slot_id="B", status=SlotStatus.INACTIVE)
            self._save()

    def _load(self) -> None:
        if self._slots_file.exists():
            data = json.loads(self._slots_file.read_text(encoding="utf-8"))
            for s in data.get("slots", []):
                self._slots[s["slot_id"]] = SystemSlot(
                    slot_id=s["slot_id"], version=s.get("version", ""),
                    image_hash=s.get("image_hash", ""),
                    status=s.get("status", SlotStatus.INACTIVE),
                    installed_at=s.get("installed_at", 0),
                    last_booted=s.get("last_booted", 0),
                    boot_count=s.get("boot_count", 0),
                    probation_until=s.get("probation_until", 0),
                    notes=s.get("notes", ""),
                )
            self._history = data.get("history", [])

    def _save(self) -> None:
        self._slots_file.write_text(
            json.dumps({
                "slots": [s.to_dict() for s in self._slots.values()],
                "history": self._history,
            }, indent=2) + "\n",
            encoding="utf-8",
        )

    def get_active_slot(self) -> SystemSlot:
        """Get the currently active slot."""
        for slot in self._slots.values():
            if slot.status in (SlotStatus.ACTIVE, SlotStatus.PROBATION):
                return slot
        return self._slots["A"]

    def get_inactive_slot(self) -> SystemSlot:
        """Get the inactive slot for updates."""
        active = self.get_active_slot()
        for slot_id in self._slots:
            if slot_id != active.slot_id:
                return self._slots[slot_id]
        return self._slots["B"]

    def update_inactive_slot(self, version: str, image_hash: str) -> dict[str, Any]:
        """Write a new image to the inactive slot and set to probation."""
        inactive = self.get_inactive_slot()
        inactive.version = version
        inactive.image_hash = image_hash
        inactive.status = SlotStatus.UPDATING
        inactive.installed_at = time.time()
        self._history.append({
            "action": "update", "slot": inactive.slot_id,
            "version": version, "timestamp": time.time(),
        })
        self._save()
        return {"slot": inactive.slot_id, "version": version, "status": "updating"}

    def promote(self, probation_days: int = 7) -> dict[str, Any]:
        """Promote the inactive slot to active with probation."""
        active = self.get_active_slot()
        inactive = self.get_inactive_slot()
        # Old active becomes inactive
        active.status = SlotStatus.INACTIVE
        # New slot becomes probation
        inactive.status = SlotStatus.PROBATION
        inactive.probation_until = time.time() + (probation_days * 86400)
        inactive.last_booted = time.time()
        inactive.boot_count += 1
        self._history.append({
            "action": "promote", "slot": inactive.slot_id,
            "probation_days": probation_days, "timestamp": time.time(),
        })
        self._save()
        return {"new_active": inactive.slot_id, "probation_until": inactive.probation_until}

    def commit(self) -> dict[str, Any]:
        """Commit the probation slot to full active status."""
        for slot in self._slots.values():
            if slot.status == SlotStatus.PROBATION:
                slot.status = SlotStatus.ACTIVE
                slot.probation_until = 0
                self._history.append({
                    "action": "commit", "slot": slot.slot_id,
                    "timestamp": time.time(),
                })
                self._save()
                return {"slot": slot.slot_id, "status": "active"}
        return {"error": "no slot in probation"}

    def rollback(self) -> dict[str, Any]:
        """Roll back to the inactive slot (previous active)."""
        active = self.get_active_slot()
        inactive = self.get_inactive_slot()
        # Current active becomes failed
        active.status = SlotStatus.FAILED
        # Inactive becomes active
        inactive.status = SlotStatus.ACTIVE
        inactive.last_booted = time.time()
        inactive.boot_count += 1
        self._history.append({
            "action": "rollback", "from": active.slot_id,
            "to": inactive.slot_id, "timestamp": time.time(),
        })
        self._save()
        return {"rolled_back_to": inactive.slot_id}

    def slots(self) -> list[SystemSlot]:
        return list(self._slots.values())

    def stats(self) -> dict[str, Any]:
        active = self.get_active_slot()
        return {
            "active_slot": active.slot_id,
            "active_version": active.version,
            "active_status": active.status.name if hasattr(active.status, 'name') else str(active.status),
            "total_boots": sum(s.boot_count for s in self._slots.values()),
            "history_entries": len(self._history),
        }


# ------------------------------------------------------------------ Egyptology

# Basic Gardiner sign list (subset)
GARDINER_SIGNS: dict[str, dict[str, str]] = {
    "A1": {"sign": "𓀀", "category": "A", "description": "seated man", "transliteration": ""},
    "A2": {"sign": "𓀁", "category": "A", "description": "seated man with hand to mouth", "transliteration": ""},
    "A3": {"sign": "𓀂", "category": "A", "description": "seated man eating", "transliteration": ""},
    "D21": {"sign": "𓂋", "category": "D", "description": "mouth", "transliteration": "r"},
    "D36": {"sign": "𓂝", "category": "D", "description": "forearm", "transliteration": "ˁ"},
    "D46": {"sign": "𓂧", "category": "D", "description": "hand", "transliteration": "d"},
    "F1": {"sign": "𓃒", "category": "F", "description": "horned viper", "transliteration": "f"},
    "G1": {"sign": "𓄿", "category": "G", "description": "Egyptian vulture", "transliteration": "ꜣ"},
    "G17": {"sign": "𓅓", "category": "G", "description": "owl", "transliteration": "m"},
    "G43": {"sign": "𓅱", "category": "G", "description": "quail chick", "transliteration": "w"},
    "M1": {"sign": "𓇅", "category": "M", "description": "reed", "transliteration": "i"},
    "M17": {"sign": "𓇋", "category": "M", "description": "reed", "transliteration": "i"},
    "N1": {"sign": "𓇳", "category": "N", "description": "sun", "transliteration": "rꜥ"},
    "N5": {"sign": "𓇳", "category": "N", "description": "sun (variant)", "transliteration": ""},
    "N35": {"sign": "𓈖", "category": "N", "description": "water", "transliteration": "n"},
    "O1": {"sign": "𓉐", "category": "O", "description": "house", "transliteration": "pr"},
    "O4": {"sign": "𓉤", "category": "O", "description": "placenta", "transliteration": "ḫ"},
    "Q1": {"sign": "𓏏", "category": "Q", "description": "bread", "transliteration": "t"},
    "Q3": {"sign": "𓏤", "category": "Q", "description": "sieve", "transliteration": ""},
    "S29": {"sign": "𓋴", "category": "S", "description": "folded cloth", "transliteration": "s"},
    "T22": {"sign": "𓏎", "category": "T", "description": "reed pen", "transliteration": ""},
    "U1": {"sign": "𓌅", "category": "U", "description": "sickle", "transliteration": "mꜣ"},
    "V1": {"sign": "𓏲", "category": "V", "description": "rope coil", "transliteration": "šn"},
    "X1": {"sign": "𓏡", "category": "X", "description": "bread loaf", "transliteration": "t"},
    "Z1": {"sign": "𓏤", "category": "Z", "description": "stroke", "transliteration": ""},
    "Z2": {"sign": "𓏥", "category": "Z", "description": "three strokes", "transliteration": ""},
    "AA1": {"sign": "𓀀", "category": "AA", "description": "seated child", "transliteration": ""},
}

# Basic dictionary — common Middle Egyptian words
EGYPTIAN_DICTIONARY: dict[str, dict[str, str]] = {
    "nsw": {"translation": "king", "part_of_speech": "noun", "period": "Old-Middle Egyptian"},
    "nb": {"translation": "lord, master, all", "part_of_speech": "noun/adjective", "period": "all periods"},
    "pr": {"translation": "house, estate", "part_of_speech": "noun", "period": "all periods"},
    "rꜥ": {"translation": "sun, Re", "part_of_speech": "noun", "period": "all periods"},
    "ꜥnḫ": {"translation": "life, to live", "part_of_speech": "noun/verb", "period": "all periods"},
    "mꜣꜥ": {"translation": "true, real, just", "part_of_speech": "adjective", "period": "all periods"},
    "ḥr": {"translation": "Horus, face, upon", "part_of_speech": "noun/preposition", "period": "all periods"},
    "ỉmn": {"translation": "Amun, hidden", "part_of_speech": "noun/adjective", "period": "Middle-Late Egyptian"},
    "wsir": {"translation": "Osiris", "part_of_speech": "noun", "period": "all periods"},
    "ỉnb": {"translation": "wall, fortress", "part_of_speech": "noun", "period": "all periods"},
    "ḏd": {"translation": "to say, speak", "part_of_speech": "verb", "period": "all periods"},
    "rn": {"translation": "name", "part_of_speech": "noun", "period": "all periods"},
    "kꜣ": {"translation": "ka (spirit), bull", "part_of_speech": "noun", "period": "all periods"},
    "bꜣ": {"translation": "ba (soul)", "part_of_speech": "noun", "period": "all periods"},
    "ꜥḥꜥ": {"translation": "to stand, stand", "part_of_speech": "verb", "period": "all periods"},
    "sḫr": {"translation": "to strike, defeat", "part_of_speech": "verb", "period": "all periods"},
    "nfr": {"translation": "good, beautiful", "part_of_speech": "adjective", "period": "all periods"},
    "dwꜣ": {"translation": "to adore, praise", "part_of_speech": "verb", "period": "all periods"},
    "ỉrt": {"translation": "eye, to do", "part_of_speech": "noun/verb", "period": "all periods"},
    "stp": {"translation": "to choose, select", "part_of_speech": "verb", "period": "all periods"},
}


class EgyptologySupport:
    """Egyptology and hieroglyphic corpus support.

    Provides:
      - Gardiner sign lookup
      - Basic dictionary lookup
      - Transliteration display
      - Sign category browsing

    This is a starting point. Full corpus integration (Thesaurus
    Linguae Aegyptiae, Ramses Online, JSesh) requires network access
    and is governed by the network policy.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def lookup_sign(self, gardiner_code: str) -> dict[str, Any]:
        """Look up a hieroglyphic sign by Gardiner code."""
        code = gardiner_code.upper().strip()
        sign = GARDINER_SIGNS.get(code)
        if sign is None:
            return {"error": f"unknown Gardiner code: {code}"}
        return {"code": code, **sign}

    def lookup_word(self, transliteration: str) -> dict[str, Any]:
        """Look up a word in the Egyptian dictionary."""
        translit = transliteration.lower().strip()
        entry = EGYPTIAN_DICTIONARY.get(translit)
        if entry is None:
            return {"error": f"word not found: {translit}"}
        return {"transliteration": translit, **entry}

    def signs_by_category(self, category: str) -> list[dict[str, Any]]:
        """List all signs in a category."""
        category = category.upper().strip()
        results = []
        for code, sign in GARDINER_SIGNS.items():
            if sign["category"] == category:
                results.append({"code": code, **sign})
        return results

    def categories(self) -> list[str]:
        """List all sign categories."""
        return sorted(set(s["category"] for s in GARDINER_SIGNS.values()))

    def dictionary_entries(self) -> list[dict[str, Any]]:
        """List all dictionary entries."""
        return [
            {"transliteration": k, **v}
            for k, v in sorted(EGYPTIAN_DICTIONARY.items())
        ]

    def search_dictionary(self, query: str) -> list[dict[str, Any]]:
        """Search the dictionary by translation or transliteration."""
        query = query.lower().strip()
        results = []
        for translit, entry in EGYPTIAN_DICTIONARY.items():
            if query in translit.lower() or query in entry["translation"].lower():
                results.append({"transliteration": translit, **entry})
        return results

    def stats(self) -> dict[str, Any]:
        return {
            "total_signs": len(GARDINER_SIGNS),
            "total_words": len(EGYPTIAN_DICTIONARY),
            "categories": len(self.categories()),
        }
