"""Tests for VoIP calling system."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.voip import (
    VoIPSystem, CallRecord,
    CALL_EMERGENCY, CALL_CONTACT, CALL_CREATOR, CALL_SUCCESSOR,
    CALL_DIALING, CALL_CONNECTED, CALL_FAILED, CALL_REJECTED,
)


class TestCallRecord(unittest.TestCase):
    def test_to_dict(self):
        c = CallRecord(call_id="c1", phone_number="5551234567")
        d = c.to_dict()
        self.assertEqual(d["call_id"], "c1")
        # Phone number should be masked
        self.assertNotEqual(d["phone_number"], "5551234567")

    def test_mask_number(self):
        self.assertEqual(CallRecord._mask_number("123"), "123")
        self.assertEqual(CallRecord._mask_number("5551234567"), "555***4567")


class TestVoIPSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.voip = VoIPSystem(self.root, require_approval=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertFalse(self.voip.get_status()["configured"])

    def test_call_rejected_without_approval(self):
        call = self.voip.make_call("5551234567", call_type=CALL_CONTACT)
        self.assertEqual(call.status, CALL_REJECTED)

    def test_call_approved_but_no_backend(self):
        call = self.voip.make_call(
            "5551234567", call_type=CALL_CONTACT, approved=True
        )
        # Approved but no VoIP backend → failed
        self.assertEqual(call.status, CALL_FAILED)

    def test_emergency_call_requires_approval(self):
        call = self.voip.call_emergency(approved=False)
        self.assertEqual(call.status, CALL_REJECTED)

    def test_emergency_call_approved_no_backend(self):
        call = self.voip.call_emergency(approved=True)
        self.assertEqual(call.status, CALL_FAILED)
        self.assertEqual(call.call_type, CALL_EMERGENCY)

    def test_call_creator_auto_approved(self):
        call = self.voip.call_creator("5551234567", approved=True)
        self.assertTrue(call.approved)
        self.assertEqual(call.call_type, CALL_CREATOR)

    def test_call_successor_requires_approval(self):
        call = self.voip.call_successor("5551234567", approved=False)
        self.assertEqual(call.status, CALL_REJECTED)

    def test_call_successor_approved(self):
        call = self.voip.call_successor("5551234567", approved=True)
        self.assertEqual(call.call_type, CALL_SUCCESSOR)
        self.assertEqual(call.status, CALL_FAILED)  # no backend

    def test_call_contact(self):
        call = self.voip.call_contact("5551234567", "Mom", approved=True)
        self.assertEqual(call.recipient_name, "Mom")
        self.assertEqual(call.call_type, CALL_CONTACT)

    def test_calls_recorded(self):
        self.voip.make_call("5551234567", approved=True)
        calls = self.voip.get_calls()
        self.assertEqual(len(calls), 1)

    def test_get_call(self):
        call = self.voip.make_call("5551234567", approved=True)
        result = self.voip.get_call(call.call_id)
        self.assertIsNotNone(result)

    def test_get_calls_by_type(self):
        self.voip.make_call("5551234567", call_type=CALL_CONTACT, approved=True)
        self.voip.make_call("911", call_type=CALL_EMERGENCY, approved=True)
        contacts = self.voip.get_calls_by_type(CALL_CONTACT)
        emergencies = self.voip.get_emergency_calls()
        self.assertEqual(len(contacts), 1)
        self.assertEqual(len(emergencies), 1)

    def test_rate_limiting(self):
        voip = VoIPSystem(self.root, require_approval=False)
        voip._rate_limit_max = 3
        for _ in range(3):
            voip.make_call("5551234567", approved=True)
        # 4th call should be rate limited
        call = voip.make_call("5551234567", approved=True)
        self.assertEqual(call.status, CALL_FAILED)

    def test_on_call_status_callback(self):
        called = []
        voip = VoIPSystem(
            self.root, require_approval=False,
            on_call_status=lambda c: called.append(c),
        )
        voip.make_call("5551234567", approved=True)
        self.assertEqual(len(called), 1)

    def test_get_status(self):
        status = self.voip.get_status()
        self.assertIn("configured", status)
        self.assertIn("method", status)
        self.assertTrue(status["require_approval"])

    def test_no_approval_required_mode(self):
        voip = VoIPSystem(self.root, require_approval=False)
        call = voip.make_call("5551234567", call_type=CALL_CONTACT)
        # Should not be rejected (no approval needed)
        # But emergency still requires approval
        self.assertNotEqual(call.status, CALL_REJECTED)

    def test_emergency_always_requires_approval(self):
        voip = VoIPSystem(self.root, require_approval=False)
        call = voip.call_emergency(approved=False)
        # Even with require_approval=False, emergency requires approval
        self.assertEqual(call.status, CALL_REJECTED)

    def test_call_reason_recorded(self):
        call = self.voip.make_call(
            "5551234567", approved=True, reason="Fall detected"
        )
        self.assertEqual(call.reason, "Fall detected")


if __name__ == "__main__":
    unittest.main()
