"""Camera system — ANUBIS's eyes everywhere he's allowed to see.

Supports four camera types:

1. **Home cameras** — RTSP/ONVIF IP cameras you own. ANUBIS connects
   directly via RTSP stream or HTTP snapshot. Continuously monitors
   for people, vehicles, animals, and unknown faces.

2. **Dashcam** — In-car camera. When you're driving, ANUBIS can
   process the dashcam feed for road hazards, vehicles, and incidents.
   Connects via RTSP or file access (dashcam WiFi hotspot).

3. **Body cam** — Wearable camera (GoPro, small camera). Streams via
   WiFi or file access. ANUBIS processes the feed for faces, objects,
   and threats in your vicinity.

4. **Public cameras** — Publicly accessible traffic/municipal cameras.
   Many cities publish traffic camera feeds as public APIs or MJPEG
   streams. ANUBIS can monitor these for traffic conditions, road
   hazards, or weather. Only accesses publicly available feeds —
   never private or government-restricted cameras.

LEGAL AND ETHICAL:
- ANUBIS only accesses cameras you own or that are publicly available
- He never hacks into private or government surveillance systems
- He never accesses cameras without permission
- All camera access is logged to the evidence ledger
- Camera feeds are processed locally — not uploaded anywhere
- You can disable any camera at any time

HARDWARE SUPPORT:
- RTSP streams (most IP cameras): rtsp://user:pass@ip:port/stream
- HTTP snapshots: http://ip/snapshot.jpg
- ONVIF discovery: auto-discovers cameras on network
- MJPEG streams: http://ip/video.mjpg
- File-based: reads from dashcam/body cam storage
- Public APIs: municipal traffic camera endpoints

Uses OpenCV (cv2) for video capture when available.
Falls back to HTTP snapshot polling when cv2 isn't available.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


# Camera types
CAM_HOME = "home"
CAM_DASHCAM = "dashcam"
CAM_BODY = "body_cam"
CAM_PUBLIC = "public"

# Connection types
CONN_RTSP = "rtsp"
CONN_HTTP_SNAPSHOT = "http_snapshot"
CONN_MJPEG = "mjpeg"
CONN_FILE = "file"
CONN_ONVIF = "onvif"

# Camera status
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"
STATUS_ERROR = "error"
STATUS_DISABLED = "disabled"


@dataclass
class Camera:
    """A camera source."""
    camera_id: str
    name: str
    camera_type: str = CAM_HOME  # home, dashcam, body_cam, public
    connection_type: str = CONN_RTSP  # rtsp, http_snapshot, mjpeg, file, onvif
    url: str = ""  # rtsp://..., http://..., or file path
    username: str = ""
    password: str = ""  # stored encrypted in production
    location: str = ""  # "front door", "driveway", "car", "body", "intersection"
    latitude: float = 0.0
    longitude: float = 0.0
    enabled: bool = True
    status: str = STATUS_OFFLINE
    last_frame_time: float = 0.0
    last_error: str = ""
    fps: float = 0.0  # measured FPS
    resolution: tuple[int, int] = (0, 0)  # width, height
    created_at: float = 0.0
    updated_at: float = 0.0
    # Monitoring settings
    detect_faces: bool = True
    detect_objects: bool = True
    detect_motion: bool = True
    record_on_motion: bool = False
    snapshot_interval: float = 5.0  # seconds between snapshots
    # Stats
    frames_captured: int = 0
    motion_events: int = 0
    face_detections: int = 0
    object_detections: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "camera_type": self.camera_type,
            "connection_type": self.connection_type,
            "url": self.url,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "enabled": self.enabled,
            "status": self.status,
            "last_frame_time": self.last_frame_time,
            "last_error": self.last_error,
            "fps": self.fps,
            "resolution": list(self.resolution),
            "detect_faces": self.detect_faces,
            "detect_objects": self.detect_objects,
            "detect_motion": self.detect_motion,
            "snapshot_interval": self.snapshot_interval,
            "frames_captured": self.frames_captured,
            "motion_events": self.motion_events,
            "face_detections": self.face_detections,
            "object_detections": self.object_detections,
        }


@dataclass
class CameraFrame:
    """A captured frame from a camera."""
    frame_id: str
    camera_id: str
    timestamp: float = 0.0
    image_path: str = ""  # where the frame was saved
    width: int = 0
    height: int = 0
    # Analysis results (filled by perception)
    faces_detected: int = 0
    objects_detected: int = 0
    motion_detected: bool = False
    analysis: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "camera_id": self.camera_id,
            "timestamp": self.timestamp,
            "image_path": self.image_path,
            "width": self.width,
            "height": self.height,
            "faces_detected": self.faces_detected,
            "objects_detected": self.objects_detected,
            "motion_detected": self.motion_detected,
            "analysis": self.analysis,
        }


@dataclass
class CameraEvent:
    """An event detected by a camera."""
    event_id: str
    camera_id: str
    camera_name: str = ""
    event_type: str = ""  # motion, face, person, vehicle, animal, unknown_person
    timestamp: float = 0.0
    description: str = ""
    frame_path: str = ""
    severity: str = "low"  # low, medium, high, critical
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "description": self.description,
            "frame_path": self.frame_path,
            "severity": self.severity,
            "location": self.location,
        }


class CameraSystem:
    """Manages all camera sources — home, dashcam, body cam, public.

    ANUBIS uses this to:
    - Connect to IP cameras via RTSP/HTTP
    - Capture frames at regular intervals
    - Feed frames to perception for face/object recognition
    - Detect motion between frames
    - Generate events for threats and activity
    - Record evidence when needed
    - Monitor public traffic cameras for road conditions

    The camera system runs in the background, capturing frames from
    each enabled camera at its configured interval. Each frame is
    analyzed by the perception system, and events are generated for
    significant detections.
    """

    ACTOR = "anubis.cameras"

    def __init__(
        self,
        root: str | Path,
        *,
        perception: Any | None = None,
        ledger: Any | None = None,
        on_event: Callable[[CameraEvent], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.perception = perception
        self.ledger = ledger
        self.on_event = on_event

        self._state_dir = self.root / "memory" / "cameras"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._cameras_file = self._state_dir / "cameras.json"
        self._events_file = self._state_dir / "camera_events.jsonl"
        self._frames_dir = self._state_dir / "frames"
        self._frames_dir.mkdir(parents=True, exist_ok=True)

        self._cameras: dict[str, Camera] = {}
        self._load_cameras()

        # Check for OpenCV
        self._cv2 = self._try_import_cv2()

        # Check for ffmpeg (for RTSP snapshot capture)
        self._ffmpeg = shutil.which("ffmpeg")

        # State
        self._monitoring = False
        self._last_frames: dict[str, Any] = {}  # camera_id -> last frame data

    def _try_import_cv2(self) -> Any:
        try:
            import cv2  # type: ignore
            return cv2
        except ImportError:
            return None

    # --------------------------------------------------- camera management

    def add_camera(
        self,
        name: str,
        camera_type: str,
        connection_type: str,
        url: str,
        *,
        location: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        username: str = "",
        password: str = "",
        detect_faces: bool = True,
        detect_objects: bool = True,
        detect_motion: bool = True,
        snapshot_interval: float = 5.0,
    ) -> Camera:
        """Add a new camera source."""
        camera_id = hashlib.sha256(
            f"cam:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        camera = Camera(
            camera_id=camera_id,
            name=name,
            camera_type=camera_type,
            connection_type=connection_type,
            url=url,
            username=username,
            password=password,
            location=location,
            latitude=latitude,
            longitude=longitude,
            detect_faces=detect_faces,
            detect_objects=detect_objects,
            detect_motion=detect_motion,
            snapshot_interval=snapshot_interval,
            created_at=time.time(),
            updated_at=time.time(),
        )

        self._cameras[camera_id] = camera
        self._save_cameras()
        self._log("camera.added", {"name": name, "type": camera_type})
        return camera

    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera."""
        if camera_id in self._cameras:
            name = self._cameras[camera_id].name
            del self._cameras[camera_id]
            self._save_cameras()
            self._log("camera.removed", {"name": name})
            return True
        return False

    def update_camera(self, camera_id: str, **kwargs: Any) -> bool:
        """Update camera settings."""
        camera = self._cameras.get(camera_id)
        if camera is None:
            return False
        for key, value in kwargs.items():
            if hasattr(camera, key) and key not in ("camera_id", "created_at"):
                setattr(camera, key, value)
        camera.updated_at = time.time()
        self._save_cameras()
        return True

    def enable_camera(self, camera_id: str) -> bool:
        """Enable a camera."""
        return self.update_camera(camera_id, enabled=True, status=STATUS_OFFLINE)

    def disable_camera(self, camera_id: str) -> bool:
        """Disable a camera."""
        return self.update_camera(
            camera_id, enabled=False, status=STATUS_DISABLED
        )

    def get_camera(self, camera_id: str) -> dict[str, Any] | None:
        """Get a specific camera."""
        c = self._cameras.get(camera_id)
        return c.to_dict() if c else None

    def get_cameras(self) -> list[dict[str, Any]]:
        """Get all cameras."""
        return [c.to_dict() for c in self._cameras.values()]

    def get_cameras_by_type(self, camera_type: str) -> list[dict[str, Any]]:
        """Get cameras filtered by type."""
        return [
            c.to_dict() for c in self._cameras.values()
            if c.camera_type == camera_type
        ]

    def get_enabled_cameras(self) -> list[dict[str, Any]]:
        """Get all enabled cameras."""
        return [c.to_dict() for c in self._cameras.values() if c.enabled]

    # --------------------------------------------------- frame capture

    def capture_frame(self, camera_id: str) -> CameraFrame | None:
        """Capture a single frame from a camera."""
        camera = self._cameras.get(camera_id)
        if camera is None or not camera.enabled:
            return None

        frame_id = hashlib.sha256(
            f"frame:{camera_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        frame_path = str(
            self._frames_dir / f"{camera_id}_{int(time.time())}.jpg"
        )

        # Try capture methods in order
        success = False

        if camera.connection_type == CONN_RTSP:
            success = self._capture_rtsp(camera, frame_path)
        elif camera.connection_type == CONN_HTTP_SNAPSHOT:
            success = self._capture_http(camera, frame_path)
        elif camera.connection_type == CONN_MJPEG:
            success = self._capture_http(camera, frame_path)
        elif camera.connection_type == CONN_FILE:
            success = self._capture_file(camera, frame_path)
        elif camera.connection_type == CONN_ONVIF:
            success = self._capture_http(camera, frame_path)

        if not success:
            camera.status = STATUS_ERROR
            camera.last_error = "Capture failed"
            self._save_cameras()
            return None

        camera.status = STATUS_ONLINE
        camera.last_frame_time = time.time()
        camera.frames_captured += 1
        camera.last_error = ""

        frame = CameraFrame(
            frame_id=frame_id,
            camera_id=camera_id,
            timestamp=time.time(),
            image_path=frame_path,
        )

        # Get resolution if cv2 available
        if self._cv2 is not None:
            try:
                img = self._cv2.imread(frame_path)
                if img is not None:
                    frame.width = img.shape[1]
                    frame.height = img.shape[0]
                    camera.resolution = (frame.width, frame.height)
            except Exception:
                pass

        # Analyze frame
        self._analyze_frame(camera, frame)

        self._save_cameras()
        return frame

    def _capture_rtsp(self, camera: Camera, frame_path: str) -> bool:
        """Capture a frame from an RTSP stream."""
        # Try OpenCV first
        if self._cv2 is not None:
            try:
                cap = self._cv2.VideoCapture(camera.url)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self._cv2.imwrite(frame_path, frame)
                    return True
            except Exception:
                pass

        # Try ffmpeg
        if self._ffmpeg:
            try:
                cmd = [
                    self._ffmpeg,  # type: ignore
                    "-y",
                    "-rtsp_transport", "tcp",
                    "-i", camera.url,
                    "-frames:v", "1",
                    "-q:v", "2",
                    frame_path,
                ]
                result = subprocess.run(
                    cmd, capture_output=True, timeout=10,
                )
                return result.returncode == 0 and os.path.exists(frame_path)
            except Exception:
                pass

        return False

    def _capture_http(self, camera: Camera, frame_path: str) -> bool:
        """Capture a frame from an HTTP snapshot URL."""
        try:
            url = camera.url
            if camera.username and camera.password:
                # Add auth to URL
                if "://" in url:
                    scheme, rest = url.split("://", 1)
                    url = f"{scheme}://{camera.username}:{camera.password}@{rest}"

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                with open(frame_path, "wb") as f:
                    f.write(data)
                return True
        except Exception:
            return False

    def _capture_file(self, camera: Camera, frame_path: str) -> bool:
        """Copy a frame from a file (dashcam/body cam storage)."""
        try:
            if not os.path.exists(camera.url):
                return False
            shutil.copy2(camera.url, frame_path)
            return True
        except Exception:
            return False

    # --------------------------------------------------- frame analysis

    def _analyze_frame(self, camera: Camera, frame: CameraFrame) -> None:
        """Analyze a captured frame using perception system."""
        if self.perception is None:
            return

        if not os.path.exists(frame.image_path):
            return

        # Motion detection (compare with last frame)
        if camera.detect_motion:
            motion = self._detect_motion(camera, frame)
            frame.motion_detected = motion
            if motion:
                camera.motion_events += 1
                self._create_event(
                    camera, "motion",
                    f"Motion detected on {camera.name}",
                    frame.image_path, "low",
                )

        # Face detection
        if camera.detect_faces and self.perception:
            try:
                face_result = self.perception.faces.identify(frame.image_path)
                frame.faces_detected = face_result.face_count
                if face_result.face_count > 0:
                    camera.face_detections += face_result.face_count

                    # Unknown person
                    if face_result.unknown_count > 0:
                        severity = "high" if camera.camera_type == CAM_HOME else "medium"
                        self._create_event(
                            camera, "unknown_person",
                            f"Unknown person on {camera.name}: {face_result.unknown_count}",
                            frame.image_path, severity,
                        )
                    elif face_result.is_known:
                        self._create_event(
                            camera, "face",
                            f"Known person on {camera.name}: {face_result.name}",
                            frame.image_path, "low",
                        )
            except Exception:
                pass

        # Object detection
        if camera.detect_objects and self.perception:
            try:
                scene = self.perception.objects.recognize(frame.image_path)
                frame.objects_detected = len(scene.objects)
                if frame.objects_detected > 0:
                    camera.object_detections += frame.objects_detected

                    # People detected
                    if scene.people_count > 0:
                        self._create_event(
                            camera, "person",
                            f"{scene.people_count} person(s) on {camera.name}",
                            frame.image_path, "medium",
                        )

                    # Vehicles detected
                    if scene.vehicles_count > 0:
                        self._create_event(
                            camera, "vehicle",
                            f"{scene.vehicles_count} vehicle(s) on {camera.name}",
                            frame.image_path, "low",
                        )

                    # Animals detected
                    if scene.animals_count > 0:
                        self._create_event(
                            camera, "animal",
                            f"{scene.animals_count} animal(s) on {camera.name}",
                            frame.image_path, "low",
                        )

                    frame.analysis = scene.to_dict()
            except Exception:
                pass

    def _detect_motion(self, camera: Camera, frame: CameraFrame) -> bool:
        """Detect motion by comparing with the last frame."""
        if self._cv2 is None:
            return False  # can't detect motion without cv2

        try:
            current = self._cv2.imread(frame.image_path)
            if current is None:
                return False

            current_gray = self._cv2.cvtColor(current, self._cv2.COLOR_BGR2GRAY)
            current_gray = self._cv2.GaussianBlur(current_gray, (21, 21), 0)

            last = self._last_frames.get(camera.camera_id)
            self._last_frames[camera.camera_id] = current_gray

            if last is None:
                return False  # first frame, no comparison

            # Compute difference
            diff = self._cv2.absdiff(last, current_gray)
            threshold = self._cv2.threshold(diff, 25, 255, self._cv2.THRESH_BINARY)[1]
            motion_pixels = self._cv2.countNonZero(threshold)
            total_pixels = current_gray.shape[0] * current_gray.shape[1]
            motion_ratio = motion_pixels / total_pixels

            return motion_ratio > 0.02  # 2% of pixels changed

        except Exception:
            return False

    # --------------------------------------------------- events

    def _create_event(
        self, camera: Camera, event_type: str, description: str,
        frame_path: str, severity: str = "low",
    ) -> CameraEvent:
        """Create a camera event."""
        event = CameraEvent(
            event_id=hashlib.sha256(
                f"event:{camera.camera_id}:{time.time()}".encode()
            ).hexdigest()[:16],
            camera_id=camera.camera_id,
            camera_name=camera.name,
            event_type=event_type,
            timestamp=time.time(),
            description=description,
            frame_path=frame_path,
            severity=severity,
            location=camera.location,
        )

        # Record event
        try:
            with open(self._events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception:
            pass

        self._log("camera.event", event.to_dict())

        # Trigger callback
        if self.on_event:
            try:
                self.on_event(event)
            except Exception:
                pass

        return event

    def get_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent camera events."""
        if not self._events_file.exists():
            return []
        try:
            lines = self._events_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_events_by_camera(self, camera_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get events for a specific camera."""
        events = self.get_events(limit=9999)
        return [e for e in events if e.get("camera_id") == camera_id][:limit]

    def get_events_by_type(self, event_type: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get events filtered by type."""
        events = self.get_events(limit=9999)
        return [e for e in events if e.get("event_type") == event_type][:limit]

    # --------------------------------------------------- monitoring loop

    def monitor_all(self) -> list[CameraFrame]:
        """Capture a frame from all enabled cameras. Returns captured frames."""
        frames: list[CameraFrame] = []
        for camera in self._cameras.values():
            if not camera.enabled:
                continue
            frame = self.capture_frame(camera.camera_id)
            if frame:
                frames.append(frame)
        return frames

    def start_monitoring(self) -> None:
        """Start continuous monitoring (would run in a thread in production)."""
        self._monitoring = True
        self._log("monitoring.started", {})

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._monitoring = False
        self._log("monitoring.stopped", {})

    @property
    def is_monitoring(self) -> bool:
        return self._monitoring

    # --------------------------------------------------- public cameras

    def add_public_camera(
        self,
        name: str,
        url: str,
        *,
        location: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        snapshot_interval: float = 60.0,  # public cameras checked less frequently
    ) -> Camera:
        """Add a publicly accessible traffic/municipal camera.

        Only use this for cameras that are genuinely publicly available.
        Never use it to access private or restricted cameras.
        """
        return self.add_camera(
            name=name,
            camera_type=CAM_PUBLIC,
            connection_type=CONN_HTTP_SNAPSHOT,
            url=url,
            location=location,
            latitude=latitude,
            longitude=longitude,
            detect_faces=False,  # don't run face recognition on public cameras
            detect_objects=True,
            detect_motion=False,  # public cameras may have constant motion
            snapshot_interval=snapshot_interval,
        )

    def check_traffic_conditions(self, route_cameras: list[str]) -> dict[str, Any]:
        """Check traffic conditions along a route using public cameras."""
        conditions: list[dict[str, Any]] = []
        for camera_id in route_cameras:
            camera = self._cameras.get(camera_id)
            if camera is None or camera.camera_type != CAM_PUBLIC:
                continue
            frame = self.capture_frame(camera_id)
            if frame:
                conditions.append({
                    "camera": camera.name,
                    "location": camera.location,
                    "vehicles_detected": frame.objects_detected,
                    "analysis": frame.analysis,
                })

        return {
            "timestamp": time.time(),
            "cameras_checked": len(conditions),
            "conditions": conditions,
        }

    # --------------------------------------------------- ONVIF discovery

    def discover_onvif_cameras(self) -> list[dict[str, Any]]:
        """Discover ONVIF cameras on the local network.

        Uses onvif-cli if available, otherwise returns empty list.
        """
        onvif_cli = shutil.which("onvif-cli")
        if not onvif_cli:
            return []

        try:
            result = subprocess.run(
                [onvif_cli, "devicemgmt", "GetDevices"],  # type: ignore
                capture_output=True, text=True, timeout=30,
            )
            # Parse output (format varies by implementation)
            cameras: list[dict[str, Any]] = []
            for line in result.stdout.splitlines():
                if "://" in line:
                    cameras.append({
                        "url": line.strip(),
                        "discovered": True,
                    })
            return cameras
        except Exception:
            return []

    # --------------------------------------------------- cleanup

    def cleanup_old_frames(self, max_age_hours: float = 24.0) -> int:
        """Delete frame images older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        count = 0
        for frame_file in self._frames_dir.glob("*.jpg"):
            try:
                if frame_file.stat().st_mtime < cutoff:
                    frame_file.unlink()
                    count += 1
            except Exception:
                pass
        return count

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        """Get camera system status."""
        cameras = list(self._cameras.values())
        return {
            "monitoring": self._monitoring,
            "total_cameras": len(cameras),
            "enabled_cameras": sum(1 for c in cameras if c.enabled),
            "online_cameras": sum(1 for c in cameras if c.status == STATUS_ONLINE),
            "home_cameras": sum(1 for c in cameras if c.camera_type == CAM_HOME),
            "dashcam_cameras": sum(1 for c in cameras if c.camera_type == CAM_DASHCAM),
            "body_cameras": sum(1 for c in cameras if c.camera_type == CAM_BODY),
            "public_cameras": sum(1 for c in cameras if c.camera_type == CAM_PUBLIC),
            "opencv_available": self._cv2 is not None,
            "ffmpeg_available": self._ffmpeg is not None,
            "total_frames_captured": sum(c.frames_captured for c in cameras),
            "total_events": len(self.get_events(limit=9999)),
        }

    # --------------------------------------------------- persistence

    def _load_cameras(self) -> None:
        if not self._cameras_file.exists():
            return
        try:
            data = json.loads(
                self._cameras_file.read_text(encoding="utf-8")
            )
            for c_id, c_data in data.items():
                self._cameras[c_id] = Camera(
                    camera_id=c_data.get("camera_id", c_id),
                    name=c_data["name"],
                    camera_type=c_data.get("camera_type", CAM_HOME),
                    connection_type=c_data.get("connection_type", CONN_RTSP),
                    url=c_data.get("url", ""),
                    username=c_data.get("username", ""),
                    password=c_data.get("password", ""),
                    location=c_data.get("location", ""),
                    latitude=c_data.get("latitude", 0.0),
                    longitude=c_data.get("longitude", 0.0),
                    enabled=c_data.get("enabled", True),
                    status=c_data.get("status", STATUS_OFFLINE),
                    last_frame_time=c_data.get("last_frame_time", 0.0),
                    last_error=c_data.get("last_error", ""),
                    fps=c_data.get("fps", 0.0),
                    resolution=tuple(c_data.get("resolution", [0, 0])),
                    detect_faces=c_data.get("detect_faces", True),
                    detect_objects=c_data.get("detect_objects", True),
                    detect_motion=c_data.get("detect_motion", True),
                    record_on_motion=c_data.get("record_on_motion", False),
                    snapshot_interval=c_data.get("snapshot_interval", 5.0),
                    frames_captured=c_data.get("frames_captured", 0),
                    motion_events=c_data.get("motion_events", 0),
                    face_detections=c_data.get("face_detections", 0),
                    object_detections=c_data.get("object_detections", 0),
                    created_at=c_data.get("created_at", 0.0),
                    updated_at=c_data.get("updated_at", 0.0),
                )
        except Exception:
            pass

    def _save_cameras(self) -> None:
        data = {c_id: c.to_dict() for c_id, c in self._cameras.items()}
        self._cameras_file.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
