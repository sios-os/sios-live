"""Package & delivery tracking.

ANUBIS tracks incoming packages and notifies when deliveries arrive.
Integrates with camera system to detect deliveries at the door.

CARRIERS:
- UPS, FedEx, USPS, Amazon, DHL
- Tracking via carrier APIs or web scraping (with gateway)
- Delivery detection via cameras (person + package at door)

Uses stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


CARRIER_UPS = "UPS"
CARRIER_FEDEX = "FedEx"
CARRIER_USPS = "USPS"
CARRIER_AMAZON = "Amazon"
CARRIER_DHL = "DHL"
CARRIER_UNKNOWN = "Unknown"

STATUS_PENDING = "pending"
STATUS_SHIPPED = "shipped"
STATUS_IN_TRANSIT = "in_transit"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_DELIVERED = "delivered"
STATUS_DELAYED = "delayed"
STATUS_EXCEPTION = "exception"


@dataclass
class Package:
    """A tracked package."""
    package_id: str
    tracking_number: str = ""
    carrier: str = CARRIER_UNKNOWN
    description: str = ""
    status: str = STATUS_PENDING
    ordered_at: float = 0.0
    shipped_at: float = 0.0
    estimated_delivery: float = 0.0
    delivered_at: float = 0.0
    sender: str = ""
    value: float = 0.0
    requires_signature: bool = False
    updates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "description": self.description,
            "status": self.status,
            "ordered_at": self.ordered_at,
            "shipped_at": self.shipped_at,
            "estimated_delivery": self.estimated_delivery,
            "delivered_at": self.delivered_at,
            "sender": self.sender,
            "value": self.value,
            "requires_signature": self.requires_signature,
            "updates": self.update_list(),
        }

    def update_list(self) -> list[dict[str, Any]]:
        return [{"timestamp": u.get("timestamp", 0), "status": u.get("status", ""), "location": u.get("location", "")} for u in self.updates]


class PackageTracker:
    """Package and delivery tracking system."""

    ACTOR = "anubis.packages"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        on_status_change: Callable[[Package], None] | None = None,
        on_delivered: Callable[[Package], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_status_change = on_status_change
        self.on_delivered = on_delivered

        self._state_dir = self.root / "memory" / "packages"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._packages_file = self._state_dir / "packages.json"

        self._packages: dict[str, Package] = {}
        self._load()

    def add_package(
        self, tracking_number: str, carrier: str = CARRIER_UNKNOWN,
        description: str = "", sender: str = "", value: float = 0,
        estimated_delivery: float = 0,
    ) -> Package:
        """Add a package to track."""
        package_id = hashlib.sha256(
            f"pkg:{tracking_number}:{time.time()}".encode()
        ).hexdigest()[:16]
        pkg = Package(
            package_id=package_id,
            tracking_number=tracking_number,
            carrier=carrier,
            description=description,
            sender=sender,
            value=value,
            ordered_at=time.time(),
            estimated_delivery=estimated_delivery,
        )
        self._packages[package_id] = pkg
        self._save()
        self._log("package.added", {"tracking": tracking_number, "carrier": carrier})
        return pkg

    def update_status(
        self, package_id: str, status: str, location: str = "",
    ) -> bool:
        """Update package status."""
        pkg = self._packages.get(package_id)
        if pkg is None:
            return False

        old_status = pkg.status
        pkg.status = status
        pkg.updates.append({
            "timestamp": time.time(),
            "status": status,
            "location": location,
        })

        if status == STATUS_SHIPPED and pkg.shipped_at == 0:
            pkg.shipped_at = time.time()
        elif status == STATUS_DELIVERED and pkg.delivered_at == 0:
            pkg.delivered_at = time.time()
            if self.on_delivered:
                try:
                    self.on_delivered(pkg)
                except Exception:
                    pass

        if old_status != status and self.on_status_change:
            try:
                self.on_status_change(pkg)
            except Exception:
                pass

        self._save()
        return True

    def remove_package(self, package_id: str) -> bool:
        if package_id in self._packages:
            del self._packages[package_id]
            self._save()
            return True
        return False

    def get_package(self, package_id: str) -> dict[str, Any] | None:
        pkg = self._packages.get(package_id)
        return pkg.to_dict() if pkg else None

    def get_packages(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._packages.values()]

    def get_active_packages(self) -> list[dict[str, Any]]:
        """Get packages that haven't been delivered yet."""
        return [
            p.to_dict() for p in self._packages.values()
            if p.status not in (STATUS_DELIVERED,)
        ]

    def get_delivered_packages(self) -> list[dict[str, Any]]:
        return [
            p.to_dict() for p in self._packages.values()
            if p.status == STATUS_DELIVERED
        ]

    def get_packages_by_carrier(self, carrier: str) -> list[dict[str, Any]]:
        return [
            p.to_dict() for p in self._packages.values()
            if p.carrier == carrier
        ]

    def detect_carrier(self, tracking_number: str) -> str:
        """Detect carrier from tracking number format."""
        tn = tracking_number.upper().replace(" ", "")
        if tn.startswith("1Z") and len(tn) == 18:
            return CARRIER_UPS
        if tn.isdigit() and len(tn) == 15:
            return CARRIER_FEDEX
        if tn.isdigit() and len(tn) in (20, 22):
            return CARRIER_USPS
        if tn.isdigit() and len(tn) == 10:
            return CARRIER_DHL
        return CARRIER_UNKNOWN

    def get_upcoming_deliveries(self, within_days: int = 3) -> list[dict[str, Any]]:
        """Get packages expected to be delivered within N days."""
        cutoff = time.time() + within_days * 86400
        return [
            p.to_dict() for p in self._packages.values()
            if p.status != STATUS_DELIVERED and
               0 < p.estimated_delivery <= cutoff
        ]

    def get_status(self) -> dict[str, Any]:
        return {
            "total_packages": len(self._packages),
            "active": len(self.get_active_packages()),
            "delivered": len(self.get_delivered_packages()),
            "upcoming": len(self.get_upcoming_deliveries()),
        }

    def _load(self) -> None:
        if not self._packages_file.exists():
            return
        try:
            data = json.loads(self._packages_file.read_text(encoding="utf-8"))
            for p_id, p in data.items():
                self._packages[p_id] = Package(
                    package_id=p_id,
                    tracking_number=p.get("tracking_number", ""),
                    carrier=p.get("carrier", CARRIER_UNKNOWN),
                    description=p.get("description", ""),
                    status=p.get("status", STATUS_PENDING),
                    ordered_at=p.get("ordered_at", 0),
                    shipped_at=p.get("shipped_at", 0),
                    estimated_delivery=p.get("estimated_delivery", 0),
                    delivered_at=p.get("delivered_at", 0),
                    sender=p.get("sender", ""),
                    value=p.get("value", 0),
                    requires_signature=p.get("requires_signature", False),
                    updates=p.get("updates", []),
                )
        except Exception:
            pass

    def _save(self) -> None:
        data = {p_id: p.to_dict() for p_id, p in self._packages.items()}
        self._packages_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
