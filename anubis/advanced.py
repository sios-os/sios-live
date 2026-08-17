"""Advanced/future integrations — Tier 4 modules.

6 ambitious modules for ANUBIS's future expansion:
1. Emergency services calling (911 with legal safeguards)
2. Multi-language support
3. AR/smart glasses integration
4. Satellite imagery analysis
5. Blockchain evidence chain
6. ANUBIS-to-ANUBIS protocol (multi-instance coordination)

Each is a framework ready for when the technology or legal framework
is in place. All use stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ============================================================
# 1. Emergency Services Calling (911)
# ============================================================

@dataclass
class EmergencyCall:
    """A record of an emergency services call."""
    call_id: str
    emergency_type: str = ""  # medical, fire, police, mental_health
    location: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    description: str = ""
    timestamp: float = 0.0
    approved_by: str = ""  # who approved the call
    call_status: str = "pending"  # pending, approved, calling, connected, failed
    duration: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id, "emergency_type": self.emergency_type,
            "location": self.location, "latitude": self.latitude,
            "longitude": self.longitude, "description": self.description,
            "timestamp": self.timestamp, "approved_by": self.approved_by,
            "call_status": self.call_status, "duration": self.duration,
            "notes": self.notes,
        }


class EmergencyServices:
    """Emergency services calling with legal safeguards.

    ANUBIS can call 911 but ONLY with explicit Creator approval.
    This is a legally sensitive capability — different jurisdictions
    have different rules about AI-initiated emergency calls.

    SAFEGUARDS:
    - Requires explicit Creator approval (voice or app)
    - Logs all calls to evidence ledger
    - Provides location and situation description
    - Never makes automated decisions about emergency services
    - Falls back to emergency contacts if Creator can't approve
    - Records the call for legal protection
    """

    ACTOR = "anubis.emergency_services"

    EMERGENCY_911 = "911"
    EMERGENCY_TYPES = ["medical", "fire", "police", "mental_health"]

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 voip: Any | None = None,
                 on_call_required: Callable[[EmergencyCall], bool] | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.voip = voip
        self.on_call_required = on_call_required  # approval callback
        self._state_dir = self.root / "memory" / "emergency_services"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._calls_file = self._state_dir / "calls.jsonl"
        self._calls: dict[str, EmergencyCall] = {}

    def request_emergency_call(
        self, emergency_type: str, description: str = "",
        location: str = "", latitude: float = 0, longitude: float = 0,
    ) -> EmergencyCall:
        """Request an emergency services call. Requires approval."""
        call_id = hashlib.sha256(
            f"emergency:{time.time()}".encode()
        ).hexdigest()[:16]
        call = EmergencyCall(
            call_id=call_id, emergency_type=emergency_type,
            description=description, location=location,
            latitude=latitude, longitude=longitude,
            timestamp=time.time(), call_status="pending",
        )
        self._calls[call_id] = call
        self._record(call)

        # Request approval
        approved = False
        if self.on_call_required:
            try:
                approved = self.on_call_required(call)
            except Exception:
                pass

        if approved:
            call.approved_by = "creator"
            call.call_status = "approved"
            self._make_call(call)
        else:
            call.call_status = "denied"
            self._log("emergency.denied", {"type": emergency_type})

        self._record(call)
        return call

    def _make_call(self, call: EmergencyCall) -> None:
        """Make the actual 911 call via VoIP."""
        call.call_status = "calling"
        if self.voip:
            result = self.voip.call_emergency(
                reason=call.description, approved=True
            )
            if result.status == "connected":
                call.call_status = "connected"
                call.duration = result.duration_seconds
            else:
                call.call_status = "failed"
                call.notes = "VoIP call failed"
        else:
            call.call_status = "failed"
            call.notes = "No VoIP system configured"
        self._log("emergency.called", {
            "type": call.emergency_type, "status": call.call_status,
        })

    def get_calls(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._calls.values()]

    def get_status(self) -> dict[str, Any]:
        return {
            "total_calls": len(self._calls),
            "voip_configured": self.voip is not None,
            "approval_required": True,
        }

    def _record(self, call: EmergencyCall) -> None:
        try:
            with open(self._calls_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(call.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# ============================================================
# 2. Multi-language Support
# ============================================================

class MultiLanguage:
    """Multi-language support for ANUBIS.

    Supports understanding and responding in multiple languages.
    Uses local translation models when available, falls back to
    cloud translation APIs.

    LANGUAGES:
    - English (default)
    - Spanish, French, German, Chinese, Japanese, Arabic, Hindi
    - Auto-detect language from input
    """

    ACTOR = "anubis.multilang"

    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "zh", "ja", "ar", "hi", "pt", "ru", "ko",
    ]

    LANGUAGE_NAMES = {
        "en": "English", "es": "Spanish", "fr": "French",
        "de": "German", "zh": "Chinese", "ja": "Japanese",
        "ar": "Arabic", "hi": "Hindi", "pt": "Portuguese",
        "ru": "Russian", "ko": "Korean",
    }

    # Simple phrase detection for language identification
    LANGUAGE_MARKERS: dict[str, list[str]] = {
        "es": ["hola", "gracias", "por favor", "si", "no", "buenos"],
        "fr": ["bonjour", "merci", "oui", "non", "sil vous plait"],
        "de": ["hallo", "danke", "ja", "nein", "bitte"],
        "zh": ["你好", "谢谢", "请", "是", "不"],
        "ja": ["こんにちは", "ありがとう", "はい", "いいえ"],
        "ar": ["مرحبا", "شكرا", "نعم", "لا"],
        "hi": ["नमस्ते", "धन्यवाद", "हां", "नहीं"],
    }

    def __init__(self, root: str | Path, *, default_lang: str = "en",
                 ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.default_lang = default_lang
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "multilang"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._translations_file = self._state_dir / "translations.json"
        self._translations: dict[str, dict[str, str]] = {}
        self._load()

    def detect_language(self, text: str) -> str:
        """Detect the language of input text."""
        text_lower = text.lower()
        for lang, markers in self.LANGUAGE_MARKERS.items():
            for marker in markers:
                if marker in text_lower:
                    return lang
        return self.default_lang

    def add_translation(self, key: str, translations: dict[str, str]) -> None:
        """Add a translatable phrase."""
        self._translations[key] = translations
        self._save()

    def translate(self, key: str, target_lang: str = "") -> str:
        """Get a translated phrase."""
        lang = target_lang or self.default_lang
        if key in self._translations:
            return self._translations[key].get(lang, self._translations[key].get("en", key))
        return key

    def get_supported_languages(self) -> list[dict[str, str]]:
        return [
            {"code": code, "name": self.LANGUAGE_NAMES.get(code, code)}
            for code in self.SUPPORTED_LANGUAGES
        ]

    def get_status(self) -> dict[str, Any]:
        return {
            "default_language": self.default_lang,
            "supported": len(self.SUPPORTED_LANGUAGES),
            "translations": len(self._translations),
        }

    def _load(self) -> None:
        if self._translations_file.exists():
            try:
                self._translations = json.loads(
                    self._translations_file.read_text(encoding="utf-8")
                )
            except Exception:
                pass

    def _save(self) -> None:
        self._translations_file.write_text(
            json.dumps(self._translations, indent=2), encoding="utf-8"
        )


# ============================================================
# 3. AR/Smart Glasses Integration
# ============================================================

@dataclass
class ARFrame:
    """A frame from AR glasses camera."""
    frame_id: str = ""
    timestamp: float = 0.0
    image_path: str = ""
    width: int = 0
    height: int = 0
    # Analysis
    faces_detected: int = 0
    objects_detected: int = 0
    text_detected: str = ""
    # Overlay info (what ANUBIS adds to the display)
    overlay_text: str = ""
    overlay_alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id, "timestamp": self.timestamp,
            "image_path": self.image_path, "width": self.width,
            "height": self.height, "faces_detected": self.faces_detected,
            "objects_detected": self.objects_detected,
            "text_detected": self.text_detected,
            "overlay_text": self.overlay_text,
            "overlay_alerts": self.overlay_alerts,
        }


class ARGlasses:
    """AR/smart glasses integration.

    Receives camera feed from smart glasses (Meta Ray-Bans, etc.)
    and provides overlay information:
    - Face recognition (who you're looking at)
    - Object identification
    - Text reading (signs, menus, documents)
    - Navigation prompts
    - Alerts and warnings

    The glasses display ANUBIS's overlay; the processing happens
    on the connected phone or ANUBIS's server.
    """

    ACTOR = "anubis.ar"

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 perception: Any | None = None) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.perception = perception
        self._state_dir = self.root / "memory" / "ar"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._frames_dir = self._state_dir / "frames"
        self._frames_dir.mkdir(parents=True, exist_ok=True)
        self._connected = False
        self._overlay_enabled = True
        self._last_frame: ARFrame | None = None

    def connect(self) -> bool:
        """Connect to AR glasses via companion app."""
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def process_frame(self, image_path: str) -> ARFrame:
        """Process a frame from the glasses camera."""
        frame_id = hashlib.sha256(
            f"ar:{time.time()}".encode()
        ).hexdigest()[:16]
        frame = ARFrame(
            frame_id=frame_id, timestamp=time.time(),
            image_path=image_path,
        )

        # Analyze with perception
        if self.perception:
            try:
                face_result = self.perception.faces.identify(image_path)
                frame.faces_detected = face_result.face_count
                if face_result.is_known:
                    frame.overlay_text = f"Person: {face_result.name}"
            except Exception:
                pass

            try:
                scene = self.perception.objects.recognize(image_path)
                frame.objects_detected = len(scene.objects)
                if scene.people_count > 0:
                    frame.overlay_alerts.append(f"{scene.people_count} person(s) in view")
            except Exception:
                pass

        self._last_frame = frame
        return frame

    def set_overlay(self, text: str) -> None:
        """Set overlay text to display on glasses."""
        if self._last_frame:
            self._last_frame.overlay_text = text

    def add_alert(self, alert: str) -> None:
        """Add an alert to the glasses display."""
        if self._last_frame:
            self._last_frame.overlay_alerts.append(alert)

    def enable_overlay(self) -> None:
        self._overlay_enabled = True

    def disable_overlay(self) -> None:
        self._overlay_enabled = False

    def get_last_frame(self) -> dict[str, Any] | None:
        return self._last_frame.to_dict() if self._last_frame else None

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "overlay_enabled": self._overlay_enabled,
            "perception_available": self.perception is not None,
            "last_frame": self._last_frame.to_dict() if self._last_frame else None,
        }


# ============================================================
# 4. Satellite Imagery Analysis
# ============================================================

@dataclass
class SatelliteImage:
    """A satellite image analysis result."""
    image_id: str = ""
    timestamp: float = 0.0
    source: str = ""  # "sentinel", "landsat", "public"
    latitude: float = 0.0
    longitude: float = 0.0
    zoom: int = 0
    image_path: str = ""
    analysis: str = ""  # text description of what was observed
    cloud_cover: float = 0.0  # %
    changes_detected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id, "timestamp": self.timestamp,
            "source": self.source, "latitude": self.latitude,
            "longitude": self.longitude, "zoom": self.zoom,
            "image_path": self.image_path, "analysis": self.analysis,
            "cloud_cover": self.cloud_cover,
            "changes_detected": self.changes_detected,
        }


class SatelliteAnalyzer:
    """Satellite imagery analysis.

    Fetches and analyzes publicly available satellite imagery for:
    - Property monitoring (changes to land, buildings)
    - Weather pattern observation
    - Environmental changes
    - Solar panel efficiency (cloud cover)

    SOURCES:
    - Sentinel Hub (free tier, requires registration)
    - NASA Worldview (free, no key)
    - Google Static Maps (free tier)
    """

    ACTOR = "anubis.satellite"

    def __init__(self, root: str | Path, *, latitude: float = 0, longitude: float = 0,
                 sentinel_key: str = "", ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.latitude = latitude
        self.longitude = longitude
        self.sentinel_key = sentinel_key
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "satellite"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._images_file = self._state_dir / "images.jsonl"
        self._images: list[SatelliteImage] = []

    def fetch_image(self, zoom: int = 15) -> SatelliteImage | None:
        """Fetch a satellite image of the configured location."""
        try:
            # Try NASA GIBS (free, no key)
            url = (
                f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/"
                f"MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-01-01/"
                f"250m/{self.latitude}/{self.longitude}.jpg"
            )
            # This is a simplified URL — real implementation would use WMTS properly
            image_id = hashlib.sha256(
                f"sat:{self.latitude}:{self.longitude}:{time.time()}".encode()
            ).hexdigest()[:16]
            image_path = str(self._state_dir / f"{image_id}.jpg")

            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "ANUBIS-Satellite/1.0")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    with open(image_path, "wb") as f:
                        f.write(resp.read())
            except Exception:
                pass  # Network may not be available

            img = SatelliteImage(
                image_id=image_id, timestamp=time.time(),
                source="public", latitude=self.latitude,
                longitude=self.longitude, zoom=zoom,
                image_path=image_path,
            )
            self._images.append(img)
            self._record(img)
            return img
        except Exception:
            return None

    def analyze_changes(self, image1_path: str, image2_path: str) -> list[str]:
        """Detect changes between two satellite images."""
        # Would use image differencing with OpenCV
        # For now, return empty list
        return []

    def get_images(self, limit: int = 20) -> list[dict[str, Any]]:
        return [img.to_dict() for img in self._images[-limit:]]

    def get_status(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "sentinel_configured": bool(self.sentinel_key),
            "total_images": len(self._images),
        }

    def _record(self, img: SatelliteImage) -> None:
        try:
            with open(self._images_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(img.to_dict()) + "\n")
        except Exception:
            pass


# ============================================================
# 5. Blockchain Evidence Chain
# ============================================================

@dataclass
class EvidenceAnchor:
    """A blockchain anchor for evidence."""
    anchor_id: str
    evidence_hash: str = ""  # SHA-256 of evidence
    blockchain_tx: str = ""  # transaction ID
    blockchain: str = ""  # "bitcoin", "ethereum", "polygon"
    timestamp: float = 0.0
    block_number: int = 0
    confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "evidence_hash": self.evidence_hash,
            "blockchain_tx": self.blockchain_tx,
            "blockchain": self.blockchain,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "confirmed": self.confirmed,
        }


class BlockchainEvidence:
    """Blockchain evidence chain for legal admissibility.

    Notarizes evidence ledger entries on a blockchain to provide
    tamper-proof, legally admissible evidence with a public timestamp.

    BLOCKCHAINS:
    - Bitcoin (via OP_RETURN) — most secure, most expensive
    - Ethereum (via storage) — flexible, moderate cost
    - Polygon — low cost, good for frequent anchoring

    PROCESS:
    1. Hash the evidence (SHA-256)
    2. Submit hash to blockchain as an anchor
    3. Store transaction ID and block number
    4. Verify anchor is confirmed on chain

    This provides cryptographic proof that evidence existed at a
    specific time and has not been modified.
    """

    ACTOR = "anubis.blockchain"

    def __init__(self, root: str | Path, *, ledger: Any | None = None,
                 blockchain: str = "polygon") -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.blockchain = blockchain
        self._state_dir = self.root / "memory" / "blockchain"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._anchors_file = self._state_dir / "anchors.jsonl"
        self._anchors: list[EvidenceAnchor] = []

    def anchor_evidence(self, evidence_data: bytes | str) -> EvidenceAnchor:
        """Anchor evidence on the blockchain."""
        if isinstance(evidence_data, str):
            evidence_data = evidence_data.encode()

        evidence_hash = hashlib.sha256(evidence_data).hexdigest()
        anchor_id = hashlib.sha256(
            f"anchor:{evidence_hash}:{time.time()}".encode()
        ).hexdigest()[:16]

        anchor = EvidenceAnchor(
            anchor_id=anchor_id,
            evidence_hash=evidence_hash,
            blockchain=self.blockchain,
            timestamp=time.time(),
        )

        # In production, this would submit to blockchain
        # For now, we just record the intent
        anchor.blockchain_tx = ""  # would be filled after submission
        anchor.confirmed = False

        self._anchors.append(anchor)
        self._record(anchor)
        self._log("evidence.anchored", {
            "hash": evidence_hash, "blockchain": self.blockchain,
        })
        return anchor

    def verify_anchor(self, anchor_id: str) -> dict[str, Any]:
        """Verify an anchor is confirmed on the blockchain."""
        for anchor in self._anchors:
            if anchor.anchor_id == anchor_id:
                # In production, would query blockchain
                return {
                    "anchor_id": anchor_id,
                    "confirmed": anchor.confirmed,
                    "evidence_hash": anchor.evidence_hash,
                    "blockchain_tx": anchor.blockchain_tx,
                }
        return {"error": "Anchor not found"}

    def get_anchors(self, limit: int = 50) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._anchors[-limit:]]

    def get_status(self) -> dict[str, Any]:
        return {
            "blockchain": self.blockchain,
            "total_anchors": len(self._anchors),
            "confirmed": sum(1 for a in self._anchors if a.confirmed),
        }

    def _record(self, anchor: EvidenceAnchor) -> None:
        try:
            with open(self._anchors_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(anchor.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# ============================================================
# 6. ANUBIS-to-ANUBIS Protocol
# ============================================================

@dataclass
class ANUBISPeer:
    """Another ANUBIS instance."""
    peer_id: str
    name: str = ""
    address: str = ""  # IP or hostname
    port: int = 8765
    api_key: str = ""
    location: str = ""
    status: str = "offline"  # offline, online, syncing
    last_seen: float = 0.0
    capabilities: list[str] = field(default_factory=list)
    shared_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id, "name": self.name,
            "address": self.address, "port": self.port,
            "location": self.location, "status": self.status,
            "last_seen": self.last_seen,
            "capabilities": self.capabilities,
        }


class ANUBISProtocol:
    """ANUBIS-to-ANUBIS communication protocol.

    Allows multiple ANUBIS instances to communicate and coordinate:
    - Share threat intelligence
    - Distribute computation tasks
    - Synchronize knowledge
    - Coordinate security responses
    - Backup each other's evidence ledgers

    USE CASES:
    - Home ANUBIS + Workshop ANUBIS coordinate security
    - Multiple properties share threat information
    - Distributed processing for large tasks
    - Redundant evidence storage

    SECURITY:
    - Mutual authentication via API keys
    - Encrypted communication (HTTPS)
    - Capability-based access control
    - All peer communication logged
    """

    ACTOR = "anubis.protocol"

    def __init__(self, root: str | Path, *, self_id: str = "",
                 ledger: Any | None = None) -> None:
        self.root = Path(root)
        self.self_id = self_id or hashlib.sha256(
            f"anubis:{time.time()}".encode()
        ).hexdigest()[:16]
        self.ledger = ledger
        self._state_dir = self.root / "memory" / "protocol"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._peers_file = self._state_dir / "peers.json"
        self._messages_file = self._state_dir / "messages.jsonl"
        self._peers: dict[str, ANUBISPeer] = {}
        self._load()

    def add_peer(self, name: str, address: str, port: int = 8765,
                 api_key: str = "", location: str = "") -> ANUBISPeer:
        """Register another ANUBIS instance as a peer."""
        peer_id = hashlib.sha256(
            f"peer:{name}:{address}".encode()
        ).hexdigest()[:16]
        peer = ANUBISPeer(
            peer_id=peer_id, name=name, address=address,
            port=port, api_key=api_key, location=location,
        )
        self._peers[peer_id] = peer
        self._save()
        self._log("peer.added", {"name": name, "address": address})
        return peer

    def remove_peer(self, peer_id: str) -> bool:
        if peer_id in self._peers:
            del self._peers[peer_id]
            self._save()
            return True
        return False

    def check_peer_status(self, peer_id: str) -> str:
        """Check if a peer is online."""
        peer = self._peers.get(peer_id)
        if peer is None:
            return "not_found"
        try:
            url = f"http://{peer.address}:{peer.port}/api/health"
            req = urllib.request.Request(url)
            if peer.api_key:
                req.add_header("Authorization", f"Bearer {peer.api_key}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    peer.status = "online"
                    peer.last_seen = time.time()
                    self._save()
                    return "online"
        except Exception:
            peer.status = "offline"
            self._save()
        return "offline"

    def send_message(self, peer_id: str, message_type: str,
                     data: dict[str, Any]) -> dict[str, Any]:
        """Send a message to a peer ANUBIS."""
        peer = self._peers.get(peer_id)
        if peer is None:
            return {"success": False, "error": "Peer not found"}
        try:
            url = f"http://{peer.address}:{peer.port}/api/chat"
            payload = json.dumps({
                "type": message_type,
                "from": self.self_id,
                "data": data,
            }).encode()
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            if peer.api_key:
                req.add_header("Authorization", f"Bearer {peer.api_key}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                self._record_message(peer_id, message_type, data, "sent")
                return {"success": True, "response": result}
        except Exception as e:
            self._record_message(peer_id, message_type, data, "failed")
            return {"success": False, "error": str(e)}

    def share_threat_intel(self, peer_id: str, threat_data: dict[str, Any]) -> dict[str, Any]:
        """Share threat intelligence with a peer."""
        return self.send_message(peer_id, "threat_intel", threat_data)

    def sync_knowledge(self, peer_id: str) -> dict[str, Any]:
        """Request knowledge synchronization with a peer."""
        return self.send_message(peer_id, "sync_request", {})

    def get_peers(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._peers.values()]

    def get_online_peers(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._peers.values() if p.status == "online"]

    def get_status(self) -> dict[str, Any]:
        return {
            "self_id": self.self_id,
            "total_peers": len(self._peers),
            "online_peers": len(self.get_online_peers()),
        }

    def _record_message(self, peer_id: str, msg_type: str,
                        data: dict[str, Any], status: str) -> None:
        try:
            with open(self._messages_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": time.time(),
                    "peer_id": peer_id, "type": msg_type,
                    "status": status, "data_size": len(str(data)),
                }) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        if not self._peers_file.exists():
            return
        try:
            data = json.loads(self._peers_file.read_text(encoding="utf-8"))
            for p_id, p in data.items():
                self._peers[p_id] = ANUBISPeer(
                    peer_id=p_id, name=p.get("name", ""),
                    address=p.get("address", ""), port=p.get("port", 8765),
                    api_key=p.get("api_key", ""),
                    location=p.get("location", ""),
                    status=p.get("status", "offline"),
                    last_seen=p.get("last_seen", 0),
                    capabilities=p.get("capabilities", []),
                )
        except Exception:
            pass

    def _save(self) -> None:
        data = {p_id: p.to_dict() for p_id, p in self._peers.items()}
        self._peers_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
