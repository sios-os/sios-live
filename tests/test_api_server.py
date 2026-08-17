"""Tests for the REST API server."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.api_server import APIServer


class TestAPIServer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.server = APIServer(self.root, port=18765, api_key="test-key")
        self.server.start()
        time.sleep(0.1)  # let server start

    def tearDown(self):
        self.server.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _request(self, method: str, path: str, body: dict | None = None,
                 headers: dict | None = None, no_auth: bool = False) -> tuple[int, dict]:
        """Make an HTTP request to the test server."""
        import urllib.request
        url = f"http://127.0.0.1:18765{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        if self.server.api_key and not no_auth and not headers:
            req.add_header("Authorization", f"Bearer {self.server.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_server_starts(self):
        self.assertTrue(self.server.is_running)

    def test_health(self):
        code, data = self._request("GET", "/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "healthy")

    def test_status(self):
        code, data = self._request("GET", "/api/status")
        self.assertEqual(code, 200)
        self.assertIn("timestamp", data)
        self.assertIn("api_server", data)

    def test_server_status(self):
        code, data = self._request("GET", "/api/server/status")
        self.assertEqual(code, 200)
        self.assertTrue(data["running"])
        self.assertEqual(data["port"], 18765)

    def test_unauthorized(self):
        # Request without API key
        code, data = self._request("GET", "/api/health", no_auth=True)
        self.assertEqual(code, 401)

    def test_wrong_api_key(self):
        code, data = self._request("GET", "/api/health",
                                   headers={"Authorization": "Bearer wrong"})
        self.assertEqual(code, 401)

    def test_no_api_key_required(self):
        server = APIServer(self.root, port=18766, api_key="")
        server.start()
        time.sleep(0.1)
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18766/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
        server.stop()

    def test_chat_no_handler(self):
        code, data = self._request("POST", "/api/chat", {"message": "hello"})
        self.assertEqual(code, 404)

    def test_chat_with_handler(self):
        self.server.on_chat = lambda msg: f"Response to: {msg}"
        code, data = self._request("POST", "/api/chat", {"message": "hello"})
        self.assertEqual(code, 200)
        self.assertEqual(data["response"], "Response to: hello")

    def test_chat_no_message(self):
        self.server.on_chat = lambda msg: "response"
        code, data = self._request("POST", "/api/chat", {})
        self.assertEqual(code, 400)

    def test_speak_no_sensory(self):
        code, data = self._request("POST", "/api/speak", {"text": "hello"})
        self.assertEqual(code, 404)

    def test_speak_with_sensory(self):
        sensory = MagicMock()
        sensory.speak = MagicMock(return_value="req-123")
        self.server.sensory = sensory
        code, data = self._request("POST", "/api/speak", {"text": "hello"})
        self.assertEqual(code, 200)
        self.assertEqual(data["request_id"], "req-123")

    def test_mode_set(self):
        sensory = MagicMock()
        sensory.set_mode = MagicMock(return_value=True)
        self.server.sensory = sensory
        code, data = self._request("POST", "/api/mode/privacy", {})
        self.assertEqual(code, 200)
        self.assertEqual(data["mode"], "privacy")

    def test_mode_invalid(self):
        sensory = MagicMock()
        sensory.set_mode = MagicMock(return_value=False)
        self.server.sensory = sensory
        code, data = self._request("POST", "/api/mode/invalid", {})
        self.assertEqual(code, 400)

    def test_cameras_empty(self):
        code, data = self._request("GET", "/api/cameras")
        self.assertEqual(code, 200)
        self.assertEqual(data["cameras"], [])

    def test_contacts_empty(self):
        code, data = self._request("GET", "/api/contacts")
        self.assertEqual(code, 200)
        self.assertEqual(data["contacts"], [])

    def test_threats_empty(self):
        code, data = self._request("GET", "/api/threats")
        self.assertEqual(code, 200)
        self.assertEqual(data["threats"], [])

    def test_threats_history_empty(self):
        code, data = self._request("GET", "/api/threats/history")
        self.assertEqual(code, 200)
        self.assertEqual(data["threats"], [])

    def test_network_devices_empty(self):
        code, data = self._request("GET", "/api/network/devices")
        self.assertEqual(code, 200)
        self.assertEqual(data["devices"], [])

    def test_remote_location(self):
        monitor = MagicMock()
        self.server.remote_monitor = monitor
        code, data = self._request("POST", "/api/remote/location", {
            "latitude": 40.7,
            "longitude": -74.0,
        })
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "received")
        monitor.receive_location.assert_called_once()

    def test_remote_accel(self):
        monitor = MagicMock()
        self.server.remote_monitor = monitor
        code, data = self._request("POST", "/api/remote/accel", {
            "x": 0, "y": 0, "z": 9.8,
        })
        self.assertEqual(code, 200)
        monitor.receive_accelerometer.assert_called_once()

    def test_remote_health(self):
        monitor = MagicMock()
        self.server.remote_monitor = monitor
        code, data = self._request("POST", "/api/remote/health", {
            "heart_rate": 72,
        })
        self.assertEqual(code, 200)
        monitor.receive_health.assert_called_once()

    def test_remote_phone(self):
        monitor = MagicMock()
        self.server.remote_monitor = monitor
        code, data = self._request("POST", "/api/remote/phone", {
            "battery_level": 80,
        })
        self.assertEqual(code, 200)
        monitor.receive_phone_status.assert_called_once()

    def test_404(self):
        code, data = self._request("GET", "/api/nonexistent")
        self.assertEqual(code, 404)

    def test_rate_limiting(self):
        # Make many requests quickly
        server = APIServer(self.root, port=18767, api_key="")
        server._rate_limit_max = 5  # low limit for testing
        server.start()
        time.sleep(0.1)

        import urllib.request
        codes = []
        for _ in range(10):
            try:
                req = urllib.request.Request("http://127.0.0.1:18767/api/health")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    codes.append(resp.status)
            except urllib.error.HTTPError as e:
                codes.append(e.code)

        server.stop()
        # Some should succeed, some should be rate limited
        self.assertIn(200, codes)
        self.assertIn(429, codes)

    def test_get_config(self):
        code, data = self._request("GET", "/api/config")
        self.assertEqual(code, 200)
        self.assertIn("host", data)
        self.assertIn("port", data)

    def test_options(self):
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:18765/api/health", method="OPTIONS")
        req.add_header("Authorization", f"Bearer {self.server.api_key}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_add_contact(self):
        contacts = MagicMock()
        contact = MagicMock()
        contact.to_dict = MagicMock(return_value={"name": "Mom", "contact_id": "c1"})
        contacts.add_contact = MagicMock(return_value=contact)
        self.server.contacts = contacts
        code, data = self._request("POST", "/api/contacts", {
            "name": "Mom",
            "phone": "5551234567",
        })
        self.assertEqual(code, 201)
        self.assertEqual(data["name"], "Mom")

    def test_network_scan(self):
        ops = MagicMock()
        ops.scan_network = MagicMock(return_value=[{"ip": "192.168.1.1"}])
        self.server.network_ops = ops
        code, data = self._request("POST", "/api/network/scan", {})
        self.assertEqual(code, 200)
        self.assertEqual(data["count"], 1)

    def test_emergency_alert(self):
        messaging = MagicMock()
        msg = MagicMock()
        msg.to_dict = MagicMock(return_value={"status": "sent"})
        messaging.send_emergency_alert = MagicMock(return_value=[msg])
        self.server.messaging = messaging
        code, data = self._request("POST", "/api/emergency/alert", {
            "message": "Test emergency",
        })
        self.assertEqual(code, 200)

    def test_threat_resolve(self):
        detector = MagicMock()
        detector.resolve_threat = MagicMock(return_value=True)
        self.server.threat_detector = detector
        code, data = self._request("POST", "/api/threats/resolve", {
            "threat_id": "t1",
            "resolution": "false alarm",
        })
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "resolved")

    def test_stop_server(self):
        self.server.stop()
        self.assertFalse(self.server.is_running)

    # ===========================================================
    # PHONE PROTOCOL ENDPOINTS
    # ===========================================================

    def test_phone_register_no_protocol(self):
        code, data = self._request("POST", "/api/phone/register", {"name": "My Phone"})
        self.assertEqual(code, 404)

    def test_phone_register_success(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/register", {
            "name": "Test Phone",
            "owner": "creator",
            "platform": "android",
        })
        self.assertEqual(code, 201)
        self.assertIn("device_id", data)
        self.assertIn("token", data)
        self.assertEqual(data["name"], "Test Phone")

    def test_phone_register_no_name(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/register", {})
        self.assertEqual(code, 400)

    def test_phone_heartbeat(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        device, _ = proto.register_device("Test Phone")
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/heartbeat", {
            "device_id": device.device_id,
            "battery_level": 75,
            "battery_charging": False,
        })
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "ok")

    def test_phone_heartbeat_no_device_id(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/heartbeat", {})
        self.assertEqual(code, 400)

    def test_phone_heartbeat_unknown_device(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/heartbeat", {
            "device_id": "nonexistent",
        })
        self.assertEqual(code, 404)

    def test_phone_telemetry(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        device, _ = proto.register_device("Test Phone")
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/phone/telemetry", {
            "device_id": device.device_id,
            "data": {"type": "test", "value": 42},
        })
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "received")

    def test_notifications_no_protocol(self):
        code, data = self._request("GET", "/api/notifications?device_id=test")
        self.assertEqual(code, 404)

    def test_notifications_no_device_id(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("GET", "/api/notifications")
        self.assertEqual(code, 400)

    def test_notifications_empty(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        device, _ = proto.register_device("Test Phone")
        self.server.phone_protocol = proto
        code, data = self._request("GET", f"/api/notifications?device_id={device.device_id}")
        self.assertEqual(code, 200)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["notifications"], [])

    def test_notifications_with_pending(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        device, _ = proto.register_device("Test Phone")
        proto.send_notification(device.device_id, "Alert", "Test alert", priority="high")
        self.server.phone_protocol = proto
        code, data = self._request("GET", f"/api/notifications?device_id={device.device_id}")
        self.assertEqual(code, 200)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["notifications"][0]["title"], "Alert")

    def test_notification_delivered(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        device, _ = proto.register_device("Test Phone")
        notif = proto.send_notification(device.device_id, "Alert", "Test alert")
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/notifications/delivered", {
            "notif_id": notif.notif_id,
        })
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "delivered")
        # Verify it's no longer pending
        code, data = self._request("GET", f"/api/notifications?device_id={device.device_id}")
        self.assertEqual(data["count"], 0)

    def test_notification_delivered_no_id(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        self.server.phone_protocol = proto
        code, data = self._request("POST", "/api/notifications/delivered", {})
        self.assertEqual(code, 400)

    def test_phone_devices_list(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        proto.register_device("Phone 1")
        proto.register_device("Phone 2")
        self.server.phone_protocol = proto
        code, data = self._request("GET", "/api/phone/devices")
        self.assertEqual(code, 200)
        self.assertEqual(len(data["devices"]), 2)

    def test_phone_status(self):
        from anubis.phone_protocol import PhoneProtocol
        proto = PhoneProtocol(self.root)
        proto.register_device("Test Phone")
        self.server.phone_protocol = proto
        code, data = self._request("GET", "/api/phone/status")
        self.assertEqual(code, 200)
        self.assertEqual(data["total_devices"], 1)


if __name__ == "__main__":
    unittest.main()
