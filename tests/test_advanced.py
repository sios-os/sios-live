"""Tests for Tier 4 advanced modules."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.advanced import (
    EmergencyServices, EmergencyCall,
    MultiLanguage,
    ARGlasses, ARFrame,
    SatelliteAnalyzer, SatelliteImage,
    BlockchainEvidence, EvidenceAnchor,
    ANUBISProtocol, ANUBISPeer,
)


class TestEmergencyServices(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ems = EmergencyServices(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_request_denied_without_approval(self):
        call = self.ems.request_emergency_call("medical", "Fall detected")
        self.assertEqual(call.call_status, "denied")

    def test_request_approved_no_voip(self):
        ems = EmergencyServices(Path(self.tmpdir), on_call_required=lambda c: True)
        call = ems.request_emergency_call("medical", "Fall")
        self.assertEqual(call.call_status, "failed")  # no VoIP
        self.assertEqual(call.approved_by, "creator")

    def test_get_calls(self):
        self.ems.request_emergency_call("fire", "Smoke detected")
        calls = self.ems.get_calls()
        self.assertEqual(len(calls), 1)

    def test_get_status(self):
        status = self.ems.get_status()
        self.assertTrue(status["approval_required"])


class TestMultiLanguage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ml = MultiLanguage(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detect_english(self):
        self.assertEqual(self.ml.detect_language("hello world"), "en")

    def test_detect_spanish(self):
        self.assertEqual(self.ml.detect_language("hola, como estas"), "es")

    def test_detect_french(self):
        self.assertEqual(self.ml.detect_language("bonjour merci"), "fr")

    def test_detect_german(self):
        self.assertEqual(self.ml.detect_language("hallo danke"), "de")

    def test_add_translation(self):
        self.ml.add_translation("greeting", {"en": "Hello", "es": "Hola"})
        self.assertEqual(self.ml.translate("greeting", "es"), "Hola")
        self.assertEqual(self.ml.translate("greeting", "en"), "Hello")

    def test_translate_missing(self):
        self.assertEqual(self.ml.translate("nonexistent"), "nonexistent")

    def test_get_supported_languages(self):
        langs = self.ml.get_supported_languages()
        self.assertGreater(len(langs), 5)
        self.assertIn({"code": "en", "name": "English"}, langs)

    def test_get_status(self):
        status = self.ml.get_status()
        self.assertEqual(status["default_language"], "en")

    def test_persist(self):
        self.ml.add_translation("test", {"en": "Test", "es": "Prueba"})
        ml2 = MultiLanguage(Path(self.tmpdir))
        self.assertEqual(ml2.translate("test", "es"), "Prueba")


class TestARGlasses(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ar = ARGlasses(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_connect(self):
        self.assertTrue(self.ar.connect())
        self.assertTrue(self.ar._connected)

    def test_disconnect(self):
        self.ar.connect()
        self.ar.disconnect()
        self.assertFalse(self.ar._connected)

    def test_process_frame_no_perception(self):
        frame = self.ar.process_frame("/fake/path.jpg")
        self.assertEqual(frame.faces_detected, 0)

    def test_process_frame_with_perception(self):
        perception = MagicMock()
        face_result = MagicMock(face_count=1, is_known=True, name="Storm")
        perception.faces.identify = MagicMock(return_value=face_result)
        scene = MagicMock(objects=[], people_count=1)
        perception.objects.recognize = MagicMock(return_value=scene)
        ar = ARGlasses(Path(self.tmpdir), perception=perception)
        frame = ar.process_frame("/fake/path.jpg")
        self.assertEqual(frame.faces_detected, 1)
        self.assertIn("Storm", frame.overlay_text)

    def test_set_overlay(self):
        self.ar.process_frame("/fake/path.jpg")
        self.ar.set_overlay("Warning: intruder")
        self.assertEqual(self.ar._last_frame.overlay_text, "Warning: intruder")

    def test_add_alert(self):
        self.ar.process_frame("/fake/path.jpg")
        self.ar.add_alert("Person behind you")
        self.assertIn("Person behind you", self.ar._last_frame.overlay_alerts)

    def test_enable_disable_overlay(self):
        self.ar.disable_overlay()
        self.assertFalse(self.ar._overlay_enabled)
        self.ar.enable_overlay()
        self.assertTrue(self.ar._overlay_enabled)

    def test_get_status(self):
        status = self.ar.get_status()
        self.assertIn("connected", status)


class TestSatelliteAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sat = SatelliteAnalyzer(Path(self.tmpdir), latitude=41.8, longitude=-87.6)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertEqual(self.sat.latitude, 41.8)

    def test_get_status(self):
        status = self.sat.get_status()
        self.assertEqual(status["latitude"], 41.8)

    def test_get_images_empty(self):
        self.assertEqual(self.sat.get_images(), [])

    def test_analyze_changes(self):
        changes = self.sat.analyze_changes("img1.jpg", "img2.jpg")
        self.assertEqual(changes, [])


class TestBlockchainEvidence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.bc = BlockchainEvidence(Path(self.tmpdir), blockchain="polygon")

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_anchor_evidence(self):
        anchor = self.bc.anchor_evidence("important evidence data")
        self.assertIsNotNone(anchor.evidence_hash)
        self.assertEqual(anchor.blockchain, "polygon")
        self.assertFalse(anchor.confirmed)

    def test_anchor_evidence_bytes(self):
        anchor = self.bc.anchor_evidence(b"binary evidence")
        self.assertIsNotNone(anchor.evidence_hash)

    def test_evidence_hash_consistent(self):
        anchor1 = self.bc.anchor_evidence("test data")
        anchor2 = self.bc.anchor_evidence("test data")
        self.assertEqual(anchor1.evidence_hash, anchor2.evidence_hash)

    def test_verify_anchor(self):
        anchor = self.bc.anchor_evidence("test")
        result = self.bc.verify_anchor(anchor.anchor_id)
        self.assertEqual(result["evidence_hash"], anchor.evidence_hash)

    def test_verify_nonexistent(self):
        result = self.bc.verify_anchor("nonexistent")
        self.assertIn("error", result)

    def test_get_anchors(self):
        self.bc.anchor_evidence("test1")
        self.bc.anchor_evidence("test2")
        anchors = self.bc.get_anchors()
        self.assertEqual(len(anchors), 2)

    def test_get_status(self):
        self.bc.anchor_evidence("test")
        status = self.bc.get_status()
        self.assertEqual(status["blockchain"], "polygon")
        self.assertEqual(status["total_anchors"], 1)


class TestANUBISProtocol(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.proto = ANUBISProtocol(Path(self.tmpdir), self_id="anubis-home")

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_peer(self):
        peer = self.proto.add_peer("Workshop ANUBIS", "192.168.1.50", 8765)
        self.assertEqual(peer.name, "Workshop ANUBIS")
        self.assertEqual(peer.address, "192.168.1.50")

    def test_remove_peer(self):
        peer = self.proto.add_peer("Test", "192.168.1.50")
        self.assertTrue(self.proto.remove_peer(peer.peer_id))
        self.assertEqual(len(self.proto.get_peers()), 0)

    def test_check_peer_offline(self):
        peer = self.proto.add_peer("Test", "192.168.1.99", 99999)
        status = self.proto.check_peer_status(peer.peer_id)
        self.assertEqual(status, "offline")

    def test_check_nonexistent_peer(self):
        self.assertEqual(self.proto.check_peer_status("nonexistent"), "not_found")

    def test_send_message_no_peer(self):
        result = self.proto.send_message("nonexistent", "test", {})
        self.assertFalse(result["success"])

    def test_send_message_offline(self):
        peer = self.proto.add_peer("Test", "192.168.1.99", 99999)
        result = self.proto.send_message(peer.peer_id, "test", {"data": "test"})
        self.assertFalse(result["success"])

    def test_share_threat_intel(self):
        peer = self.proto.add_peer("Test", "192.168.1.99", 99999)
        result = self.proto.share_threat_intel(peer.peer_id, {"threat": "intruder"})
        self.assertFalse(result["success"])  # peer offline

    def test_get_online_peers(self):
        self.proto.add_peer("Test", "192.168.1.99", 99999)
        online = self.proto.get_online_peers()
        self.assertEqual(len(online), 0)

    def test_get_status(self):
        self.proto.add_peer("Test", "192.168.1.50")
        status = self.proto.get_status()
        self.assertEqual(status["self_id"], "anubis-home")
        self.assertEqual(status["total_peers"], 1)

    def test_persist(self):
        self.proto.add_peer("Test", "192.168.1.50")
        proto2 = ANUBISProtocol(Path(self.tmpdir))
        self.assertEqual(len(proto2.get_peers()), 1)


if __name__ == "__main__":
    unittest.main()
