"""Emergency contacts and successor notification policy.

ANUBIS maintains an emergency contact list separate from the successor.
The successor (Ethan Pace) is notified ONLY in the confirmed
absence/takeover scenario — never for general emergencies.

Emergency contacts are for physical emergencies:
- Falls, medical events, injury
- Home intrusion while Creator is present
- Any situation requiring immediate human attention

The contact list has priority ordering — ANUBIS contacts people in
order until someone responds. Contacts can have roles (medical,
security, family, neighbor) and trusted status.

All contact attempts are logged to the evidence ledger.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EmergencyContact:
    """A person on the emergency contact list."""
    contact_id: str
    name: str
    phone: str = ""  # phone number for SMS/calls
    email: str = ""  # email for email-to-SMS or email alerts
    relationship: str = ""  # family, friend, neighbor, doctor, etc.
    role: str = ""  # medical, security, general, primary
    priority: int = 99  # 1 = highest priority, contacted first
    trusted: bool = False
    available: bool = True  # can be toggled off if someone is unavailable
    notes: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "relationship": self.relationship,
            "role": self.role,
            "priority": self.priority,
            "trusted": self.trusted,
            "available": self.available,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ContactAttempt:
    """Record of an attempt to contact someone."""
    attempt_id: str
    contact_id: str
    contact_name: str
    method: str = "sms"  # sms, call, email
    message: str = ""
    status: str = "pending"  # pending, sent, delivered, failed, responded
    timestamp: float = 0.0
    response: str = ""
    response_timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "contact_id": self.contact_id,
            "contact_name": self.contact_name,
            "method": self.method,
            "message": self.message,
            "status": self.status,
            "timestamp": self.timestamp,
            "response": self.response,
            "response_timestamp": self.response_timestamp,
        }


@dataclass
class SuccessorPolicy:
    """Strict policy for when the successor can be notified.

    The successor is ONLY notified when ALL of these conditions are met:
    1. Creator is confirmed absent (no activity for extended period)
    2. Creator is unresponsive to all contact attempts
    3. A threat to the Creator's life or the system's integrity is detected
    4. The pre-defined absence threshold has been exceeded

    The successor is NEVER notified for:
    - General emergencies (use emergency contacts)
    - Minor threats or suspicious activity
    - System maintenance or updates
    - Routine check-ins
    """
    successor_name: str = "Ethan Pace"
    successor_id: str = "144f7f638118138b"
    successor_phone: str = ""
    successor_email: str = ""

    # Conditions that must ALL be true before successor notification
    absence_threshold_hours: float = 24.0  # min hours of no Creator activity
    contact_attempts_required: int = 3  # min failed contact attempts
    threat_severity_required: str = "critical"  # min threat severity

    # State tracking
    creator_last_active: float = 0.0
    contact_attempts_made: int = 0
    successor_notified: bool = False
    successor_notified_at: float = 0.0
    notification_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "successor_name": self.successor_name,
            "successor_id": self.successor_id,
            "successor_phone": self.successor_phone,
            "successor_email": self.successor_email,
            "absence_threshold_hours": self.absence_threshold_hours,
            "contact_attempts_required": self.contact_attempts_required,
            "threat_severity_required": self.threat_severity_required,
            "creator_last_active": self.creator_last_active,
            "contact_attempts_made": self.contact_attempts_made,
            "successor_notified": self.successor_notified,
            "successor_notified_at": self.successor_notified_at,
            "notification_reason": self.notification_reason,
        }


class ContactManager:
    """Manages emergency contacts and successor notification policy.

    This is the central authority for who ANUBIS can contact and when.
    The successor policy is deliberately strict — the successor is only
    notified in the confirmed absence/takeover scenario.
    """

    ACTOR = "anubis.contacts"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger

        self._state_dir = self.root / "memory" / "contacts"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._contacts_file = self._state_dir / "emergency_contacts.json"
        self._attempts_file = self._state_dir / "contact_attempts.jsonl"
        self._successor_file = self._state_dir / "successor_policy.json"

        self._contacts: dict[str, EmergencyContact] = {}
        self._successor = SuccessorPolicy()
        self._load()

    # --------------------------------------------------- contacts

    def add_contact(
        self,
        name: str,
        phone: str = "",
        email: str = "",
        *,
        relationship: str = "",
        role: str = "general",
        priority: int = 99,
        trusted: bool = False,
        notes: str = "",
    ) -> EmergencyContact:
        """Add a new emergency contact."""
        contact_id = hashlib.sha256(
            f"contact:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        contact = EmergencyContact(
            contact_id=contact_id,
            name=name,
            phone=phone,
            email=email,
            relationship=relationship,
            role=role,
            priority=priority,
            trusted=trusted,
            notes=notes,
            created_at=time.time(),
            updated_at=time.time(),
        )

        self._contacts[contact_id] = contact
        self._save_contacts()
        self._log("contact.added", {"name": name, "role": role})
        return contact

    def remove_contact(self, contact_id: str) -> bool:
        """Remove an emergency contact."""
        if contact_id in self._contacts:
            name = self._contacts[contact_id].name
            del self._contacts[contact_id]
            self._save_contacts()
            self._log("contact.removed", {"name": name})
            return True
        return False

    def update_contact(
        self, contact_id: str, **kwargs: Any
    ) -> bool:
        """Update an emergency contact's fields."""
        contact = self._contacts.get(contact_id)
        if contact is None:
            return False
        for key, value in kwargs.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        contact.updated_at = time.time()
        self._save_contacts()
        return True

    def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        """Get a specific contact."""
        c = self._contacts.get(contact_id)
        return c.to_dict() if c else None

    def get_contacts(self) -> list[dict[str, Any]]:
        """Get all emergency contacts, sorted by priority."""
        contacts = sorted(
            self._contacts.values(),
            key=lambda c: (c.priority, c.name),
        )
        return [c.to_dict() for c in contacts]

    def get_available_contacts(self) -> list[dict[str, Any]]:
        """Get contacts that are available, sorted by priority."""
        contacts = sorted(
            [c for c in self._contacts.values() if c.available],
            key=lambda c: (c.priority, c.name),
        )
        return [c.to_dict() for c in contacts]

    def get_contact_by_phone(self, phone: str) -> dict[str, Any] | None:
        """Find a contact by phone number."""
        for c in self._contacts.values():
            if c.phone == phone:
                return c.to_dict()
        return None

    def set_contact_available(self, contact_id: str, available: bool) -> bool:
        """Toggle a contact's availability."""
        return self.update_contact(contact_id, available=available)

    # --------------------------------------------------- successor policy

    def get_successor_policy(self) -> dict[str, Any]:
        """Get the successor notification policy."""
        return self._successor.to_dict()

    def update_creator_activity(self) -> None:
        """Record that the Creator is active right now."""
        self._successor.creator_last_active = time.time()
        self._successor.contact_attempts_made = 0  # reset attempts
        self._save_successor()

    def record_contact_attempt(self) -> int:
        """Record an attempt to contact the Creator (that failed).

        Returns the new attempt count.
        """
        self._successor.contact_attempts_made += 1
        self._save_successor()
        return self._successor.contact_attempts_made

    def check_successor_notification_needed(
        self,
        threat_severity: str = "critical",
    ) -> tuple[bool, str]:
        """Check if the successor should be notified.

        Returns (should_notify, reason).
        The successor is notified ONLY when ALL conditions are met:
        1. Creator has been absent for the threshold period
        2. Enough contact attempts have failed
        3. A critical threat is detected
        4. Successor hasn't already been notified
        """
        if self._successor.successor_notified:
            return False, "Successor already notified"

        # Check absence
        if self._successor.creator_last_active == 0:
            return False, "No activity baseline set"

        hours_absent = (time.time() - self._successor.creator_last_active) / 3600
        if hours_absent < self._successor.absence_threshold_hours:
            return False, (
                f"Creator absent {hours_absent:.1f}h, "
                f"need {self._successor.absence_threshold_hours}h"
            )

        # Check contact attempts
        if self._successor.contact_attempts_made < self._successor.contact_attempts_required:
            return False, (
                f"Only {self._successor.contact_attempts_made} attempts, "
                f"need {self._successor.contact_attempts_required}"
            )

        # Check threat severity
        severity_order = ["low", "medium", "high", "critical"]
        required_idx = severity_order.index(
            self._successor.threat_severity_required
        )
        actual_idx = severity_order.index(threat_severity) if threat_severity in severity_order else 0
        if actual_idx < required_idx:
            return False, (
                f"Threat severity '{threat_severity}' below "
                f"required '{self._successor.threat_severity_required}'"
            )

        return True, "All conditions met for successor notification"

    def notify_successor(self, reason: str) -> bool:
        """Mark the successor as notified. This is irreversible.

        Once the successor is notified, it means the takeover scenario
        has been triggered. This is the most serious action ANUBIS can take.
        """
        if self._successor.successor_notified:
            return False  # already notified

        self._successor.successor_notified = True
        self._successor.successor_notified_at = time.time()
        self._successor.notification_reason = reason
        self._save_successor()

        self._log("successor.notified", {
            "successor": self._successor.successor_name,
            "reason": reason,
            "timestamp": self._successor.successor_notified_at,
        })

        return True

    def reset_successor_notification(self) -> bool:
        """Reset successor notification state.

        This should only be done by the Creator or successor confirming
        they are now in control. Requires governance approval in production.
        """
        self._successor.successor_notified = False
        self._successor.successor_notified_at = 0.0
        self._successor.notification_reason = ""
        self._successor.contact_attempts_made = 0
        self._successor.creator_last_active = time.time()
        self._save_successor()
        self._log("successor.notification_reset", {})
        return True

    def get_successor_contact_info(self) -> dict[str, str]:
        """Get successor contact info (only used when notification is approved)."""
        return {
            "name": self._successor.successor_name,
            "phone": self._successor.successor_phone,
            "email": self._successor.successor_email,
        }

    def set_successor_contact_info(
        self, phone: str = "", email: str = ""
    ) -> None:
        """Update successor contact info."""
        if phone:
            self._successor.successor_phone = phone
        if email:
            self._successor.successor_email = email
        self._save_successor()

    # --------------------------------------------------- contact attempts

    def record_attempt(
        self,
        contact_id: str,
        contact_name: str,
        method: str,
        message: str,
        status: str = "sent",
    ) -> ContactAttempt:
        """Record a contact attempt."""
        attempt = ContactAttempt(
            attempt_id=hashlib.sha256(
                f"attempt:{contact_id}:{time.time()}".encode()
            ).hexdigest()[:16],
            contact_id=contact_id,
            contact_name=contact_name,
            method=method,
            message=message,
            status=status,
            timestamp=time.time(),
        )

        try:
            with open(self._attempts_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(attempt.to_dict()) + "\n")
        except Exception:
            pass

        self._log("contact.attempt", attempt.to_dict())
        return attempt

    def get_attempts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent contact attempts."""
        if not self._attempts_file.exists():
            return []
        try:
            lines = self._attempts_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        """Get contact system status."""
        hours_absent = 0.0
        if self._successor.creator_last_active > 0:
            hours_absent = (time.time() - self._successor.creator_last_active) / 3600

        return {
            "total_contacts": len(self._contacts),
            "available_contacts": sum(
                1 for c in self._contacts.values() if c.available
            ),
            "trusted_contacts": sum(
                1 for c in self._contacts.values() if c.trusted
            ),
            "successor_name": self._successor.successor_name,
            "successor_notified": self._successor.successor_notified,
            "creator_hours_absent": round(hours_absent, 1),
            "contact_attempts_made": self._successor.contact_attempts_made,
            "absence_threshold_hours": self._successor.absence_threshold_hours,
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        """Load contacts and successor policy from disk."""
        # Load contacts
        if self._contacts_file.exists():
            try:
                data = json.loads(
                    self._contacts_file.read_text(encoding="utf-8")
                )
                for c_id, c_data in data.items():
                    self._contacts[c_id] = EmergencyContact(
                        contact_id=c_data["contact_id"],
                        name=c_data["name"],
                        phone=c_data.get("phone", ""),
                        email=c_data.get("email", ""),
                        relationship=c_data.get("relationship", ""),
                        role=c_data.get("role", ""),
                        priority=c_data.get("priority", 99),
                        trusted=c_data.get("trusted", False),
                        available=c_data.get("available", True),
                        notes=c_data.get("notes", ""),
                        created_at=c_data.get("created_at", 0),
                        updated_at=c_data.get("updated_at", 0),
                    )
            except Exception:
                pass

        # Load successor policy
        if self._successor_file.exists():
            try:
                data = json.loads(
                    self._successor_file.read_text(encoding="utf-8")
                )
                self._successor = SuccessorPolicy(
                    successor_name=data.get("successor_name", "Ethan Pace"),
                    successor_id=data.get("successor_id", "144f7f638118138b"),
                    successor_phone=data.get("successor_phone", ""),
                    successor_email=data.get("successor_email", ""),
                    absence_threshold_hours=data.get("absence_threshold_hours", 24.0),
                    contact_attempts_required=data.get("contact_attempts_required", 3),
                    threat_severity_required=data.get("threat_severity_required", "critical"),
                    creator_last_active=data.get("creator_last_active", 0.0),
                    contact_attempts_made=data.get("contact_attempts_made", 0),
                    successor_notified=data.get("successor_notified", False),
                    successor_notified_at=data.get("successor_notified_at", 0.0),
                    notification_reason=data.get("notification_reason", ""),
                )
            except Exception:
                pass

    def _save_contacts(self) -> None:
        data = {c_id: c.to_dict() for c_id, c in self._contacts.items()}
        self._contacts_file.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _save_successor(self) -> None:
        self._successor_file.write_text(
            json.dumps(self._successor.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
