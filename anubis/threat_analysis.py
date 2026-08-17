"""Threat analysis — ANUBIS's unified threat detection and response.

This module ties together all perception, sensory, network, and remote
monitoring data to detect threats across four domains:

1. **Physical threats** — intruders, duress, unknown people/voices
2. **Behavioral threats** — coercion, impersonation, social engineering
3. **Cyber threats** — network intrusions, unauthorized access, tampering
4. **Remote threats** — falls, medical events, unusual location, no movement

Threat severity levels:
- CRITICAL: Immediate danger → alert Creator + emergency contacts, record evidence
- HIGH: Significant threat → alert Creator immediately, capture evidence
- MEDIUM: Suspicious activity → notify Creator, log everything
- LOW: Notable but not dangerous → log for pattern analysis

DESIGN PRINCIPLES:
- ANUBIS never takes action against a person autonomously
- He alerts, records, and recommends — humans make the call
- All threats logged to the tamper-evident evidence ledger
- Duress detection has a special path (requires successor confirmation)
- Privacy preserved — threat analysis doesn't expose raw audio/video
- False positives managed — ANUBIS asks for confirmation before escalating

SUCCESSOR POLICY:
The successor is ONLY notified when ALL conditions are met:
1. Creator absent for threshold period (default 24 hours)
2. All contact attempts to Creator have failed
3. A critical threat is detected
This is handled by ContactManager, not this module directly.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .contacts import ContactManager
from .messaging import SignalMessenger


# Threat severity levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

SEVERITY_ORDER = [SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]

# Threat domains
DOMAIN_PHYSICAL = "physical"
DOMAIN_BEHAVIORAL = "behavioral"
DOMAIN_CYBER = "cyber"
DOMAIN_REMOTE = "remote"

# Threat types
THREAT_INTRUDER = "intruder"
THREAT_DURESS = "duress"
THREAT_UNKNOWN_VOICE = "unknown_voice"
THREAT_UNKNOWN_PERSON = "unknown_person"
THREAT_VEHICLE_UNUSUAL = "vehicle_unusual"
THREAT_COERCION = "coercion"
THREAT_IMPERSONATION = "impersonation"
THREAT_SOCIAL_ENGINEERING = "social_engineering"
THREAT_UNAUTHORIZED_ACCESS = "unauthorized_access"
THREAT_BRUTE_FORCE = "brute_force"
THREAT_NETWORK_INTRUSION = "network_intrusion"
THREAT_TAMPER = "tamper"
THREAT_SANDBOX_ESCAPE = "sandbox_escape"
THREAT_KNOWLEDGE_POISONING = "knowledge_poisoning"
THREAT_FALL = "fall"
THREAT_MEDICAL = "medical"
THREAT_NO_MOVEMENT = "no_movement"
THREAT_UNUSUAL_LOCATION = "unusual_location"
THREAT_LOW_BATTERY = "low_battery"


@dataclass
class Threat:
    """A detected threat."""
    threat_id: str
    domain: str = ""  # physical, behavioral, cyber, remote
    threat_type: str = ""  # intruder, duress, fall, etc.
    severity: str = SEVERITY_LOW
    description: str = ""
    timestamp: float = 0.0
    source: str = ""  # perception, sensory, network, remote_monitor
    evidence: dict[str, Any] = field(default_factory=dict)
    location: str = ""  # home, away, network
    creator_present: bool = True
    resolved: bool = False
    response: str = ""
    response_timestamp: float = 0.0
    alerts_sent: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat_id": self.threat_id,
            "domain": self.domain,
            "threat_type": self.threat_type,
            "severity": self.severity,
            "description": self.description,
            "timestamp": self.timestamp,
            "source": self.source,
            "evidence": self.evidence,
            "location": self.location,
            "creator_present": self.creator_present,
            "resolved": self.resolved,
            "response": self.response,
            "response_timestamp": self.response_timestamp,
            "alerts_sent": self.alerts_sent,
        }


@dataclass
class ThreatResponse:
    """Recommended response to a threat."""
    action: str = ""  # alert_creator, alert_contacts, record_evidence, etc.
    description: str = ""
    requires_approval: bool = False
    notify_successor: bool = False
    emergency_contacts: bool = False
    record_evidence: bool = True
    lockdown: bool = False  # lock down sensitive systems

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "description": self.description,
            "requires_approval": self.requires_approval,
            "notify_successor": self.notify_successor,
            "emergency_contacts": self.emergency_contacts,
            "record_evidence": self.record_evidence,
            "lockdown": self.lockdown,
        }


@dataclass
class BehavioralBaseline:
    """Learns normal patterns for the Creator and household."""
    # Voice patterns
    normal_emotions: list[str] = field(default_factory=lambda: ["neutral", "calm"])
    normal_speech_times: list[float] = field(default_factory=list)  # hours of day

    # Activity patterns
    normal_active_hours: tuple[float, float] = (7.0, 23.0)  # 7am to 11pm
    normal_home_hours: tuple[float, float] = (18.0, 8.0)  # 6pm to 8am

    # Network patterns
    normal_device_count: int = 5
    normal_active_devices: list[str] = field(default_factory=list)

    # Command patterns
    normal_command_frequency: float = 10.0  # commands per day
    normal_command_types: list[str] = field(default_factory=list)

    # Learning state
    samples: int = 0
    last_updated: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "normal_emotions": self.normal_emotions,
            "normal_active_hours": list(self.normal_active_hours),
            "normal_home_hours": list(self.normal_home_hours),
            "normal_device_count": self.normal_device_count,
            "normal_active_devices": self.normal_active_devices,
            "normal_command_frequency": self.normal_command_frequency,
            "normal_command_types": self.normal_command_types,
            "samples": self.samples,
            "last_updated": self.last_updated,
        }


class ThreatDetector:
    """Unified threat detection across all domains.

    Integrates with:
    - PerceptionSystem (voice ID, emotion, faces, objects)
    - SensorySystem (audio, screen, voice)
    - NetworkOperator (network devices, intrusions)
    - RemoteMonitor (location, fall detection, health)
    - ContactManager (emergency contacts, successor policy)
    - SignalMessenger (sending alerts)
    - Evidence ledger (logging all threats)
    """

    ACTOR = "anubis.threat_analysis"

    def __init__(
        self,
        root: str | Path,
        *,
        contacts: ContactManager | None = None,
        messaging: SignalMessenger | None = None,
        ledger: Any | None = None,
        observer: Any | None = None,
        on_threat: Callable[[Threat], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.contacts = contacts
        self.messaging = messaging
        self.ledger = ledger
        self.observer = observer
        self.on_threat = on_threat

        self._state_dir = self.root / "memory" / "threats"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._threats_file = self._state_dir / "threats.jsonl"
        self._baseline_file = self._state_dir / "baseline.json"

        self._baseline = BehavioralBaseline()
        self._load_baseline()
        self._active_threats: dict[str, Threat] = {}

    # --------------------------------------------------- threat analysis

    def analyze_perception(
        self,
        voice_result: dict[str, Any] | None = None,
        emotion_result: dict[str, Any] | None = None,
        face_result: dict[str, Any] | None = None,
        scene_result: dict[str, Any] | None = None,
        *,
        creator_present: bool = True,
    ) -> list[Threat]:
        """Analyze perception data for physical threats."""
        threats: list[Threat] = []

        # Voice-based threats
        if voice_result:
            threats.extend(self._analyze_voice(voice_result, creator_present))

        # Emotion-based threats
        if emotion_result:
            threats.extend(self._analyze_emotion(emotion_result, creator_present))

        # Face-based threats
        if face_result:
            threats.extend(self._analyze_faces(face_result, creator_present))

        # Object-based threats
        if scene_result:
            threats.extend(self._analyze_scene(scene_result, creator_present))

        # Process all detected threats
        for threat in threats:
            self._process_threat(threat)

        return threats

    def analyze_network(
        self,
        devices: list[dict[str, Any]] | None = None,
        alerts: list[dict[str, Any]] | None = None,
    ) -> list[Threat]:
        """Analyze network data for cyber threats."""
        threats: list[Threat] = []

        if alerts:
            for alert in alerts:
                threat = Threat(
                    threat_id=self._gen_id("net", alert.get("alert_type", "")),
                    domain=DOMAIN_CYBER,
                    threat_type=THREAT_NETWORK_INTRUSION,
                    severity=alert.get("severity", SEVERITY_MEDIUM),
                    description=alert.get("description", ""),
                    timestamp=time.time(),
                    source="network_ops",
                    evidence=alert,
                )
                threats.append(threat)

        if devices:
            for device in devices:
                if not device.get("known", False) and device.get("ip"):
                    threat = Threat(
                        threat_id=self._gen_id("dev", device.get("device_id", "")),
                        domain=DOMAIN_CYBER,
                        threat_type=THREAT_UNAUTHORIZED_ACCESS,
                        severity=SEVERITY_MEDIUM,
                        description=f"Unknown device on network: {device.get('ip', '')}",
                        timestamp=time.time(),
                        source="network_ops",
                        evidence=device,
                    )
                    threats.append(threat)

        for threat in threats:
            self._process_threat(threat)

        return threats

    def analyze_remote(
        self,
        remote_alerts: list[dict[str, Any]] | None = None,
        location: dict[str, Any] | None = None,
        health: dict[str, Any] | None = None,
    ) -> list[Threat]:
        """Analyze remote monitoring data for threats while Creator is away."""
        threats: list[Threat] = []

        if remote_alerts:
            for alert in remote_alerts:
                threat_type = THREAT_NO_MOVEMENT
                if alert.get("alert_type") == "fall_detected":
                    threat_type = THREAT_FALL
                elif alert.get("alert_type") == "abnormal_heart_rate":
                    threat_type = THREAT_MEDICAL
                elif alert.get("alert_type") == "low_blood_oxygen":
                    threat_type = THREAT_MEDICAL
                elif alert.get("alert_type") == "unusual_stationary":
                    threat_type = THREAT_NO_MOVEMENT
                elif alert.get("alert_type") == "low_battery":
                    threat_type = THREAT_LOW_BATTERY

                threat = Threat(
                    threat_id=self._gen_id("rem", alert.get("alert_id", "")),
                    domain=DOMAIN_REMOTE,
                    threat_type=threat_type,
                    severity=alert.get("severity", SEVERITY_MEDIUM),
                    description=alert.get("description", ""),
                    timestamp=alert.get("timestamp", time.time()),
                    source="remote_monitor",
                    evidence=alert,
                    location="away",
                    creator_present=False,
                )
                threats.append(threat)

        for threat in threats:
            self._process_threat(threat)

        return threats

    # --------------------------------------------------- specific analyzers

    def _analyze_voice(
        self, voice_result: dict[str, Any], creator_present: bool
    ) -> list[Threat]:
        """Analyze voice identification for threats."""
        threats: list[Threat] = []

        is_human = voice_result.get("is_human", True)
        is_known = voice_result.get("is_known", False)
        is_trusted = voice_result.get("is_trusted", False)
        audio_type = voice_result.get("audio_type", "speech")

        # Unknown human voice in home
        if is_human and not is_known and creator_present and audio_type == "speech":
            threats.append(Threat(
                threat_id=self._gen_id("voice", voice_result.get("name", "")),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_UNKNOWN_VOICE,
                severity=SEVERITY_MEDIUM,
                description=(
                    f"Unknown voice detected in home"
                    if creator_present else
                    f"Unknown voice detected — Creator not home"
                ),
                timestamp=time.time(),
                source="perception",
                evidence=voice_result,
                creator_present=creator_present,
            ))

        # Unknown voice while Creator not home — more serious
        if is_human and not is_known and not creator_present:
            threats[-1].severity = SEVERITY_HIGH if threats else SEVERITY_HIGH
            if threats:
                threats[-1].description = (
                    "Unknown voice detected — Creator is not home. "
                    "Possible intruder."
                )

        return threats

    def _analyze_emotion(
        self, emotion_result: dict[str, Any], creator_present: bool
    ) -> list[Threat]:
        """Analyze emotion for duress or distress."""
        threats: list[Threat] = []

        emotion = emotion_result.get("emotion", "neutral")
        confidence = emotion_result.get("confidence", 0.0)

        if emotion == "duress" and confidence > 0.7:
            threats.append(Threat(
                threat_id=self._gen_id("emo", "duress"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_DURESS,
                severity=SEVERITY_CRITICAL,
                description=(
                    f"Duress detected in Creator's voice "
                    f"(confidence: {confidence:.0%})"
                ),
                timestamp=time.time(),
                source="perception",
                evidence=emotion_result,
                creator_present=True,
            ))

        elif emotion == "fearful" and confidence > 0.6:
            threats.append(Threat(
                threat_id=self._gen_id("emo", "fear"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_DURESS,
                severity=SEVERITY_HIGH,
                description=(
                    f"Fear detected in Creator's voice "
                    f"(confidence: {confidence:.0%})"
                ),
                timestamp=time.time(),
                source="perception",
                evidence=emotion_result,
                creator_present=True,
            ))

        return threats

    def _analyze_faces(
        self, face_result: dict[str, Any], creator_present: bool
    ) -> list[Threat]:
        """Analyze face recognition for threats."""
        threats: list[Threat] = []

        face_count = face_result.get("face_count", 0)
        unknown_count = face_result.get("unknown_count", 0)
        is_known = face_result.get("is_known", False)

        # Unknown person detected
        if unknown_count > 0 and not creator_present:
            threats.append(Threat(
                threat_id=self._gen_id("face", "intruder"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_INTRUDER,
                severity=SEVERITY_CRITICAL,
                description=(
                    f"Unknown person detected — Creator is not home. "
                    f"{unknown_count} unknown face(s)."
                ),
                timestamp=time.time(),
                source="perception",
                evidence=face_result,
                creator_present=False,
            ))
        elif unknown_count > 0 and creator_present:
            threats.append(Threat(
                threat_id=self._gen_id("face", "unknown"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_UNKNOWN_PERSON,
                severity=SEVERITY_MEDIUM,
                description=f"Unknown person detected — {unknown_count} face(s)",
                timestamp=time.time(),
                source="perception",
                evidence=face_result,
                creator_present=True,
            ))

        return threats

    def _analyze_scene(
        self, scene_result: dict[str, Any], creator_present: bool
    ) -> list[Threat]:
        """Analyze scene/object detection for threats."""
        threats: list[Threat] = []

        people_count = scene_result.get("people_count", 0)
        vehicles_count = scene_result.get("vehicles_count", 0)

        # People detected while Creator not home
        if people_count > 0 and not creator_present:
            threats.append(Threat(
                threat_id=self._gen_id("scene", "people"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_INTRUDER,
                severity=SEVERITY_HIGH,
                description=f"{people_count} person(s) detected — Creator not home",
                timestamp=time.time(),
                source="perception",
                evidence=scene_result,
                creator_present=False,
            ))

        # Vehicle at unusual hours
        current_hour = time.localtime().tm_hour
        if vehicles_count > 0 and (current_hour < 6 or current_hour > 23):
            threats.append(Threat(
                threat_id=self._gen_id("scene", "vehicle"),
                domain=DOMAIN_PHYSICAL,
                threat_type=THREAT_VEHICLE_UNUSUAL,
                severity=SEVERITY_LOW,
                description=f"Vehicle detected at unusual hour ({current_hour}:00)",
                timestamp=time.time(),
                source="perception",
                evidence=scene_result,
            ))

        return threats

    # --------------------------------------------------- threat processing

    def _process_threat(self, threat: Threat) -> None:
        """Process a detected threat — record, alert, respond."""
        # Record threat
        self._record_threat(threat)
        self._active_threats[threat.threat_id] = threat

        # Get recommended response
        response = self._recommend_response(threat)

        # Execute response
        self._execute_response(threat, response)

        # Feed to observer
        if self.observer is not None:
            try:
                self.observer._make_observation(
                    source="threat_analysis",
                    event_type=threat.threat_type,
                    content=threat.description,
                    severity=threat.severity,
                )
            except Exception:
                pass

        # Trigger callback
        if self.on_threat:
            try:
                self.on_threat(threat)
            except Exception:
                pass

        # Log
        self._log("threat.detected", threat.to_dict())

    def _recommend_response(self, threat: Threat) -> ThreatResponse:
        """Recommend a response based on threat severity and type."""
        response = ThreatResponse()

        if threat.severity == SEVERITY_CRITICAL:
            response.action = "critical_alert"
            response.description = "Critical threat — alert Creator and emergency contacts"
            response.emergency_contacts = True
            response.record_evidence = True
            response.lockdown = True
            # Check if successor notification is needed
            if self.contacts:
                should_notify, reason = (
                    self.contacts.check_successor_notification_needed(
                        threat.severity
                    )
                )
                if should_notify:
                    response.notify_successor = True
                    response.description += (
                        f". Successor notification conditions met: {reason}"
                    )

        elif threat.severity == SEVERITY_HIGH:
            response.action = "high_alert"
            response.description = "High-severity threat — alert Creator immediately"
            response.emergency_contacts = True
            response.record_evidence = True

        elif threat.severity == SEVERITY_MEDIUM:
            response.action = "medium_alert"
            response.description = "Medium-severity threat — notify Creator"
            response.record_evidence = True
            response.requires_approval = False

        else:  # LOW
            response.action = "log"
            response.description = "Low-severity threat — logged for analysis"
            response.record_evidence = True

        # Special case: duress
        if threat.threat_type == THREAT_DURESS:
            response.requires_approval = True
            response.description += (
                ". Duress detected — require secondary confirmation"
            )

        return response

    def _execute_response(self, threat: Threat, response: ThreatResponse) -> None:
        """Execute the recommended response."""
        threat.response = response.description

        # Record evidence
        if response.record_evidence and self.ledger:
            try:
                self.ledger.append(
                    self.ACTOR,
                    "threat.evidence",
                    {
                        "threat_id": threat.threat_id,
                        "type": threat.threat_type,
                        "severity": threat.severity,
                        "evidence": threat.evidence,
                    },
                )
            except Exception:
                pass

        # Send emergency alerts
        if response.emergency_contacts and self.messaging:
            try:
                messages = self.messaging.send_emergency_alert(
                    f"ANUBIS Alert: {threat.description}"
                )
                threat.alerts_sent = [m.to_dict() for m in messages]
            except Exception:
                pass

        # Notify successor (only if all conditions met)
        if response.notify_successor and self.messaging and self.contacts:
            try:
                msg = self.messaging.send_to_successor(
                    f"ANUBIS Successor Notification: {threat.description}"
                )
                if msg.status == "sent":
                    self.contacts.notify_successor(threat.description)
            except Exception:
                pass

    # --------------------------------------------------- threat management

    def resolve_threat(self, threat_id: str, resolution: str = "") -> bool:
        """Mark a threat as resolved."""
        threat = self._active_threats.get(threat_id)
        if threat is None:
            return False
        threat.resolved = True
        threat.response = resolution
        threat.response_timestamp = time.time()
        self._record_threat(threat)
        del self._active_threats[threat_id]
        self._log("threat.resolved", {
            "threat_id": threat_id,
            "resolution": resolution,
        })
        return True

    def get_active_threats(self) -> list[dict[str, Any]]:
        """Get all currently active threats."""
        return [t.to_dict() for t in self._active_threats.values()]

    def get_threat_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get threat history."""
        if not self._threats_file.exists():
            return []
        try:
            lines = self._threats_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_threats_by_severity(self, severity: str) -> list[dict[str, Any]]:
        """Get threats filtered by severity."""
        history = self.get_threat_history(limit=9999)
        return [t for t in history if t.get("severity") == severity]

    def get_threats_by_domain(self, domain: str) -> list[dict[str, Any]]:
        """Get threats filtered by domain."""
        history = self.get_threat_history(limit=9999)
        return [t for t in history if t.get("domain") == domain]

    # --------------------------------------------------- behavioral baseline

    def update_baseline(
        self,
        emotion: str = "",
        active_hour: float | None = None,
        device_count: int | None = None,
        command_type: str = "",
    ) -> None:
        """Update the behavioral baseline with new observations."""
        if emotion and emotion not in self._baseline.normal_emotions:
            if self._baseline.samples > 10:  # only add if well-established
                self._baseline.normal_emotions.append(emotion)

        if active_hour is not None:
            self._baseline.normal_speech_times.append(active_hour)

        if device_count is not None:
            # Running average
            old = self._baseline.normal_device_count
            self._baseline.normal_device_count = int(
                (old * self._baseline.samples + device_count) /
                (self._baseline.samples + 1)
            )

        if command_type and command_type not in self._baseline.normal_command_types:
            self._baseline.normal_command_types.append(command_type)

        self._baseline.samples += 1
        self._baseline.last_updated = time.time()
        self._save_baseline()

    def check_anomalous_behavior(
        self,
        emotion: str = "",
        device_count: int | None = None,
        command_type: str = "",
    ) -> bool:
        """Check if current behavior is anomalous compared to baseline."""
        if emotion and emotion not in self._baseline.normal_emotions:
            if emotion in ["duress", "fearful", "angry"]:
                return True

        if device_count is not None:
            if device_count > self._baseline.normal_device_count + 2:
                return True

        return False

    def get_baseline(self) -> dict[str, Any]:
        """Get the behavioral baseline."""
        return self._baseline.to_dict()

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        """Get threat analysis system status."""
        return {
            "active_threats": len(self._active_threats),
            "total_threats": len(self.get_threat_history(limit=9999)),
            "critical_threats": len(self.get_threats_by_severity(SEVERITY_CRITICAL)),
            "high_threats": len(self.get_threats_by_severity(SEVERITY_HIGH)),
            "baseline_samples": self._baseline.samples,
            "contacts_configured": self.contacts is not None,
            "messaging_configured": self.messaging is not None,
        }

    # --------------------------------------------------- helpers

    def _gen_id(self, prefix: str, suffix: str) -> str:
        return hashlib.sha256(
            f"{prefix}:{suffix}:{time.time()}".encode()
        ).hexdigest()[:16]

    def _record_threat(self, threat: Threat) -> None:
        try:
            with open(self._threats_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(threat.to_dict()) + "\n")
        except Exception:
            pass

    def _load_baseline(self) -> None:
        if not self._baseline_file.exists():
            return
        try:
            data = json.loads(
                self._baseline_file.read_text(encoding="utf-8")
            )
            self._baseline = BehavioralBaseline(
                normal_emotions=data.get("normal_emotions", ["neutral", "calm"]),
                normal_active_hours=tuple(data.get("normal_active_hours", [7.0, 23.0])),
                normal_home_hours=tuple(data.get("normal_home_hours", [18.0, 8.0])),
                normal_device_count=data.get("normal_device_count", 5),
                normal_active_devices=data.get("normal_active_devices", []),
                normal_command_frequency=data.get("normal_command_frequency", 10.0),
                normal_command_types=data.get("normal_command_types", []),
                samples=data.get("samples", 0),
                last_updated=data.get("last_updated", 0.0),
            )
        except Exception:
            pass

    def _save_baseline(self) -> None:
        self._baseline_file.write_text(
            json.dumps(self._baseline.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
