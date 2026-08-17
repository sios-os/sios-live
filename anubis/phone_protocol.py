"""Phone companion app protocol.

Defines the communication protocol between ANUBIS and the phone
companion app. The phone app sends telemetry (GPS, accelerometer,
health, status) and receives commands (notifications, alerts).

PROTOCOL:
- Phone connects to ANUBIS API server (REST)
- Phone authenticates with device token
- Phone sends telemetry via POST endpoints
- ANUBIS sends notifications via push (or polling)

This module manages:
- Device registration and authentication
- Telemetry validation and routing
- Notification queue for offline devices
- Device health monitoring

The actual phone app would be a separate project (React Native or
Flutter), but this module defines the server-side protocol.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


DEVICE_ACTIVE = "active"
DEVICE_OFFLINE = "offline"
DEVICE_REGISTERED = "registered"
DEVICE_REVOKED = "revoked"


@dataclass
class PhoneDevice:
    """A registered phone device."""
    device_id: str
    name: str = ""
    owner: str = ""  # "creator", "family"
    token: str = ""  # auth token
    platform: str = ""  # "android", "ios"
    status: str = DEVICE_REGISTERED
    registered_at: float = 0.0
    last_seen: float = 0.0
    battery_level: float = 0.0
    battery_charging: bool = False
    app_version: str = ""
    push_token: str = ""  # FCM/APNs token

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "owner": self.owner,
            "platform": self.platform,
            "status": self.status,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "battery_level": self.battery_level,
            "battery_charging": self.battery_charging,
            "app_version": self.app_version,
        }


@dataclass
class Notification:
    """A notification queued for a device."""
    notif_id: str
    device_id: str = ""
    title: str = ""
    body: str = ""
    priority: str = "normal"  # normal, high, urgent
    created_at: float = 0.0
    delivered: bool = False
    delivered_at: float = 0.0
    action: str = ""  # optional action (e.g., "acknowledge", "call")

    def to_dict(self) -> dict[str, Any]:
        return {
            "notif_id": self.notif_id,
            "device_id": self.device_id,
            "title": self.title,
            "body": self.body,
            "priority": self.priority,
            "created_at": self.created_at,
            "delivered": self.delivered,
            "delivered_at": self.delivered_at,
            "action": self.action,
        }


class PhoneProtocol:
    """Phone companion app protocol manager.

    Manages device registration, telemetry routing, and notifications.
    Works with the API server to provide endpoints for the phone app.
    """

    ACTOR = "anubis.phone"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        on_telemetry: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_telemetry = on_telemetry

        self._state_dir = self.root / "memory" / "phone"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._devices_file = self._state_dir / "devices.json"
        self._notifs_file = self._state_dir / "notifications.jsonl"

        self._devices: dict[str, PhoneDevice] = {}
        self._notifications: list[Notification] = []
        self._load()

    def register_device(
        self, name: str, owner: str = "creator",
        platform: str = "", app_version: str = "",
    ) -> tuple[PhoneDevice, str]:
        """Register a new phone device. Returns (device, auth_token)."""
        device_id = hashlib.sha256(
            f"device:{name}:{time.time()}".encode()
        ).hexdigest()[:16]
        token = hashlib.sha256(
            f"token:{device_id}:{time.time()}".encode()
        ).hexdigest()

        device = PhoneDevice(
            device_id=device_id,
            name=name,
            owner=owner,
            token=token,
            platform=platform,
            status=DEVICE_REGISTERED,
            registered_at=time.time(),
            last_seen=time.time(),
            app_version=app_version,
        )

        self._devices[device_id] = device
        self._save_devices()
        self._log("device.registered", {"name": name, "owner": owner})
        return device, token

    def authenticate(self, device_id: str, token: str) -> bool:
        """Authenticate a device."""
        device = self._devices.get(device_id)
        if device is None or device.status == DEVICE_REVOKED:
            return False
        return device.token == token

    def revoke_device(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if device is None:
            return False
        device.status = DEVICE_REVOKED
        self._save_devices()
        return True

    def heartbeat(self, device_id: str, battery: float = 0, charging: bool = False) -> bool:
        """Update device heartbeat."""
        device = self._devices.get(device_id)
        if device is None:
            return False
        device.last_seen = time.time()
        device.battery_level = battery
        device.battery_charging = charging
        device.status = DEVICE_ACTIVE
        self._save_devices()
        return True

    def receive_telemetry(self, device_id: str, data: dict[str, Any]) -> bool:
        """Receive telemetry data from a phone."""
        device = self._devices.get(device_id)
        if device is None:
            return False
        device.last_seen = time.time()
        if self.on_telemetry:
            try:
                self.on_telemetry(device_id, data)
            except Exception:
                pass
        self._log("telemetry.received", {"device": device_id, "type": data.get("type", "")})
        return True

    def send_notification(
        self, device_id: str, title: str, body: str,
        priority: str = "normal", action: str = "",
    ) -> Notification:
        """Queue a notification for a device."""
        notif_id = hashlib.sha256(
            f"notif:{device_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        notif = Notification(
            notif_id=notif_id,
            device_id=device_id,
            title=title,
            body=body,
            priority=priority,
            action=action,
            created_at=time.time(),
        )
        self._notifications.append(notif)
        self._save_notifs()
        return notif

    def get_pending_notifications(self, device_id: str) -> list[dict[str, Any]]:
        """Get undelivered notifications for a device."""
        return [
            n.to_dict() for n in self._notifications
            if n.device_id == device_id and not n.delivered
        ]

    def mark_notification_delivered(self, notif_id: str) -> bool:
        for n in self._notifications:
            if n.notif_id == notif_id:
                n.delivered = True
                n.delivered_at = time.time()
                self._save_notifs()
                return True
        return False

    def get_devices(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._devices.values()]

    def get_active_devices(self) -> list[dict[str, Any]]:
        cutoff = time.time() - 300  # 5 minutes
        return [
            d.to_dict() for d in self._devices.values()
            if d.status == DEVICE_ACTIVE and d.last_seen > cutoff
        ]

    def get_offline_devices(self) -> list[dict[str, Any]]:
        cutoff = time.time() - 300
        return [
            d.to_dict() for d in self._devices.values()
            if d.last_seen < cutoff and d.status != DEVICE_REVOKED
        ]

    def get_status(self) -> dict[str, Any]:
        return {
            "total_devices": len(self._devices),
            "active": len(self.get_active_devices()),
            "offline": len(self.get_offline_devices()),
            "pending_notifications": sum(
                1 for n in self._notifications if not n.delivered
            ),
        }

    def _load(self) -> None:
        if self._devices_file.exists():
            try:
                data = json.loads(self._devices_file.read_text(encoding="utf-8"))
                for d_id, d in data.items():
                    self._devices[d_id] = PhoneDevice(
                        device_id=d_id,
                        name=d.get("name", ""),
                        owner=d.get("owner", ""),
                        token=d.get("token", ""),
                        platform=d.get("platform", ""),
                        status=d.get("status", DEVICE_REGISTERED),
                        registered_at=d.get("registered_at", 0),
                        last_seen=d.get("last_seen", 0),
                        battery_level=d.get("battery_level", 0),
                        battery_charging=d.get("battery_charging", False),
                        app_version=d.get("app_version", ""),
                    )
            except Exception:
                pass

        if self._notifs_file.exists():
            try:
                for line in self._notifs_file.read_text(encoding="utf-8").strip().splitlines():
                    n = json.loads(line)
                    self._notifications.append(Notification(
                        notif_id=n.get("notif_id", ""),
                        device_id=n.get("device_id", ""),
                        title=n.get("title", ""),
                        body=n.get("body", ""),
                        priority=n.get("priority", "normal"),
                        created_at=n.get("created_at", 0),
                        delivered=n.get("delivered", False),
                        delivered_at=n.get("delivered_at", 0),
                        action=n.get("action", ""),
                    ))
            except Exception:
                pass

    def _save_devices(self) -> None:
        data = {d_id: d.to_dict() for d_id, d in self._devices.items()}
        self._devices_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_notifs(self) -> None:
        try:
            with open(self._notifs_file, "w", encoding="utf-8") as f:
                for n in self._notifications:
                    f.write(json.dumps(n.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
