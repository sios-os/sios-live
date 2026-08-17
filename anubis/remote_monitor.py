"""Remote monitoring — ANUBIS watches the Creator while away from home.

The Creator's phone becomes ANUBIS's remote eyes and ears. This module
receives data from multiple sources and monitors the Creator's safety:

1. **Phone companion app** — streams GPS location, accelerometer
   (fall detection), battery, optional audio for voice/emotion analysis
2. **Wearable device** — smartwatch/fitness band data: heart rate,
   fall detection, activity level
3. **Network phone connection** — when on same WiFi, ANUBIS can
   connect directly to the phone for audio/status
4. **Car integration** — OBD-II data for driving patterns (future)

ANUBIS uses whatever source is available at any given time. If the
phone app is running, use it. If a wearable is connected, use it too.
If only network connection is available, use that. Cross-reference
multiple sources for accuracy.

FALL DETECTION:
- Accelerometer data: high-impact event followed by stillness
- Heart rate spike then drop (wearable)
- No movement for extended period after impact
- ANUBIS sends emergency alert if fall detected and Creator doesn't respond

LOCATION MONITORING:
- Track GPS coordinates over time
- Detect if Creator is at unusual locations
- Detect if Creator hasn't moved for an unusual period
- Geofence: alert if Creator leaves expected area

PRIVACY:
- Location data is only stored locally, never shared
- Audio from phone mic is only analyzed locally, never recorded
- The Creator can disable any source at any time
- All monitoring requires Creator opt-in

The phone companion app (separate project) sends data to ANUBIS
via an encrypted local connection. This module receives and analyzes it.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class LocationUpdate:
    """A GPS location update from the phone."""
    timestamp: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    accuracy: float = 0.0  # meters
    speed: float = 0.0  # m/s
    altitude: float = 0.0
    source: str = "phone"  # phone, wearable, car

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "speed": self.speed,
            "altitude": self.altitude,
            "source": self.source,
        }


@dataclass
class AccelerometerData:
    """Accelerometer data from the phone or wearable."""
    timestamp: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    magnitude: float = 0.0  # computed: sqrt(x² + y² + z²)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "magnitude": round(self.magnitude, 3),
        }


@dataclass
class HealthData:
    """Health data from a wearable device."""
    timestamp: float = 0.0
    heart_rate: int = 0  # bpm
    heart_rate_variability: float = 0.0
    steps: int = 0
    activity_level: str = "unknown"  # resting, walking, running, cycling
    stress_level: float = 0.0  # 0-1, if wearable supports it
    blood_oxygen: float = 0.0  # SpO2 %
    body_temperature: float = 0.0
    source: str = "wearable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "heart_rate": self.heart_rate,
            "heart_rate_variability": self.heart_rate_variability,
            "steps": self.steps,
            "activity_level": self.activity_level,
            "stress_level": self.stress_level,
            "blood_oxygen": self.blood_oxygen,
            "body_temperature": self.body_temperature,
            "source": self.source,
        }


@dataclass
class PhoneStatus:
    """Status update from the phone."""
    timestamp: float = 0.0
    battery_level: float = 0.0  # 0-100
    battery_charging: bool = False
    network_type: str = ""  # wifi, cellular, none
    screen_on: bool = False
    in_call: bool = False
    ringer_mode: str = ""  # normal, silent, vibrate

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "battery_level": self.battery_level,
            "battery_charging": self.battery_charging,
            "network_type": self.network_type,
            "screen_on": self.screen_on,
            "in_call": self.in_call,
            "ringer_mode": self.ringer_mode,
        }


@dataclass
class FallEvent:
    """A detected fall event."""
    event_id: str
    timestamp: float = 0.0
    impact_magnitude: float = 0.0
    location: LocationUpdate | None = None
    creator_responded: bool = False
    response_timestamp: float = 0.0
    alert_sent: bool = False
    severity: str = "unknown"  # minor, moderate, severe, unknown

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "impact_magnitude": round(self.impact_magnitude, 3),
            "location": self.location.to_dict() if self.location else None,
            "creator_responded": self.creator_responded,
            "response_timestamp": self.response_timestamp,
            "alert_sent": self.alert_sent,
            "severity": self.severity,
        }


@dataclass
class RemoteAlert:
    """An alert generated by remote monitoring."""
    alert_id: str
    alert_type: str = ""  # fall, no_movement, unusual_location, low_battery, etc.
    severity: str = "low"
    description: str = ""
    timestamp: float = 0.0
    location: LocationUpdate | None = None
    resolved: bool = False
    response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "timestamp": self.timestamp,
            "location": self.location.to_dict() if self.location else None,
            "resolved": self.resolved,
            "response": self.response,
        }


class RemoteMonitor:
    """Monitors the Creator while away from home.

    Receives data from phone, wearable, and network sources.
    Detects falls, unusual locations, inactivity, and other safety issues.
    Sends alerts through the messaging system when needed.

    The phone companion app sends data via a local HTTP endpoint or
    direct socket connection. This module processes that data.
    """

    ACTOR = "anubis.remote_monitor"

    # Fall detection thresholds
    FALL_IMPACT_THRESHOLD = 25.0  # m/s² (gravity = 9.8, fall impact is much higher)
    FALL_STILLNESS_THRESHOLD = 2.0  # m/s² (after fall, movement is minimal)
    FALL_STILLNESS_DURATION = 5.0  # seconds of stillness to confirm fall
    FALL_RESPONSE_TIMEOUT = 60.0  # seconds to wait for Creator response

    # Location monitoring
    HOME_RADIUS_M = 100  # meters — if within this radius of home, Creator is "home"
    STATIONARY_TIMEOUT = 3600  # seconds — no movement for 1 hour is unusual (when away)
    LOW_BATTERY_THRESHOLD = 15.0  # percent

    def __init__(
        self,
        root: str | Path,
        *,
        home_latitude: float = 0.0,
        home_longitude: float = 0.0,
        ledger: Any | None = None,
        on_alert: Callable[[RemoteAlert], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.home_latitude = home_latitude
        self.home_longitude = home_longitude
        self.ledger = ledger
        self.on_alert = on_alert

        self._state_dir = self.root / "memory" / "remote_monitor"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._locations_file = self._state_dir / "locations.jsonl"
        self._falls_file = self._state_dir / "falls.jsonl"
        self._alerts_file = self._state_dir / "alerts.jsonl"
        self._health_file = self._state_dir / "health.jsonl"

        # State tracking
        self._last_location: LocationUpdate | None = None
        self._last_movement_time: float = time.time()
        self._last_accel: AccelerometerData | None = None
        self._potential_fall: FallEvent | None = None
        self._phone_status: PhoneStatus | None = None
        self._last_health: HealthData | None = None
        self._monitoring: bool = False
        self._sources: dict[str, bool] = {
            "phone": False,
            "wearable": False,
            "network": False,
        }

    # --------------------------------------------------- data ingestion

    def receive_location(self, location: LocationUpdate) -> None:
        """Receive a location update from the phone."""
        self._last_location = location
        self._sources["phone"] = True

        # Record location
        self._record(self._locations_file, location.to_dict())

        # Check for issues
        self._check_location(location)

    def receive_accelerometer(self, data: AccelerometerData) -> None:
        """Receive accelerometer data from the phone or wearable."""
        # Compute magnitude if not set
        if data.magnitude == 0:
            data.magnitude = math.sqrt(data.x**2 + data.y**2 + data.z**2)

        self._last_accel = data
        self._sources["phone"] = True

        # Check for fall
        self._check_fall(data)

    def receive_health(self, data: HealthData) -> None:
        """Receive health data from a wearable."""
        self._last_health = data
        self._sources["wearable"] = True

        # Record health data
        self._record(self._health_file, data.to_dict())

        # Check for health issues
        self._check_health(data)

    def receive_phone_status(self, status: PhoneStatus) -> None:
        """Receive phone status update."""
        self._phone_status = status
        self._sources["phone"] = True

        # Check for low battery
        if status.battery_level < self.LOW_BATTERY_THRESHOLD:
            if not status.battery_charging:
                self._create_alert(
                    alert_type="low_battery",
                    severity="low",
                    description=f"Phone battery at {status.battery_level:.0f}%",
                )

    # --------------------------------------------------- fall detection

    def _check_fall(self, data: AccelerometerData) -> None:
        """Check accelerometer data for a fall event."""
        # If we already have a potential fall, check for stillness or recovery
        if self._potential_fall and not self._potential_fall.creator_responded:
            if data.magnitude < self.FALL_STILLNESS_THRESHOLD:
                # Still after impact — likely a fall
                time_since_impact = data.timestamp - self._potential_fall.timestamp
                if time_since_impact > self.FALL_STILLNESS_DURATION:
                    # Confirmed fall — Creator hasn't moved
                    self._potential_fall.severity = self._assess_fall_severity(
                        self._potential_fall.impact_magnitude
                    )
                    self._confirm_fall(self._potential_fall)
                    self._potential_fall = None
            elif data.magnitude > 10.0:
                # Creator moved after impact — probably not a fall
                self._potential_fall.creator_responded = True
                self._potential_fall.response_timestamp = data.timestamp
                self._record(self._falls_file, self._potential_fall.to_dict())
                self._potential_fall = None
            return  # Don't check for new impact on same data as recovery check

        # Detect impact (sudden high acceleration) — only when no pending fall
        if data.magnitude > self.FALL_IMPACT_THRESHOLD:
            # Potential fall — start monitoring for stillness
            self._potential_fall = FallEvent(
                event_id=hashlib.sha256(
                    f"fall:{data.timestamp}".encode()
                ).hexdigest()[:16],
                timestamp=data.timestamp,
                impact_magnitude=data.magnitude,
                location=self._last_location,
            )
            self._log("fall.impact_detected", {
                "magnitude": data.magnitude,
                "timestamp": data.timestamp,
            })

    def _assess_fall_severity(self, impact: float) -> str:
        """Assess fall severity from impact magnitude."""
        if impact > 40:
            return "severe"
        elif impact > 30:
            return "moderate"
        else:
            return "minor"

    def _confirm_fall(self, fall: FallEvent) -> None:
        """Confirm a fall event and trigger alert."""
        fall.alert_sent = True
        self._record(self._falls_file, fall.to_dict())

        # _create_alert calls on_alert callback
        self._create_alert(
            alert_type="fall_detected",
            severity="critical",
            description=(
                f"Fall detected — impact {fall.impact_magnitude:.1f} m/s², "
                f"Creator hasn't moved. Severity: {fall.severity}"
            ),
            location=fall.location,
        )

        self._log("fall.confirmed", fall.to_dict())

    def creator_responded_after_fall(self) -> None:
        """Mark that the Creator responded after a fall alert."""
        if self._potential_fall:
            self._potential_fall.creator_responded = True
            self._potential_fall.response_timestamp = time.time()
            self._record(self._falls_file, self._potential_fall.to_dict())
            self._potential_fall = None

    # --------------------------------------------------- location monitoring

    def _check_location(self, location: LocationUpdate) -> None:
        """Check location for issues."""
        # Update movement time if moving
        if location.speed > 0.5:  # walking speed
            self._last_movement_time = location.timestamp

        # Check if Creator is home
        if self.home_latitude and self.home_longitude:
            distance = self._haversine_distance(
                location.latitude, location.longitude,
                self.home_latitude, self.home_longitude,
            )

            if distance > self.HOME_RADIUS_M:
                # Creator is away from home
                # Check for unusual stationary period
                stationary_time = location.timestamp - self._last_movement_time
                if stationary_time > self.STATIONARY_TIMEOUT and location.speed < 0.5:
                    self._create_alert(
                        alert_type="unusual_stationary",
                        severity="medium",
                        description=(
                            f"Creator hasn't moved in "
                            f"{stationary_time/60:.0f} minutes while away from home"
                        ),
                        location=location,
                    )

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two GPS points in meters."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    # --------------------------------------------------- health monitoring

    def _check_health(self, data: HealthData) -> None:
        """Check health data for issues."""
        # Abnormal heart rate
        if data.heart_rate > 0:
            if data.heart_rate > 150 or data.heart_rate < 40:
                self._create_alert(
                    alert_type="abnormal_heart_rate",
                    severity="high",
                    description=f"Abnormal heart rate: {data.heart_rate} bpm",
                )

        # Low blood oxygen
        if data.blood_oxygen > 0 and data.blood_oxygen < 90:
            self._create_alert(
                alert_type="low_blood_oxygen",
                severity="high",
                description=f"Low blood oxygen: {data.blood_oxygen:.0f}%",
            )

        # High stress
        if data.stress_level > 0.8:
            self._create_alert(
                alert_type="high_stress",
                severity="medium",
                description=f"High stress level detected: {data.stress_level:.0%}",
            )

    # --------------------------------------------------- alerts

    def _create_alert(
        self, alert_type: str, severity: str = "low",
        description: str = "", location: LocationUpdate | None = None,
    ) -> RemoteAlert:
        """Create a remote monitoring alert."""
        alert = RemoteAlert(
            alert_id=hashlib.sha256(
                f"alert:{alert_type}:{time.time()}".encode()
            ).hexdigest()[:16],
            alert_type=alert_type,
            severity=severity,
            description=description,
            timestamp=time.time(),
            location=location,
        )
        self._record(self._alerts_file, alert.to_dict())
        self._log("alert.created", alert.to_dict())

        if self.on_alert:
            try:
                self.on_alert(alert)
            except Exception:
                pass

        return alert

    def get_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent remote monitoring alerts."""
        return self._read_records(self._alerts_file, limit)

    def get_falls(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get fall event history."""
        return self._read_records(self._falls_file, limit)

    def get_locations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent location updates."""
        return self._read_records(self._locations_file, limit)

    def get_health_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get health data history."""
        return self._read_records(self._health_file, limit)

    # --------------------------------------------------- status

    def start_monitoring(self) -> None:
        """Start remote monitoring."""
        self._monitoring = True
        self._log("monitoring.started", {})

    def stop_monitoring(self) -> None:
        """Stop remote monitoring."""
        self._monitoring = False
        self._log("monitoring.stopped", {})

    @property
    def is_monitoring(self) -> bool:
        return self._monitoring

    def get_active_sources(self) -> list[str]:
        """Get list of currently active data sources."""
        return [s for s, active in self._sources.items() if active]

    def get_last_known_location(self) -> dict[str, Any] | None:
        """Get the Creator's last known location."""
        return self._last_location.to_dict() if self._last_location else None

    def get_status(self) -> dict[str, Any]:
        """Get remote monitor status."""
        return {
            "monitoring": self._monitoring,
            "sources": self._sources,
            "active_sources": self.get_active_sources(),
            "home_set": self.home_latitude != 0 and self.home_longitude != 0,
            "last_location": self.get_last_known_location(),
            "potential_fall": (
                self._potential_fall.to_dict() if self._potential_fall else None
            ),
            "phone_battery": (
                self._phone_status.battery_level if self._phone_status else None
            ),
            "heart_rate": (
                self._last_health.heart_rate if self._last_health else None
            ),
            "total_alerts": len(self.get_alerts(limit=9999)),
            "total_falls": len(self.get_falls(limit=9999)),
        }

    # --------------------------------------------------- helpers

    def _record(self, file_path: Path, data: dict[str, Any]) -> None:
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception:
            pass

    def _read_records(self, file_path: Path, limit: int) -> list[dict[str, Any]]:
        if not file_path.exists():
            return []
        try:
            lines = file_path.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
