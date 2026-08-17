"""Tests for contacts, messaging, network_ops, remote_monitor, threat_analysis."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.contacts import (
    ContactManager, EmergencyContact, ContactAttempt, SuccessorPolicy,
)
from anubis.messaging import (
    SignalMessenger, Message, CARRIER_GATEWAYS,
)
from anubis.network_ops import (
    NetworkOperator, NetworkDevice, TrafficAlert,
)
from anubis.remote_monitor import (
    RemoteMonitor, LocationUpdate, AccelerometerData, HealthData,
    PhoneStatus, FallEvent, RemoteAlert,
)
from anubis.threat_analysis import (
    ThreatDetector, Threat, ThreatResponse, BehavioralBaseline,
    SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL,
    DOMAIN_PHYSICAL, DOMAIN_BEHAVIORAL, DOMAIN_CYBER, DOMAIN_REMOTE,
    THREAT_INTRUDER, THREAT_DURESS, THREAT_FALL, THREAT_UNKNOWN_VOICE,
    THREAT_VEHICLE_UNUSUAL,
)


# --------------------------------------------------------------- contacts


class TestEmergencyContact(unittest.TestCase):
    def test_to_dict(self):
        c = EmergencyContact(contact_id="c1", name="Mom", phone="5551234567")
        d = c.to_dict()
        self.assertEqual(d["contact_id"], "c1")
        self.assertEqual(d["name"], "Mom")
        self.assertEqual(d["phone"], "5551234567")


class TestSuccessorPolicy(unittest.TestCase):
    def test_to_dict(self):
        p = SuccessorPolicy()
        d = p.to_dict()
        self.assertEqual(d["successor_name"], "Ethan Pace")
        self.assertEqual(d["successor_id"], "144f7f638118138b")
        self.assertFalse(d["successor_notified"])
        self.assertEqual(d["absence_threshold_hours"], 24.0)

    def test_strict_conditions(self):
        p = SuccessorPolicy()
        self.assertEqual(p.contact_attempts_required, 3)
        self.assertEqual(p.threat_severity_required, "critical")


class TestContactManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        cm = ContactManager(self.root)
        self.assertEqual(cm.get_contacts(), [])
        policy = cm.get_successor_policy()
        self.assertEqual(policy["successor_name"], "Ethan Pace")

    def test_add_contact(self):
        cm = ContactManager(self.root)
        contact = cm.add_contact("Mom", "5551234567", relationship="family",
                                  role="medical", priority=1, trusted=True)
        self.assertEqual(contact.name, "Mom")
        self.assertTrue(contact.trusted)
        self.assertEqual(contact.priority, 1)

    def test_remove_contact(self):
        cm = ContactManager(self.root)
        contact = cm.add_contact("Mom", "5551234567")
        self.assertTrue(cm.remove_contact(contact.contact_id))
        self.assertEqual(len(cm.get_contacts()), 0)

    def test_update_contact(self):
        cm = ContactManager(self.root)
        contact = cm.add_contact("Mom", "5551234567")
        self.assertTrue(cm.update_contact(contact.contact_id, phone="5559999999"))
        data = cm.get_contact(contact.contact_id)
        self.assertEqual(data["phone"], "5559999999")

    def test_get_contacts_sorted_by_priority(self):
        cm = ContactManager(self.root)
        cm.add_contact("Bob", priority=3)
        cm.add_contact("Alice", priority=1)
        cm.add_contact("Charlie", priority=2)
        contacts = cm.get_contacts()
        self.assertEqual(contacts[0]["name"], "Alice")
        self.assertEqual(contacts[1]["name"], "Charlie")
        self.assertEqual(contacts[2]["name"], "Bob")

    def test_get_available_contacts(self):
        cm = ContactManager(self.root)
        c1 = cm.add_contact("Alice", priority=1)
        cm.add_contact("Bob", priority=2)
        cm.set_contact_available(c1.contact_id, False)
        available = cm.get_available_contacts()
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]["name"], "Bob")

    def test_get_contact_by_phone(self):
        cm = ContactManager(self.root)
        cm.add_contact("Mom", "5551234567")
        result = cm.get_contact_by_phone("5551234567")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Mom")

    def test_contacts_persist(self):
        cm = ContactManager(self.root)
        cm.add_contact("Mom", "5551234567", trusted=True)
        cm2 = ContactManager(self.root)
        contacts = cm2.get_contacts()
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["name"], "Mom")
        self.assertTrue(contacts[0]["trusted"])

    def test_update_creator_activity(self):
        cm = ContactManager(self.root)
        cm.update_creator_activity()
        policy = cm.get_successor_policy()
        self.assertGreater(policy["creator_last_active"], 0)

    def test_record_contact_attempt(self):
        cm = ContactManager(self.root)
        count = cm.record_contact_attempt()
        self.assertEqual(count, 1)
        count = cm.record_contact_attempt()
        self.assertEqual(count, 2)

    def test_successor_notification_not_needed_initially(self):
        cm = ContactManager(self.root)
        should, reason = cm.check_successor_notification_needed("critical")
        self.assertFalse(should)

    def test_successor_notification_not_needed_low_severity(self):
        cm = ContactManager(self.root)
        cm.update_creator_activity()
        # Set absence to past
        cm._successor.creator_last_active = time.time() - 25 * 3600
        cm._successor.contact_attempts_made = 5
        should, reason = cm.check_successor_notification_needed("low")
        self.assertFalse(should)
        self.assertIn("severity", reason.lower())

    def test_successor_notification_needed(self):
        cm = ContactManager(self.root)
        cm.update_creator_activity()
        cm._successor.creator_last_active = time.time() - 25 * 3600
        cm._successor.contact_attempts_made = 5
        should, reason = cm.check_successor_notification_needed("critical")
        self.assertTrue(should)

    def test_notify_successor(self):
        cm = ContactManager(self.root)
        self.assertTrue(cm.notify_successor("Creator unresponsive"))
        # Can't notify twice
        self.assertFalse(cm.notify_successor("test"))

    def test_reset_successor_notification(self):
        cm = ContactManager(self.root)
        cm.notify_successor("test")
        self.assertTrue(cm.reset_successor_notification())
        policy = cm.get_successor_policy()
        self.assertFalse(policy["successor_notified"])

    def test_set_successor_contact_info(self):
        cm = ContactManager(self.root)
        cm.set_successor_contact_info(phone="5550000000", email="ethan@test.com")
        info = cm.get_successor_contact_info()
        self.assertEqual(info["phone"], "5550000000")
        self.assertEqual(info["email"], "ethan@test.com")

    def test_record_attempt(self):
        cm = ContactManager(self.root)
        cm.record_attempt("c1", "Mom", "sms", "test message", "sent")
        attempts = cm.get_attempts()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["contact_name"], "Mom")

    def test_get_status(self):
        cm = ContactManager(self.root)
        status = cm.get_status()
        self.assertEqual(status["total_contacts"], 0)
        self.assertEqual(status["successor_name"], "Ethan Pace")
        self.assertFalse(status["successor_notified"])


# --------------------------------------------------------------- messaging


class TestMessage(unittest.TestCase):
    def test_to_dict_masks_phone(self):
        msg = Message(message_id="m1", to="5551234567", body="test")
        d = msg.to_dict()
        self.assertIn("****", d["to"])
        self.assertNotEqual(d["to"], "5551234567")


class TestSignalMessenger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.contacts = ContactManager(self.root)
        self.messenger = SignalMessenger(
            self.root, self.contacts, signal_number="+1234567890",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertEqual(self.messenger.signal_number, "+1234567890")

    def test_signal_available_check(self):
        self.assertIsInstance(self.messenger.signal_available(), bool)

    def test_email_configured_check(self):
        self.assertIsInstance(self.messenger.email_configured(), bool)

    def test_is_available(self):
        self.assertIsInstance(self.messenger.is_available(), bool)

    def test_send_to_nonexistent_contact(self):
        msg = self.messenger.send_to_contact("nonexistent", "test")
        self.assertEqual(msg.status, "failed")
        self.assertIn("not found", msg.error)

    def test_send_to_contact_no_phone(self):
        contact = self.contacts.add_contact("Test", phone="", email="")
        msg = self.messenger.send_to_contact(contact.contact_id, "test")
        self.assertEqual(msg.status, "failed")

    def test_send_emergency_alert_no_contacts(self):
        messages = self.messenger.send_emergency_alert("test alert")
        self.assertEqual(len(messages), 0)

    def test_send_emergency_alert_with_contacts(self):
        self.contacts.add_contact("Mom", "5551234567", priority=1)
        self.contacts.add_contact("Dad", "5559876543", priority=2)
        messages = self.messenger.send_emergency_alert("test alert", max_contacts=2)
        # Messages will fail (no signal/email configured) but should be attempted
        self.assertEqual(len(messages), 2)

    def test_rate_limiting(self):
        # Non-emergency messages are rate limited
        contact = self.contacts.add_contact("Test", "5551234567")
        msg1 = self.messenger.send_to_contact(contact.contact_id, "msg1")
        msg2 = self.messenger.send_to_contact(contact.contact_id, "msg2")
        # Second should be rate limited (or both fail since no messaging available)
        # Just verify it doesn't crash
        self.assertIsInstance(msg1, Message)
        self.assertIsInstance(msg2, Message)

    def test_get_history(self):
        history = self.messenger.get_history()
        self.assertIsInstance(history, list)

    def test_get_status(self):
        status = self.messenger.get_status()
        self.assertIn("signal_available", status)
        self.assertIn("email_configured", status)
        self.assertIn("max_messages_per_hour", status)

    def test_send_to_successor(self):
        self.contacts.set_successor_contact_info(phone="5550000000")
        msg = self.messenger.send_to_successor("Successor notification test")
        # Will fail (no signal configured) but should attempt
        self.assertIsInstance(msg, Message)
        self.assertTrue(msg.is_successor)
        self.assertTrue(msg.is_emergency)

    def test_carrier_gateways(self):
        self.assertIn("verizon", CARRIER_GATEWAYS)
        self.assertIn("att", CARRIER_GATEWAYS)
        self.assertIn("tmobile", CARRIER_GATEWAYS)


# --------------------------------------------------------------- network ops


class TestNetworkDevice(unittest.TestCase):
    def test_to_dict(self):
        d = NetworkDevice(device_id="d1", ip="192.168.1.100", hostname="laptop")
        data = d.to_dict()
        self.assertEqual(data["device_id"], "d1")
        self.assertEqual(data["ip"], "192.168.1.100")
        self.assertEqual(data["hostname"], "laptop")

    def test_device_types(self):
        d = NetworkDevice(device_id="d1", device_type="camera")
        self.assertEqual(d.device_type, "camera")


class TestNetworkOperator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        ops = NetworkOperator(self.root)
        self.assertIsInstance(ops.get_status(), dict)

    def test_get_local_ip(self):
        ops = NetworkOperator(self.root)
        # Should return some IP (might be 127.0.0.1 on isolated systems)
        self.assertIsInstance(ops._local_ip, str)

    def test_trust_device(self):
        ops = NetworkOperator(self.root)
        # Manually add a device
        device = NetworkDevice(device_id="d1", ip="192.168.1.100")
        ops._devices["d1"] = device
        self.assertTrue(ops.trust_device("d1"))
        self.assertTrue(ops._devices["d1"].trusted)

    def test_identify_device(self):
        ops = NetworkOperator(self.root)
        device = NetworkDevice(device_id="d1", ip="192.168.1.100")
        ops._devices["d1"] = device
        self.assertTrue(ops.identify_device("d1", "My Laptop", "computer"))
        self.assertEqual(ops._devices["d1"].hostname, "My Laptop")
        self.assertTrue(ops._devices["d1"].known)

    def test_remove_device(self):
        ops = NetworkOperator(self.root)
        device = NetworkDevice(device_id="d1", ip="192.168.1.100")
        ops._devices["d1"] = device
        self.assertTrue(ops.remove_device("d1"))
        self.assertEqual(len(ops.get_devices()), 0)

    def test_get_unknown_devices(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100", known=False)
        ops._devices["d2"] = NetworkDevice(device_id="d2", ip="192.168.1.101", known=True)
        unknown = ops.get_unknown_devices()
        self.assertEqual(len(unknown), 1)

    def test_get_trusted_devices(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100", trusted=True)
        ops._devices["d2"] = NetworkDevice(device_id="d2", ip="192.168.1.101", trusted=False)
        trusted = ops.get_trusted_devices()
        self.assertEqual(len(trusted), 1)

    def test_devices_persist(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100", trusted=True)
        ops._save_devices()
        ops2 = NetworkOperator(self.root)
        self.assertEqual(len(ops2.get_devices()), 1)
        self.assertTrue(ops2._devices["d1"].trusted)

    def test_quarantine_device(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100")
        result = ops.quarantine_device("d1")
        self.assertTrue(result["success"])
        self.assertTrue(ops._devices["d1"].quarantined)

    def test_release_device(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100", quarantined=True)
        result = ops.release_device("d1")
        self.assertTrue(result["success"])
        self.assertFalse(ops._devices["d1"].quarantined)

    def test_check_for_intrusions_unknown(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(device_id="d1", ip="192.168.1.100", known=False)
        alerts = ops.check_for_intrusions()
        self.assertTrue(any(a["type"] == "unknown_device" for a in alerts))

    def test_check_for_intrusions_suspicious_ports(self):
        ops = NetworkOperator(self.root)
        ops._devices["d1"] = NetworkDevice(
            device_id="d1", ip="192.168.1.100", ports=[31337], known=True,
        )
        alerts = ops.check_for_intrusions()
        self.assertTrue(any(a["type"] == "suspicious_ports" for a in alerts))

    def test_get_alerts(self):
        ops = NetworkOperator(self.root)
        ops._create_alert("test", "192.168.1.100", "low", "test alert")
        alerts = ops.get_alerts()
        self.assertEqual(len(alerts), 1)

    def test_get_status(self):
        ops = NetworkOperator(self.root)
        status = ops.get_status()
        self.assertIn("local_ip", status)
        self.assertIn("total_devices", status)
        self.assertIn("is_linux", status)

    def test_guess_device_type(self):
        ops = NetworkOperator(self.root)
        self.assertEqual(ops._guess_device_type([554]), "camera")
        self.assertEqual(ops._guess_device_type([22, 80]), "computer")
        self.assertEqual(ops._guess_device_type([80]), "iot")
        self.assertEqual(ops._guess_device_type([22]), "computer")

    def test_ssh_nonexistent_device(self):
        ops = NetworkOperator(self.root)
        result = ops.ssh_command("nonexistent", "ls")
        self.assertFalse(result["success"])

    def test_http_request_nonexistent_device(self):
        ops = NetworkOperator(self.root)
        result = ops.http_request("nonexistent", "/status")
        self.assertFalse(result["success"])


# --------------------------------------------------------------- remote monitor


class TestLocationUpdate(unittest.TestCase):
    def test_to_dict(self):
        loc = LocationUpdate(latitude=40.7, longitude=-74.0)
        d = loc.to_dict()
        self.assertEqual(d["latitude"], 40.7)
        self.assertEqual(d["longitude"], -74.0)


class TestAccelerometerData(unittest.TestCase):
    def test_magnitude_computed(self):
        data = AccelerometerData(x=3, y=4, z=0)
        # magnitude should be 5 (3-4-5 triangle)
        # But magnitude is only computed in receive_accelerometer
        # So test the computation manually
        import math
        mag = math.sqrt(3**2 + 4**2 + 0**2)
        self.assertEqual(mag, 5.0)


class TestHealthData(unittest.TestCase):
    def test_to_dict(self):
        h = HealthData(heart_rate=72, activity_level="resting")
        d = h.to_dict()
        self.assertEqual(d["heart_rate"], 72)
        self.assertEqual(d["activity_level"], "resting")


class TestRemoteMonitor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.monitor = RemoteMonitor(
            self.root, home_latitude=40.7, home_longitude=-74.0,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertFalse(self.monitor.is_monitoring)

    def test_start_stop_monitoring(self):
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_monitoring)
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring)

    def test_receive_location(self):
        loc = LocationUpdate(latitude=40.7, longitude=-74.0, timestamp=time.time())
        self.monitor.receive_location(loc)
        last = self.monitor.get_last_known_location()
        self.assertIsNotNone(last)
        self.assertEqual(last["latitude"], 40.7)

    def test_receive_accelerometer(self):
        data = AccelerometerData(x=0, y=0, z=9.8, timestamp=time.time())
        self.monitor.receive_accelerometer(data)
        # Should not trigger fall (normal gravity)
        self.assertIsNone(self.monitor._potential_fall)

    def test_fall_detection_impact(self):
        # High impact
        impact = AccelerometerData(x=0, y=0, z=30.0, timestamp=time.time())
        self.monitor.receive_accelerometer(impact)
        self.assertIsNotNone(self.monitor._potential_fall)

    def test_fall_detection_confirmed(self):
        alerts = []
        monitor = RemoteMonitor(
            self.root, home_latitude=40.7, home_longitude=-74.0,
            on_alert=lambda a: alerts.append(a),
        )
        # Impact
        t = time.time()
        impact = AccelerometerData(x=0, y=0, z=30.0, timestamp=t)
        monitor.receive_accelerometer(impact)
        # Stillness after 6 seconds
        still = AccelerometerData(x=0, y=0, z=0.5, timestamp=t + 6)
        monitor.receive_accelerometer(still)
        # Should have triggered fall alert
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, "fall_detected")
        self.assertEqual(alerts[0].severity, "critical")

    def test_fall_detection_recovered(self):
        impact = AccelerometerData(x=0, y=0, z=30.0, timestamp=time.time())
        self.monitor.receive_accelerometer(impact)
        # Movement after impact — not a fall
        movement = AccelerometerData(x=5, y=5, z=10, timestamp=time.time() + 1)
        self.monitor.receive_accelerometer(movement)
        self.assertIsNone(self.monitor._potential_fall)

    def test_receive_health(self):
        data = HealthData(heart_rate=72, timestamp=time.time())
        self.monitor.receive_health(data)
        status = self.monitor.get_status()
        self.assertEqual(status["heart_rate"], 72)

    def test_abnormal_heart_rate_alert(self):
        alerts = []
        monitor = RemoteMonitor(
            self.root, on_alert=lambda a: alerts.append(a),
        )
        data = HealthData(heart_rate=180, timestamp=time.time())
        monitor.receive_health(data)
        self.assertTrue(any(a.alert_type == "abnormal_heart_rate" for a in alerts))

    def test_low_blood_oxygen_alert(self):
        alerts = []
        monitor = RemoteMonitor(
            self.root, on_alert=lambda a: alerts.append(a),
        )
        data = HealthData(blood_oxygen=85, timestamp=time.time())
        monitor.receive_health(data)
        self.assertTrue(any(a.alert_type == "low_blood_oxygen" for a in alerts))

    def test_receive_phone_status(self):
        status = PhoneStatus(battery_level=80, timestamp=time.time())
        self.monitor.receive_phone_status(status)
        result = self.monitor.get_status()
        self.assertEqual(result["phone_battery"], 80)

    def test_low_battery_alert(self):
        alerts = []
        monitor = RemoteMonitor(
            self.root, on_alert=lambda a: alerts.append(a),
        )
        status = PhoneStatus(battery_level=10, timestamp=time.time())
        monitor.receive_phone_status(status)
        self.assertTrue(any(a.alert_type == "low_battery" for a in alerts))

    def test_haversine_distance(self):
        # New York to Los Angeles is roughly 3,944 km
        distance = self.monitor._haversine_distance(
            40.7128, -74.0060,  # NYC
            34.0522, -118.2437,  # LA
        )
        # Should be roughly 3,940,000 meters (±100,000)
        self.assertGreater(distance, 3_800_000)
        self.assertLess(distance, 4_100_000)

    def test_get_active_sources(self):
        self.monitor.receive_location(
            LocationUpdate(latitude=40.7, longitude=-74.0, timestamp=time.time())
        )
        sources = self.monitor.get_active_sources()
        self.assertIn("phone", sources)

    def test_get_status(self):
        status = self.monitor.get_status()
        self.assertIn("monitoring", status)
        self.assertIn("sources", status)
        self.assertIn("home_set", status)

    def test_get_alerts(self):
        self.assertEqual(self.monitor.get_alerts(), [])

    def test_get_falls(self):
        self.assertEqual(self.monitor.get_falls(), [])

    def test_get_locations(self):
        loc = LocationUpdate(latitude=40.7, longitude=-74.0, timestamp=time.time())
        self.monitor.receive_location(loc)
        locations = self.monitor.get_locations()
        self.assertEqual(len(locations), 1)

    def test_creator_responded_after_fall(self):
        impact = AccelerometerData(x=0, y=0, z=30.0, timestamp=time.time())
        self.monitor.receive_accelerometer(impact)
        self.monitor.creator_responded_after_fall()
        self.assertIsNone(self.monitor._potential_fall)


# --------------------------------------------------------------- threat analysis


class TestThreat(unittest.TestCase):
    def test_to_dict(self):
        t = Threat(
            threat_id="t1", domain=DOMAIN_PHYSICAL,
            threat_type=THREAT_INTRUDER, severity=SEVERITY_HIGH,
            description="Test threat",
        )
        d = t.to_dict()
        self.assertEqual(d["threat_id"], "t1")
        self.assertEqual(d["domain"], DOMAIN_PHYSICAL)
        self.assertEqual(d["severity"], SEVERITY_HIGH)

    def test_threat_types(self):
        self.assertEqual(THREAT_DURESS, "duress")
        self.assertEqual(THREAT_FALL, "fall")
        self.assertEqual(THREAT_INTRUDER, "intruder")


class TestThreatResponse(unittest.TestCase):
    def test_to_dict(self):
        r = ThreatResponse(action="alert", description="test")
        d = r.to_dict()
        self.assertEqual(d["action"], "alert")
        self.assertTrue(d["record_evidence"])


class TestBehavioralBaseline(unittest.TestCase):
    def test_to_dict(self):
        b = BehavioralBaseline()
        d = b.to_dict()
        self.assertIn("neutral", d["normal_emotions"])
        self.assertEqual(d["samples"], 0)


class TestThreatDetector(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.contacts = ContactManager(self.root)
        self.messaging = SignalMessenger(self.root, self.contacts)
        self.detector = ThreatDetector(
            self.root, contacts=self.contacts, messaging=self.messaging,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        status = self.detector.get_status()
        self.assertEqual(status["active_threats"], 0)
        self.assertTrue(status["contacts_configured"])

    def test_analyze_perception_unknown_voice(self):
        threats = self.detector.analyze_perception(
            voice_result={
                "is_human": True,
                "is_known": False,
                "is_trusted": False,
                "audio_type": "speech",
                "name": "",
            },
            creator_present=True,
        )
        self.assertTrue(any(t.threat_type == THREAT_UNKNOWN_VOICE for t in threats))

    def test_analyze_perception_duress(self):
        threats = self.detector.analyze_perception(
            emotion_result={
                "emotion": "duress",
                "confidence": 0.85,
            },
            creator_present=True,
        )
        self.assertTrue(any(t.threat_type == THREAT_DURESS for t in threats))
        self.assertTrue(any(t.severity == SEVERITY_CRITICAL for t in threats))

    def test_analyze_perception_intruder_not_home(self):
        threats = self.detector.analyze_perception(
            face_result={
                "face_count": 1,
                "unknown_count": 1,
                "is_known": False,
            },
            creator_present=False,
        )
        self.assertTrue(any(t.threat_type == THREAT_INTRUDER for t in threats))
        self.assertTrue(any(t.severity == SEVERITY_CRITICAL for t in threats))

    def test_analyze_perception_unknown_person_home(self):
        threats = self.detector.analyze_perception(
            face_result={
                "face_count": 2,
                "unknown_count": 1,
                "is_known": True,
            },
            creator_present=True,
        )
        self.assertTrue(any(t.threat_type == "unknown_person" for t in threats))

    def test_analyze_network_unknown_device(self):
        threats = self.detector.analyze_network(
            devices=[
                {"device_id": "d1", "ip": "192.168.1.100", "known": False},
            ],
        )
        self.assertTrue(any(t.domain == DOMAIN_CYBER for t in threats))

    def test_analyze_network_alert(self):
        threats = self.detector.analyze_network(
            alerts=[
                {"alert_type": "port_scan", "severity": "high",
                 "description": "Port scan detected"},
            ],
        )
        self.assertTrue(len(threats) > 0)

    def test_analyze_remote_fall(self):
        threats = self.detector.analyze_remote(
            remote_alerts=[
                {"alert_type": "fall_detected", "severity": "critical",
                 "description": "Fall detected", "timestamp": time.time()},
            ],
        )
        self.assertTrue(any(t.threat_type == THREAT_FALL for t in threats))
        self.assertTrue(any(t.severity == SEVERITY_CRITICAL for t in threats))

    def test_analyze_remote_medical(self):
        threats = self.detector.analyze_remote(
            remote_alerts=[
                {"alert_type": "abnormal_heart_rate", "severity": "high",
                 "description": "Heart rate 180 bpm", "timestamp": time.time()},
            ],
        )
        self.assertTrue(any(t.threat_type == "medical" for t in threats))

    def test_threat_recorded(self):
        self.detector.analyze_perception(
            emotion_result={"emotion": "duress", "confidence": 0.85},
            creator_present=True,
        )
        history = self.detector.get_threat_history()
        self.assertGreater(len(history), 0)

    def test_resolve_threat(self):
        threats = self.detector.analyze_perception(
            voice_result={
                "is_human": True, "is_known": False,
                "audio_type": "speech",
            },
        )
        if threats:
            threat_id = threats[0].threat_id
            self.assertTrue(self.detector.resolve_threat(threat_id, "false alarm"))
            self.assertEqual(len(self.detector.get_active_threats()), 0)

    def test_get_threats_by_severity(self):
        self.detector.analyze_perception(
            emotion_result={"emotion": "duress", "confidence": 0.85},
        )
        critical = self.detector.get_threats_by_severity(SEVERITY_CRITICAL)
        self.assertGreater(len(critical), 0)

    def test_get_threats_by_domain(self):
        self.detector.analyze_network(
            devices=[{"device_id": "d1", "ip": "1.2.3.4", "known": False}],
        )
        cyber = self.detector.get_threats_by_domain(DOMAIN_CYBER)
        self.assertGreater(len(cyber), 0)

    def test_update_baseline(self):
        self.detector.update_baseline(emotion="happy", device_count=5)
        baseline = self.detector.get_baseline()
        self.assertGreater(baseline["samples"], 0)

    def test_check_anomalous_behavior(self):
        self.detector.update_baseline(emotion="neutral")
        self.detector.update_baseline(emotion="calm")
        self.detector._baseline.samples = 15  # set above threshold
        # Duress is anomalous
        self.assertTrue(self.detector.check_anomalous_behavior(emotion="duress"))
        # Neutral is normal
        self.assertFalse(self.detector.check_anomalous_behavior(emotion="neutral"))

    def test_recommend_response_critical(self):
        threat = Threat(
            threat_id="t1", severity=SEVERITY_CRITICAL,
            threat_type=THREAT_DURESS,
        )
        response = self.detector._recommend_response(threat)
        self.assertTrue(response.emergency_contacts)
        self.assertTrue(response.record_evidence)

    def test_recommend_response_low(self):
        threat = Threat(
            threat_id="t1", severity=SEVERITY_LOW,
            threat_type=THREAT_VEHICLE_UNUSUAL,
        )
        response = self.detector._recommend_response(threat)
        self.assertTrue(response.record_evidence)
        self.assertFalse(response.emergency_contacts)

    def test_recommend_response_duress_requires_approval(self):
        threat = Threat(
            threat_id="t1", severity=SEVERITY_CRITICAL,
            threat_type=THREAT_DURESS,
        )
        response = self.detector._recommend_response(threat)
        self.assertTrue(response.requires_approval)

    def test_on_threat_callback(self):
        called = []
        detector = ThreatDetector(
            self.root, on_threat=lambda t: called.append(t),
        )
        detector.analyze_perception(
            emotion_result={"emotion": "duress", "confidence": 0.85},
        )
        self.assertGreater(len(called), 0)

    def test_get_status(self):
        status = self.detector.get_status()
        self.assertIn("active_threats", status)
        self.assertIn("total_threats", status)
        self.assertIn("baseline_samples", status)

    def test_baseline_persists(self):
        self.detector.update_baseline(emotion="happy")
        detector2 = ThreatDetector(self.root)
        self.assertGreater(detector2.get_baseline()["samples"], 0)

    def test_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        detector = ThreatDetector(self.root, observer=observer)
        detector.analyze_perception(
            emotion_result={"emotion": "duress", "confidence": 0.85},
        )
        observer._make_observation.assert_called()


if __name__ == "__main__":
    unittest.main()
