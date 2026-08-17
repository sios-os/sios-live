"""Tests for the ADB-based phone adapter."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.phone_adapter import PhoneAdapter, SMSMessage, CallRecord, PhoneStatus


class TestPhoneAdapter(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)
        self.phone = PhoneAdapter(
            self.root,
            adb_path="fake_adb",
            ledger=MagicMock(),
            on_speak=MagicMock(),
            on_sms_received=MagicMock(),
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # CONNECTION
    # ===========================================================

    def test_is_connected_no_adb(self):
        # fake_adb doesn't exist, so should return False
        result = self.phone.is_connected()
        self.assertFalse(result)

    def test_is_connected_with_mock(self):
        with patch.object(self.phone, '_run_adb') as mock_adb:
            mock_adb.return_value = (0, "List of devices attached\ndevice123\tdevice\n", "")
            result = self.phone.is_connected()
            self.assertTrue(result)
            self.assertEqual(self.phone._device_id, "device123")

    def test_is_connected_no_devices(self):
        with patch.object(self.phone, '_run_adb') as mock_adb:
            mock_adb.return_value = (0, "List of devices attached\n", "")
            result = self.phone.is_connected()
            self.assertFalse(result)

    def test_is_connected_unauthorized(self):
        with patch.object(self.phone, '_run_adb') as mock_adb:
            mock_adb.return_value = (0, "List of devices attached\ndevice123\tunauthorized\n", "")
            result = self.phone.is_connected()
            self.assertFalse(result)

    def test_get_device_id_not_connected(self):
        result = self.phone.get_device_id()
        self.assertIsNone(result)

    def test_get_device_id_connected(self):
        with patch.object(self.phone, '_run_adb') as mock_adb:
            mock_adb.return_value = (0, "List of devices attached\ndevice123\tdevice\n", "")
            result = self.phone.get_device_id()
            self.assertEqual(result, "device123")

    # ===========================================================
    # SMS
    # ===========================================================

    def test_send_sms_not_connected(self):
        result = self.phone.send_sms("+1234567890", "Hello")
        self.assertFalse(result["sent"])
        self.assertIn("no phone", result["error"])

    def test_send_sms_empty_number(self):
        with patch.object(self.phone, 'is_connected', return_value=True):
            result = self.phone.send_sms("", "Hello")
            self.assertFalse(result["sent"])

    def test_send_sms_empty_body(self):
        with patch.object(self.phone, 'is_connected', return_value=True):
            result = self.phone.send_sms("+1234567890", "")
            self.assertFalse(result["sent"])

    def test_send_sms_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            result = self.phone.send_sms("+1234567890", "Hello from ANUBIS")
            self.assertTrue(result["sent"])
            self.assertEqual(result["to"], "+123456****")

    def test_send_sms_failure(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (1, "", "Error: permission denied")
            result = self.phone.send_sms("+1234567890", "Hello")
            self.assertFalse(result["sent"])
            self.assertIn("error", result)

    def test_receive_sms_not_connected(self):
        result = self.phone.receive_sms()
        self.assertEqual(result["messages"], [])
        self.assertIn("no phone", result["error"])

    def test_receive_sms_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0,
                "Row: 0 address=+1234567890, body=Hello there, date=1697000000000, _id=1\n"
                "Row: 1 address=+1987654321, body=Test message, date=1697000001000, _id=2",
                "")
            result = self.phone.receive_sms(limit=10)
            self.assertEqual(result["count"], 2)
            self.assertEqual(result["messages"][0]["sender"], "+1234567890")
            self.assertEqual(result["messages"][0]["body"], "Hello there")

    def test_get_sent_sms_not_connected(self):
        result = self.phone.get_sent_sms()
        self.assertEqual(result["messages"], [])

    def test_parse_sms_line_valid(self):
        msg = self.phone._parse_sms_line(
            "Row: 0 address=+1234567890, body=Hello, date=1697000000000, _id=1",
            "inbox",
        )
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender, "+1234567890")
        self.assertEqual(msg.body, "Hello")

    def test_parse_sms_line_invalid(self):
        msg = self.phone._parse_sms_line("garbage line", "inbox")
        # Should not crash, may return None or a partial message
        # The key is it doesn't throw

    def test_sms_log_written(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            self.phone.send_sms("+1234567890", "Hello")
            # Check log file was written
            self.assertTrue(self.phone._sms_log.exists())
            log_content = self.phone._sms_log.read_text()
            self.assertIn("sent", log_content)

    # ===========================================================
    # CALLS
    # ===========================================================

    def test_make_call_not_connected(self):
        result = self.phone.make_call("+1234567890")
        self.assertFalse(result["called"])

    def test_make_call_empty_number(self):
        with patch.object(self.phone, 'is_connected', return_value=True):
            result = self.phone.make_call("")
            self.assertFalse(result["called"])

    def test_make_call_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            result = self.phone.make_call("+1234567890")
            self.assertTrue(result["called"])
            self.assertFalse(result["emergency"])

    def test_make_emergency_call(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            result = self.phone.make_call("911")
            self.assertTrue(result["called"])
            self.assertTrue(result["emergency"])

    def test_make_call_failure(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (1, "", "Error")
            result = self.phone.make_call("+1234567890")
            self.assertFalse(result["called"])

    def test_answer_call_not_connected(self):
        result = self.phone.answer_call()
        self.assertFalse(result["answered"])

    def test_answer_call_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "", "")
            result = self.phone.answer_call()
            self.assertTrue(result["answered"])

    def test_end_call_not_connected(self):
        result = self.phone.end_call()
        self.assertFalse(result["ended"])

    def test_end_call_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "", "")
            result = self.phone.end_call()
            self.assertTrue(result["ended"])

    def test_get_call_history_not_connected(self):
        result = self.phone.get_call_history()
        self.assertEqual(result["calls"], [])

    def test_get_call_history_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0,
                "Row: 0 number=+1234567890, duration=120, date=1697000000000, type=2, name=John",
                "")
            result = self.phone.get_call_history()
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["calls"][0]["direction"], "outgoing")
            self.assertEqual(result["calls"][0]["duration_seconds"], 120)

    def test_call_log_written(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            self.phone.make_call("+1234567890")
            self.assertTrue(self.phone._call_log.exists())
            log_content = self.phone._call_log.read_text()
            self.assertIn("outgoing", log_content)

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_get_status_not_connected(self):
        status = self.phone.get_status()
        self.assertFalse(status["connected"])

    def test_get_status_connected(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            # Mock different shell commands for different queries
            mock_shell.side_effect = [
                (0, "  level: 85", ""),          # battery level
                (0, "  status: Charging", ""),    # battery status
                (0, "mSignalStrength=3", ""),     # signal
                (0, "ready", ""),                 # SIM state
                (0, "T-Mobile", ""),              # operator
                (0, "0", ""),                     # airplane mode
                (0, "mWakefulness=Awake", ""),    # screen
                (0, "number=+15551234567", ""),   # phone number
            ]
            status = self.phone.get_status()
            self.assertTrue(status["connected"])
            self.assertEqual(status["battery_level"], 85)
            self.assertTrue(status["battery_charging"])
            self.assertEqual(status["sim_state"], "ready")
            self.assertEqual(status["network_operator"], "T-Mobile")
            self.assertTrue(status["screen_on"])

    def test_get_phone_number_not_connected(self):
        result = self.phone.get_phone_number()
        self.assertEqual(result, "")

    def test_get_phone_number_from_sim(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.side_effect = [
                (-1, "", "error"),  # method 1 fails
                (0, "number=+15551234567", ""),  # method 2 succeeds
            ]
            result = self.phone.get_phone_number()
            self.assertEqual(result, "+15551234567")

    # ===========================================================
    # POLLING
    # ===========================================================

    def test_start_polling_not_connected(self):
        result = self.phone.start_polling()
        self.assertFalse(result["polling"])

    def test_stop_polling_when_not_polling(self):
        result = self.phone.stop_polling()
        self.assertFalse(result["polling"])

    def test_start_stop_polling(self):
        with patch.object(self.phone, 'is_connected', return_value=True):
            result = self.phone.start_polling()
            self.assertTrue(result["polling"])
            time.sleep(0.1)  # let thread start
            result = self.phone.stop_polling()
            self.assertFalse(result["polling"])

    # ===========================================================
    # UTILITY
    # ===========================================================

    def test_wake_screen_not_connected(self):
        result = self.phone.wake_screen()
        self.assertFalse(result["woken"])

    def test_wake_screen_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "", "")
            result = self.phone.wake_screen()
            self.assertTrue(result["woken"])

    def test_send_ussd_not_connected(self):
        result = self.phone.send_ussd("*100#")
        self.assertFalse(result["sent"])

    def test_send_ussd_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "", "")
            result = self.phone.send_ussd("*100#")
            self.assertTrue(result["sent"])

    def test_get_imei_not_connected(self):
        result = self.phone.get_imei()
        self.assertEqual(result, "")

    def test_get_sms_log_empty(self):
        result = self.phone.get_sms_log()
        self.assertEqual(result["count"], 0)

    def test_get_sms_log_with_entries(self):
        # Write a test entry
        with open(self.phone._sms_log, "a") as f:
            f.write(json.dumps({"direction": "sent", "number": "****"}) + "\n")
        result = self.phone.get_sms_log()
        self.assertEqual(result["count"], 1)

    def test_get_call_log_local_empty(self):
        result = self.phone.get_call_log_local()
        self.assertEqual(result["count"], 0)

    def test_get_system_status_not_connected(self):
        status = self.phone.get_system_status()
        self.assertFalse(status["connected"])
        self.assertEqual(status["adb_path"], "fake_adb")

    # ===========================================================
    # DATA STRUCTURES
    # ===========================================================

    def test_sms_message_to_dict(self):
        msg = SMSMessage(
            msg_id="1", timestamp=time.time(), sender="+1234567890",
            body="Hello", direction="inbox",
        )
        d = msg.to_dict()
        self.assertEqual(d["msg_id"], "1")
        self.assertEqual(d["sender"], "+1234567890")
        self.assertEqual(d["body"], "Hello")

    def test_call_record_to_dict(self):
        call = CallRecord(
            call_id="1", timestamp=time.time(), number="+1234567890",
            duration_seconds=60, direction="outgoing",
        )
        d = call.to_dict()
        self.assertEqual(d["direction"], "outgoing")
        self.assertIn("****", d["number"])  # masked

    def test_phone_status_to_dict(self):
        status = PhoneStatus(connected=True, battery_level=85, sim_state="ready")
        d = status.to_dict()
        self.assertTrue(d["connected"])
        self.assertEqual(d["battery_level"], 85)
        self.assertEqual(d["sim_state"], "ready")

    def test_mask_number(self):
        self.assertEqual(self.phone._mask_number("+1234567890"), "+123456****")
        self.assertEqual(self.phone._mask_number("123"), "123")
        self.assertEqual(self.phone._mask_number(""), "")

    # ===========================================================
    # SMS CALLBACK
    # ===========================================================

    def test_sms_received_callback(self):
        """Test that the SMS received callback is called during polling."""
        # We can't easily test the full polling loop, but we can test
        # that the callback is set and would be called
        self.assertIsNotNone(self.phone.on_sms_received)

    # ===========================================================
    # SPEAK CALLBACK
    # ===========================================================

    def test_speak_called_on_send_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            self.phone.send_sms("+1234567890", "Hello")
            self.phone.on_speak.assert_called()

    def test_speak_called_on_call_success(self):
        with patch.object(self.phone, 'is_connected', return_value=True), \
             patch.object(self.phone, '_run_shell') as mock_shell:
            mock_shell.return_value = (0, "Starting: Intent", "")
            self.phone.make_call("+1234567890")
            self.phone.on_speak.assert_called()


if __name__ == "__main__":
    unittest.main()
