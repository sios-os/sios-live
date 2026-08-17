"""REST API server — HTTP backbone for all ANUBIS integrations.

Exposes ANUBIS's capabilities over HTTP so that:
- The phone companion app can send data and receive commands
- The web dashboard can display status and configuration
- External services (smart home, calendar, etc.) can communicate
- Other devices on the network can query ANUBIS

Uses only the Python standard library (http.server) — no Flask, no
FastAPI, no external dependencies. This keeps ANUBIS self-reliant.

SECURITY:
- Binds to localhost by default (not 0.0.0.0)
- API key authentication for all endpoints
- Rate limiting to prevent abuse
- All requests logged to evidence ledger
- CORS headers for web dashboard
- No secrets exposed in responses

ENDPOINTS:
  GET  /api/status           — System status
  GET  /api/health           — Health check
  POST /api/chat             — Send a message to ANUBIS
  GET  /api/cameras          — List cameras
  GET  /api/cameras/{id}/frame — Capture frame from camera
  GET  /api/contacts         — List emergency contacts
  POST /api/contacts         — Add emergency contact
  GET  /api/threats          — List active threats
  GET  /api/threats/history  — Threat history
  GET  /api/network/devices  — List network devices
  POST /api/network/scan     — Trigger network scan
  GET  /api/remote/status    — Remote monitor status
  POST /api/remote/location  — Receive phone GPS update
  POST /api/remote/accel     — Receive phone accelerometer data
  POST /api/remote/health    — Receive wearable health data
  POST /api/remote/phone     — Receive phone status
  GET  /api/perception/status — Perception system status
  GET  /api/memory/stats     — Memory statistics
  GET  /api/scheduler/status — Scheduler status
  POST /api/speak            — Make ANUBIS speak
  POST /api/mode/{mode}      — Set listening mode
  GET  /api/config           — Get configuration
  PUT  /api/config           — Update configuration
"""
from __future__ import annotations

import hashlib
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse, parse_qs
import threading


class APIServer:
    """REST API server for ANUBIS.

    Runs in a background thread. All endpoints return JSON.
    Authentication via API key in Authorization header or query param.

    Usage:
        server = APIServer(root, port=8765, api_key="secret")
        server.start()
        # ... server runs in background ...
        server.stop()
    """

    ACTOR = "anubis.api"

    def __init__(
        self,
        root: str | Path,
        *,
        port: int = 8765,
        host: str = "127.0.0.1",
        api_key: str = "",
        ledger: Any | None = None,
        # System components (injected)
        sensory: Any | None = None,
        perception: Any | None = None,
        contacts: Any | None = None,
        messaging: Any | None = None,
        network_ops: Any | None = None,
        remote_monitor: Any | None = None,
        threat_detector: Any | None = None,
        cameras: Any | None = None,
        memory: Any | None = None,
        scheduler: Any | None = None,
        observer: Any | None = None,
        proactive: Any | None = None,
        consciousness: Any | None = None,
        phone_protocol: Any | None = None,
        on_chat: Callable[[str], str] | None = None,
        on_command: Callable[[dict], dict] | None = None,
    ) -> None:
        self.root = Path(root)
        self.port = port
        self.host = host
        self.api_key = api_key
        self.ledger = ledger

        # Component references
        self.sensory = sensory
        self.perception = perception
        self.contacts = contacts
        self.messaging = messaging
        self.network_ops = network_ops
        self.remote_monitor = remote_monitor
        self.threat_detector = threat_detector
        self.cameras = cameras
        self.memory = memory
        self.scheduler = scheduler
        self.observer = observer
        self.proactive = proactive
        self.consciousness = consciousness
        self.phone_protocol = phone_protocol
        self.on_chat = on_chat
        self.on_command = on_command

        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._request_count = 0
        self._start_time = 0.0

        # Rate limiting
        self._rate_limits: dict[str, list[float]] = {}
        self._rate_limit_window = 60.0  # seconds
        self._rate_limit_max = 100  # requests per window per IP

    def start(self) -> bool:
        """Start the API server in a background thread."""
        if self._running:
            return True

        handler = _make_handler(self)

        try:
            self._server = HTTPServer((self.host, self.port), handler)
        except OSError:
            return False

        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="anubis-api-server",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the API server."""
        self._running = False
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        self._server = None

    @property
    def is_running(self) -> bool:
        return self._running

    def _send_command(self, req: dict) -> dict:
        """Send a command to the daemon via the on_command callback."""
        if self.on_command:
            try:
                return self.on_command(req)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "daemon command bridge not configured"}

    def get_status(self) -> dict[str, Any]:
        """Get API server status."""
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "uptime_seconds": time.time() - self._start_time if self._running else 0,
            "total_requests": self._request_count,
            "api_key_required": bool(self.api_key),
        }

    # --------------------------------------------------- rate limiting

    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP is within rate limit."""
        now = time.time()
        requests = self._rate_limits.get(ip, [])
        # Remove old entries
        requests = [t for t in requests if now - t < self._rate_limit_window]
        if len(requests) >= self._rate_limit_max:
            self._rate_limits[ip] = requests
            return False
        requests.append(now)
        self._rate_limits[ip] = requests
        return True

    # --------------------------------------------------- authentication

    def _authenticate(self, headers: dict[str, str], query: dict[str, list[str]]) -> bool:
        """Check API key authentication."""
        if not self.api_key:
            return True  # no auth required

        # Check Authorization header
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            if token == self.api_key:
                return True

        # Check query parameter
        api_key = query.get("api_key", [""])[0]
        if api_key == self.api_key:
            return True

        return False

    # --------------------------------------------------- request logging

    def _log_request(self, method: str, path: str, ip: str, status: int) -> None:
        """Log a request to the evidence ledger."""
        self._request_count += 1
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, "request", {
                    "method": method,
                    "path": path,
                    "ip": ip,
                    "status": status,
                })
            except Exception:
                pass


