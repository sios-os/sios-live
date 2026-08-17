"""Tests for smart home control."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.smarthome import (
    SmartHome, SmartDevice, AutomationRule,
    DEV_LIGHT, DEV_LOCK, DEV_THERMOSTAT, DEV_SWITCH, DEV_GARAGE, DEV_BLINDS, DEV_SENSOR,
    PROTO_HOMEASSISTANT, PROTO_HTTP,
    STATE_ON, STATE_OFF, STATE_LOCKED, STATE_UNLOCKED, STATE_UNKNOWN,
)


class TestSmartDevice(unittest.TestCase):
    def test_to_dict(self):
        d = SmartDevice(device_id="d1", name="Living Room Light", device_type=DEV_LIGHT)
        data = d.to_dict()
        self.assertEqual(data["device_id"], "d1")
        self.assertEqual(data["name"], "Living Room Light")
        self.assertEqual(data["device_type"], DEV_LIGHT)


class TestSmartHome(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.home = SmartHome(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_light(self):
        light = self.home.add_device(
            "Living Room Light", DEV_LIGHT, PROTO_HTTP,
            entity_id="http://192.168.1.50/light",
            location="living room",
        )
        self.assertEqual(light.device_type, DEV_LIGHT)
        self.assertFalse(light.requires_approval)

    def test_add_lock_requires_approval(self):
        lock = self.home.add_device(
            "Front Door Lock", DEV_LOCK, PROTO_HTTP,
            entity_id="http://192.168.1.50/lock",
            location="front door",
        )
        self.assertTrue(lock.requires_approval)  # locks require approval by default

    def test_add_garage_requires_approval(self):
        garage = self.home.add_device(
            "Garage Door", DEV_GARAGE, PROTO_HTTP,
            entity_id="http://192.168.1.50/garage",
        )
        self.assertTrue(garage.requires_approval)

    def test_add_thermostat(self):
        thermo = self.home.add_device(
            "Main Thermostat", DEV_THERMOSTAT, PROTO_HTTP,
            entity_id="http://192.168.1.50/thermo",
        )
        self.assertEqual(thermo.device_type, DEV_THERMOSTAT)

    def test_remove_device(self):
        dev = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://test")
        self.assertTrue(self.home.remove_device(dev.device_id))
        self.assertEqual(len(self.home.get_devices()), 0)

    def test_get_devices_by_type(self):
        self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://1")
        self.home.add_device("L2", DEV_LIGHT, PROTO_HTTP, "http://2")
        self.home.add_device("S1", DEV_SWITCH, PROTO_HTTP, "http://3")
        lights = self.home.get_devices_by_type(DEV_LIGHT)
        self.assertEqual(len(lights), 2)

    def test_get_devices_by_location(self):
        self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://1", location="kitchen")
        self.home.add_device("L2", DEV_LIGHT, PROTO_HTTP, "http://2", location="living room")
        kitchen = self.home.get_devices_by_location("kitchen")
        self.assertEqual(len(kitchen), 1)

    def test_devices_persist(self):
        self.home.add_device("Test Light", DEV_LIGHT, PROTO_HTTP, "http://test", location="bedroom")
        home2 = SmartHome(self.root)
        devices = home2.get_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "Test Light")

    def test_turn_on_no_protocol(self):
        # Device with no working protocol → command fails gracefully
        dev = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        result = self.home.turn_on(dev.device_id)
        self.assertFalse(result["success"])

    def test_turn_on_nonexistent(self):
        result = self.home.turn_on("nonexistent")
        self.assertFalse(result["success"])

    def test_lock_denied_without_approval(self):
        home = SmartHome(self.root, on_command=lambda d, c: False)
        lock = home.add_device("Front Door", DEV_LOCK, PROTO_HTTP, "http://test")
        result = home.lock(lock.device_id)
        self.assertFalse(result["success"])
        self.assertIn("approval", result["error"])

    def test_lock_approved(self):
        home = SmartHome(self.root, on_command=lambda d, c: True)
        lock = home.add_device("Front Door", DEV_LOCK, PROTO_HTTP, "http://192.168.1.99:99999")
        result = home.lock(lock.device_id)
        # Approved but command fails (no real device)
        self.assertFalse(result["success"])
        # But it should not be denied — it was approved
        self.assertNotIn("approval", result.get("error", ""))

    def test_lock_no_callback(self):
        # No approval callback → command proceeds (but fails on no device)
        lock = self.home.add_device("Front Door", DEV_LOCK, PROTO_HTTP, "http://192.168.1.99:99999")
        result = self.home.lock(lock.device_id)
        self.assertFalse(result["success"])

    def test_set_brightness_invalid(self):
        light = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://test")
        result = self.home.set_brightness(light.device_id, 300)
        self.assertFalse(result["success"])

    def test_set_brightness_valid(self):
        light = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        result = self.home.set_brightness(light.device_id, 128)
        # Command fails (no real device) but brightness is valid
        self.assertFalse(result["success"])

    def test_automation_rule(self):
        light = self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        rule = self.home.add_rule(
            "Lock up at night", "time_22:00",
            [{"device_id": light.device_id, "command": "turn_off"}],
        )
        self.assertTrue(rule.enabled)
        rules = self.home.get_rules()
        self.assertEqual(len(rules), 1)

    def test_remove_rule(self):
        rule = self.home.add_rule("Test", "trigger", [])
        self.assertTrue(self.home.remove_rule(rule.rule_id))
        self.assertEqual(len(self.home.get_rules()), 0)

    def test_trigger_rule(self):
        light = self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        rule = self.home.add_rule(
            "Test Rule", "test_trigger",
            [{"device_id": light.device_id, "command": "turn_off"}],
        )
        result = self.home.trigger_rule(rule.rule_id)
        self.assertTrue(result["success"])
        self.assertEqual(rule.trigger_count, 1)

    def test_check_triggers(self):
        light = self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        self.home.add_rule("R1", "creator_left",
                           [{"device_id": light.device_id, "command": "turn_off"}])
        self.home.add_rule("R2", "creator_left",
                           [{"device_id": light.device_id, "command": "turn_on"}])
        results = self.home.check_triggers("creator_left")
        self.assertEqual(len(results), 2)

    def test_scene_away(self):
        light = self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        lock = self.home.add_device("Lock1", DEV_LOCK, PROTO_HTTP, "http://192.168.1.99:99999")
        result = self.home.activate_scene("away")
        self.assertTrue(result["success"])
        self.assertEqual(result["scene"], "away")

    def test_scene_unknown(self):
        result = self.home.activate_scene("nonexistent_scene")
        self.assertFalse(result["success"])

    def test_scene_night(self):
        light = self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        result = self.home.activate_scene("night")
        self.assertTrue(result["success"])

    def test_get_status(self):
        self.home.add_device("L1", DEV_LIGHT, PROTO_HTTP, "http://1")
        self.home.add_device("Lock1", DEV_LOCK, PROTO_HTTP, "http://2")
        self.home.add_device("Thermo1", DEV_THERMOSTAT, PROTO_HTTP, "http://3")
        status = self.home.get_status()
        self.assertEqual(status["total_devices"], 3)
        self.assertEqual(status["lights"], 1)
        self.assertEqual(status["locks"], 1)
        self.assertEqual(status["thermostats"], 1)

    def test_sync_states_no_ha(self):
        result = self.home.sync_states()
        self.assertFalse(result["success"])

    def test_command_history(self):
        dev = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        self.home.turn_on(dev.device_id)
        # Check history file exists
        self.assertTrue(self.home._history_file.exists())

    def test_toggle(self):
        dev = self.home.add_device("Test", DEV_LIGHT, PROTO_HTTP, "http://192.168.1.99:99999")
        dev.state = STATE_OFF
        result = self.home.toggle(dev.device_id)
        # Fails (no real device) but shouldn't crash
        self.assertIn("success", result)

    def test_rules_persist(self):
        self.home.add_rule("Test Rule", "trigger", [{"device_id": "x", "command": "off"}])
        home2 = SmartHome(self.root)
        rules = home2.get_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "Test Rule")


if __name__ == "__main__":
    unittest.main()