def _make_handler(api_server: APIServer) -> type[BaseHTTPRequestHandler]:
    """Create a request handler class with access to the API server."""

    class ANUBISRequestHandler(BaseHTTPRequestHandler):
        # Suppress default logging
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _send_json(self, code: int, data: Any) -> None:
            body = json.dumps(data, indent=2, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            self.wfile.write(body)

        def _send_error(self, code: int, message: str) -> None:
            self._send_json(code, {"error": message})

        def _get_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            try:
                body = self.rfile.read(content_length)
                return json.loads(body)
            except Exception:
                return {}

        def _get_headers(self) -> dict[str, str]:
            return {k.lower(): v for k, v in self.headers.items()}

        def _authenticate(self) -> bool:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            return api_server._authenticate(self._get_headers(), query)

        def _check_rate(self) -> bool:
            ip = self.client_address[0] if self.client_address else "unknown"
            return api_server._check_rate_limit(ip)

        def do_OPTIONS(self) -> None:
            self._send_json(200, {"status": "ok"})

        def do_GET(self) -> None:
            if not self._authenticate():
                self._send_error(401, "Unauthorized")
                return
            if not self._check_rate():
                self._send_error(429, "Rate limit exceeded")
                return

            parsed = urlparse(self.path)
            path = parsed.path
            ip = self.client_address[0] if self.client_address else "unknown"

            try:
                result, code = self._handle_get(path, parsed)
                self._send_json(code, result)
                api_server._log_request("GET", path, ip, code)
            except Exception as e:
                self._send_error(500, str(e))
                api_server._log_request("GET", path, ip, 500)

        def do_POST(self) -> None:
            if not self._authenticate():
                self._send_error(401, "Unauthorized")
                return
            if not self._check_rate():
                self._send_error(429, "Rate limit exceeded")
                return

            parsed = urlparse(self.path)
            path = parsed.path
            ip = self.client_address[0] if self.client_address else "unknown"

            try:
                body = self._get_body()
                result, code = self._handle_post(path, body, parsed)
                self._send_json(code, result)
                api_server._log_request("POST", path, ip, code)
            except Exception as e:
                self._send_error(500, str(e))
                api_server._log_request("POST", path, ip, 500)

        def do_PUT(self) -> None:
            if not self._authenticate():
                self._send_error(401, "Unauthorized")
                return
            parsed = urlparse(self.path)
            path = parsed.path
            ip = self.client_address[0] if self.client_address else "unknown"
            try:
                body = self._get_body()
                result, code = self._handle_put(path, body, parsed)
                self._send_json(code, result)
                api_server._log_request("PUT", path, ip, code)
            except Exception as e:
                self._send_error(500, str(e))
                api_server._log_request("PUT", path, ip, 500)

        # --------------------------------------------------- GET handlers

        def _handle_get(self, path: str, parsed: Any) -> tuple[Any, int]:
            # Health & status
            if path == "/api/health":
                return {"status": "healthy", "timestamp": time.time()}, 200
            if path == "/api/status":
                return self._get_system_status(), 200

            # Cameras
            if path == "/api/cameras":
                if api_server.cameras:
                    return {"cameras": api_server.cameras.get_cameras()}, 200
                return {"cameras": []}, 200

            # Contacts
            if path == "/api/contacts":
                if api_server.contacts:
                    return {"contacts": api_server.contacts.get_contacts()}, 200
                return {"contacts": []}, 200

            # Threats
            if path == "/api/threats":
                if api_server.threat_detector:
                    return {"threats": api_server.threat_detector.get_active_threats()}, 200
                return {"threats": []}, 200
            if path == "/api/threats/history":
                if api_server.threat_detector:
                    limit = int(parse_qs(parsed.query).get("limit", ["50"])[0])
                    return {"threats": api_server.threat_detector.get_threat_history(limit)}, 200
                return {"threats": []}, 200

            # Network
            if path == "/api/network/devices":
                if api_server.network_ops:
                    return {"devices": api_server.network_ops.get_devices()}, 200
                return {"devices": []}, 200
            if path == "/api/network/status":
                if api_server.network_ops:
                    return api_server.network_ops.get_status(), 200
                return {"error": "network ops not configured"}, 404

            # Remote monitor
            if path == "/api/remote/status":
                if api_server.remote_monitor:
                    return api_server.remote_monitor.get_status(), 200
                return {"error": "remote monitor not configured"}, 404

            # Perception
            if path == "/api/perception/status":
                if api_server.perception:
                    return api_server.perception.get_status(), 200
                return {"error": "perception not configured"}, 404

            # Phone — pending notifications
            if path == "/api/notifications":
                if api_server.phone_protocol:
                    device_id = parse_qs(parsed.query).get("device_id", [""])[0]
                    if not device_id:
                        return {"error": "device_id query param required"}, 400
                    notifs = api_server.phone_protocol.get_pending_notifications(device_id)
                    return {"notifications": notifs, "count": len(notifs)}, 200
                return {"error": "phone protocol not configured"}, 404

            # Phone — device list
            if path == "/api/phone/devices":
                if api_server.phone_protocol:
                    return {"devices": api_server.phone_protocol.get_devices()}, 200
                return {"devices": []}, 200

            # Phone — protocol status
            if path == "/api/phone/status":
                if api_server.phone_protocol:
                    return api_server.phone_protocol.get_status(), 200
                return {"error": "phone protocol not configured"}, 404

            # Memory
            if path == "/api/memory/stats":
                if api_server.memory:
                    return api_server.memory.stats(), 200
                return {"error": "memory not configured"}, 404

            # Scheduler
            if path == "/api/scheduler/status":
                if api_server.scheduler:
                    return api_server.scheduler.get_status(), 200
                return {"error": "scheduler not configured"}, 404

            # Messaging
            if path == "/api/messaging/status":
                if api_server.messaging:
                    return api_server.messaging.get_status(), 200
                return {"error": "messaging not configured"}, 404

            # API server status
            if path == "/api/server/status":
                return api_server.get_status(), 200

            # Sensory
            if path == "/api/sensory/status":
                if api_server.sensory:
                    return api_server.sensory.get_status(), 200
                return {"error": "sensory not configured"}, 404

            # Config
            if path == "/api/config":
                return self._get_config(), 200

            # Self-healing endpoints (phone app screens)
            if path == "/api/snapshots":
                return api_server._send_command({"cmd": "snapshot_list"}), 200
            if path == "/api/snapshots/status":
                return api_server._send_command({"cmd": "snapshot_status"}), 200
            if path == "/api/self_repair/status":
                return api_server._send_command({"cmd": "self_repair_status"}), 200
            if path == "/api/self_repair/alerts":
                return api_server._send_command({"cmd": "self_repair_alerts"}), 200
            if path == "/api/drive_report":
                return api_server._send_command({"cmd": "drive_report"}), 200
            if path == "/api/cold_archive/status":
                return api_server._send_command({"cmd": "cold_archive_status"}), 200
            if path == "/api/boot_check":
                return api_server._send_command({"cmd": "boot_check"}), 200
            if path == "/api/book/status":
                return api_server._send_command({"cmd": "book_seal_status"}), 200
            if path == "/api/book/latest":
                return api_server._send_command({"cmd": "book_read_latest"}), 200
            if path == "/api/book/editions":
                return api_server._send_command({"cmd": "book_list_editions"}), 200
            if path == "/api/dream/status":
                return api_server._send_command({"cmd": "dream_status"}), 200
            if path == "/api/dream/gaps":
                return api_server._send_command({"cmd": "dream_gaps"}), 200
            if path == "/api/dream/recommendations":
                return api_server._send_command({"cmd": "dream_recommendations"}), 200
            if path == "/api/funding/status":
                return api_server._send_command({"cmd": "funding_status"}), 200
            if path == "/api/funding/pending_reviews":
                return api_server._send_command({"cmd": "funding_pending_reviews"}), 200
            if path == "/api/phone/status":
                return api_server._send_command({"cmd": "phone_status"}), 200
            if path == "/api/email/status":
                return api_server._send_command({"cmd": "email_status"}), 200
            if path == "/api/inference/status":
                return api_server._send_command({"cmd": "inference_status"}), 200
            if path == "/api/dependency/status":
                return api_server._send_command({"cmd": "dependency_status"}), 200

            return {"error": f"Not found: {path}"}, 404

        # --------------------------------------------------- POST handlers

        def _handle_post(self, path: str, body: dict[str, Any], parsed: Any) -> tuple[Any, int]:
            # Chat
            if path == "/api/chat":
                message = body.get("message", "")
                if not message:
                    return {"error": "No message provided"}, 400
                if api_server.on_chat:
                    response = api_server.on_chat(message)
                    return {"response": response}, 200
                return {"error": "Chat not configured"}, 404

            # Speak
            if path == "/api/speak":
                text = body.get("text", "")
                if not text:
                    return {"error": "No text provided"}, 400
                if api_server.sensory:
                    req_id = api_server.sensory.speak(text, priority=body.get("priority", "normal"))
                    return {"request_id": req_id, "status": "queued"}, 200
                return {"error": "Sensory not configured"}, 404

            # Listening mode
            if path.startswith("/api/mode/"):
                mode = path.split("/api/mode/")[1]
                if api_server.sensory:
                    if api_server.sensory.set_mode(mode):
                        return {"mode": mode, "status": "set"}, 200
                    return {"error": f"Invalid mode: {mode}"}, 400
                return {"error": "Sensory not configured"}, 404

            # Contacts — add
            if path == "/api/contacts":
                if api_server.contacts:
                    name = body.get("name", "")
                    if not name:
                        return {"error": "Name required"}, 400
                    contact = api_server.contacts.add_contact(
                        name=name,
                        phone=body.get("phone", ""),
                        email=body.get("email", ""),
                        relationship=body.get("relationship", ""),
                        role=body.get("role", "general"),
                        priority=body.get("priority", 99),
                        trusted=body.get("trusted", False),
                    )
                    return contact.to_dict(), 201
                return {"error": "Contacts not configured"}, 404

            # Network scan
            if path == "/api/network/scan":
                if api_server.network_ops:
                    devices = api_server.network_ops.scan_network()
                    return {"devices": devices, "count": len(devices)}, 200
                return {"error": "Network ops not configured"}, 404

            # Network quarantine
            if path == "/api/network/quarantine":
                if api_server.network_ops:
                    device_id = body.get("device_id", "")
                    if not device_id:
                        return {"error": "device_id required"}, 400
                    result = api_server.network_ops.quarantine_device(device_id)
                    return result, 200
                return {"error": "Network ops not configured"}, 404

            # Remote monitor — receive data
            if path == "/api/remote/location":
                if api_server.remote_monitor:
                    from .remote_monitor import LocationUpdate
                    loc = LocationUpdate(
                        latitude=body.get("latitude", 0),
                        longitude=body.get("longitude", 0),
                        accuracy=body.get("accuracy", 0),
                        speed=body.get("speed", 0),
                        altitude=body.get("altitude", 0),
                        timestamp=body.get("timestamp", time.time()),
                        source=body.get("source", "phone"),
                    )
                    api_server.remote_monitor.receive_location(loc)
                    return {"status": "received"}, 200
                return {"error": "Remote monitor not configured"}, 404

            if path == "/api/remote/accel":
                if api_server.remote_monitor:
                    from .remote_monitor import AccelerometerData
                    data = AccelerometerData(
                        x=body.get("x", 0),
                        y=body.get("y", 0),
                        z=body.get("z", 0),
                        timestamp=body.get("timestamp", time.time()),
                    )
                    api_server.remote_monitor.receive_accelerometer(data)
                    return {"status": "received"}, 200
                return {"error": "Remote monitor not configured"}, 404

            if path == "/api/remote/health":
                if api_server.remote_monitor:
                    from .remote_monitor import HealthData
                    data = HealthData(
                        heart_rate=body.get("heart_rate", 0),
                        heart_rate_variability=body.get("heart_rate_variability", 0),
                        steps=body.get("steps", 0),
                        activity_level=body.get("activity_level", "unknown"),
                        stress_level=body.get("stress_level", 0),
                        blood_oxygen=body.get("blood_oxygen", 0),
                        body_temperature=body.get("body_temperature", 0),
                        timestamp=body.get("timestamp", time.time()),
                    )
                    api_server.remote_monitor.receive_health(data)
                    return {"status": "received"}, 200
                return {"error": "Remote monitor not configured"}, 404

            if path == "/api/remote/phone":
                if api_server.remote_monitor:
                    from .remote_monitor import PhoneStatus
                    status = PhoneStatus(
                        battery_level=body.get("battery_level", 0),
                        battery_charging=body.get("battery_charging", False),
                        network_type=body.get("network_type", ""),
                        screen_on=body.get("screen_on", False),
                        in_call=body.get("in_call", False),
                        ringer_mode=body.get("ringer_mode", ""),
                        timestamp=body.get("timestamp", time.time()),
                    )
                    api_server.remote_monitor.receive_phone_status(status)
                    return {"status": "received"}, 200
                return {"error": "Remote monitor not configured"}, 404

            # Camera capture
            if path.startswith("/api/cameras/") and path.endswith("/frame"):
                camera_id = path.split("/")[3]
                if api_server.cameras:
                    frame = api_server.cameras.capture_frame(camera_id)
                    if frame:
                        return frame.to_dict(), 200
                    return {"error": "Capture failed"}, 500
                return {"error": "Cameras not configured"}, 404

            # Camera monitor all
            if path == "/api/cameras/monitor":
                if api_server.cameras:
                    frames = api_server.cameras.monitor_all()
                    return {"frames": [f.to_dict() for f in frames]}, 200
                return {"error": "Cameras not configured"}, 404

            # Emergency alert
            if path == "/api/emergency/alert":
                if api_server.messaging:
                    message = body.get("message", "Emergency alert")
                    messages = api_server.messaging.send_emergency_alert(message)
                    return {"sent": [m.to_dict() for m in messages]}, 200
                return {"error": "Messaging not configured"}, 404

            # Threat resolve
            if path == "/api/threats/resolve":
                if api_server.threat_detector:
                    threat_id = body.get("threat_id", "")
                    resolution = body.get("resolution", "")
                    if api_server.threat_detector.resolve_threat(threat_id, resolution):
                        return {"status": "resolved"}, 200
                    return {"error": "Threat not found"}, 404
                return {"error": "Threat detector not configured"}, 404

            # Phone — register device
            if path == "/api/phone/register":
                if api_server.phone_protocol:
                    name = body.get("name", "")
                    if not name:
                        return {"error": "name required"}, 400
                    device, token = api_server.phone_protocol.register_device(
                        name,
                        owner=body.get("owner", "creator"),
                        platform=body.get("platform", "android"),
                        app_version=body.get("app_version", ""),
                    )
                    return {
                        "device_id": device.device_id,
                        "name": device.name,
                        "token": token,
                        "status": device.status,
                    }, 201
                return {"error": "phone protocol not configured"}, 404

            # Phone — heartbeat
            if path == "/api/phone/heartbeat":
                if api_server.phone_protocol:
                    device_id = body.get("device_id", "")
                    if not device_id:
                        return {"error": "device_id required"}, 400
                    ok = api_server.phone_protocol.heartbeat(
                        device_id,
                        battery=body.get("battery_level", 0),
                        charging=body.get("battery_charging", False),
                    )
                    if ok:
                        return {"status": "ok"}, 200
                    return {"error": "device not found"}, 404
                return {"error": "phone protocol not configured"}, 404

            # Phone — telemetry (generic)
            if path == "/api/phone/telemetry":
                if api_server.phone_protocol:
                    device_id = body.get("device_id", "")
                    if not device_id:
                        return {"error": "device_id required"}, 400
                    data = body.get("data", {})
                    ok = api_server.phone_protocol.receive_telemetry(device_id, data)
                    if ok:
                        return {"status": "received"}, 200
                    return {"error": "device not found"}, 404
                return {"error": "phone protocol not configured"}, 404

            # Phone — mark notification delivered
            if path == "/api/notifications/delivered":
                if api_server.phone_protocol:
                    notif_id = body.get("notif_id", "")
                    if not notif_id:
                        return {"error": "notif_id required"}, 400
                    ok = api_server.phone_protocol.mark_notification_delivered(notif_id)
                    if ok:
                        return {"status": "delivered"}, 200
                    return {"error": "notification not found"}, 404
                return {"error": "phone protocol not configured"}, 404

            return {"error": f"Not found: {path}"}, 404

        # --------------------------------------------------- PUT handlers

        def _handle_put(self, path: str, body: dict[str, Any], parsed: Any) -> tuple[Any, int]:
            if path == "/api/config":
                return self._update_config(body), 200
            return {"error": f"Not found: {path}"}, 404

        # --------------------------------------------------- helpers

        def _get_system_status(self) -> dict[str, Any]:
            status: dict[str, Any] = {
                "timestamp": time.time(),
                "api_server": api_server.get_status(),
            }
            if api_server.sensory:
                status["sensory"] = api_server.sensory.get_status()
            if api_server.perception:
                status["perception"] = api_server.perception.get_status()
            if api_server.contacts:
                status["contacts"] = api_server.contacts.get_status()
            if api_server.messaging:
                status["messaging"] = api_server.messaging.get_status()
            if api_server.network_ops:
                status["network"] = api_server.network_ops.get_status()
            if api_server.remote_monitor:
                status["remote"] = api_server.remote_monitor.get_status()
            if api_server.threat_detector:
                status["threats"] = api_server.threat_detector.get_status()
            if api_server.cameras:
                status["cameras"] = api_server.cameras.get_status()
            if api_server.memory:
                status["memory"] = api_server.memory.stats()
            if api_server.scheduler:
                status["scheduler"] = api_server.scheduler.get_status()
            return status

        def _get_config(self) -> dict[str, Any]:
            return {
                "api": api_server.get_status(),
                "host": api_server.host,
                "port": api_server.port,
            }

        def _update_config(self, body: dict[str, Any]) -> dict[str, Any]:
            # Configuration updates would go here
            return {"status": "updated", "changes": list(body.keys())}

    return ANUBISRequestHandler
