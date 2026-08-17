"""Tests for the ANUBIS sleep protocol — goodnight, wake, good morning."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.sleep_protocol import SleepProtocol, SleepState


class TestSleepProtocol(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.smarthome = MagicMock()
        self.smarthome.get_devices = MagicMock(return_value=[
            {"device_id": "lock1", "device_type": "lock", "location": "front"},
            {"device_id": "lock2", "device_type": "lock", "location": "back"},
            {"device_id": "light1", "device_type": "light", "location": "bedroom"},
        ])
        self.smarthome.lock = MagicMock(return_value={"status": "locked"})
        self.sensory = MagicMock()
        self.sensory.set_mode = MagicMock(return_value=True)
        self.sensory.speak = MagicMock(return_value="req-1")
        self.notifications = MagicMock()
        self.notifications.notify = MagicMock(return_value=MagicMock(notif_id="n1"))
        self.notifications.alert = MagicMock(return_value=MagicMock(notif_id="n1"))
        self.calendar = MagicMock()
        self.calendar.get_today_events = MagicMock(return_value=[
            {"title": "Doctor appointment", "start_time": time.time() + 3600},
        ])
        self.mission_queue = MagicMock()
        self.mission_queue.stats = MagicMock(return_value={
            "total": 10, "by_status": {"completed": 7, "failed": 1, "pending": 2},
        })
        self.mission_queue.all_missions = MagicMock(return_value=[
            MagicMock(mission_id="m1", skill_name="test_skill", task="do thing", status="pending"),
            MagicMock(mission_id="m2", skill_name="test_skill2", task="do other", status="pending"),
        ])
        self.skill_library = MagicMock()
        self.skill_library.names = MagicMock(return_value=["skill_a", "skill_b", "skill_c"])
        self.court = MagicMock()
        self.court.stats = MagicMock(return_value={
            "total_reviews": 5, "creator_approved": 3, "on_probation": 1,
            "verdict_distribution": {"APPROVED": 3, "PROBATION": 1, "REJECTED": 1},
        })
        self.court.reviews = MagicMock(return_value=[
            MagicMock(review_id="r1", description="Skill v2.0", artifact_hash="abc",
                      creator_approved=False, verdict=1),
        ])
        self.weather = MagicMock()
        self.weather.get_forecast = MagicMock(return_value=[
            {"temperature": 72, "condition": "sunny"},
        ])
        self.weather.get_alerts = MagicMock(return_value=[])

        self.protocol = SleepProtocol(
            self.root,
            smarthome=self.smarthome,
            sensory=self.sensory,
            notifications=self.notifications,
            calendar=self.calendar,
            mission_queue=self.mission_queue,
            skill_library=self.skill_library,
            court=self.court,
            weather=self.weather,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_initial_status_awake(self):
        status = self.protocol.get_status()
        self.assertEqual(status["state"], "awake")
        self.assertIsNone(status["session"])

    def test_initial_state(self):
        self.assertEqual(self.protocol.state, SleepState.AWAKE)
        self.assertFalse(self.protocol.is_sleeping)
        self.assertFalse(self.protocol.is_waking)

    # ===========================================================
    # GOODNIGHT
    # ===========================================================

    def test_goodnight_locks_doors(self):
        result = self.protocol.goodnight()
        self.assertEqual(result["state"], "sleeping")
        self.assertTrue(result["doors_locked"])
        # Should have locked both locks
        self.assertEqual(self.smarthome.lock.call_count, 2)

    def test_goodnight_sets_sleep_mode(self):
        self.protocol.goodnight()
        self.sensory.set_mode.assert_called_with("sleep")

    def test_goodnight_speaks(self):
        self.protocol.goodnight()
        self.sensory.speak.assert_called()

    def test_goodnight_sends_notification(self):
        self.protocol.goodnight()
        self.notifications.notify.assert_called()

    def test_goodnight_creates_session(self):
        self.protocol.goodnight()
        self.assertTrue(self.protocol.is_sleeping)
        self.assertIsNotNone(self.protocol.get_status()["session"])

    def test_goodnight_when_already_sleeping(self):
        self.protocol.goodnight()
        result = self.protocol.goodnight()
        self.assertIn("error", result)

    def test_goodnight_no_smarthome(self):
        protocol = SleepProtocol(self.root, sensory=self.sensory)
        result = protocol.goodnight()
        self.assertEqual(result["state"], "sleeping")
        self.assertFalse(result["doors_locked"])

    # ===========================================================
    # WAKE
    # ===========================================================

    def test_wake_sounds_alarm(self):
        self.protocol.goodnight()
        # Reset mock to check wake calls
        self.sensory.speak.reset_mock()
        self.notifications.alert.reset_mock()
        result = self.protocol.wake()
        self.assertEqual(result["state"], "waking")
        self.sensory.speak.assert_called()
        self.notifications.alert.assert_called()

    def test_wake_sets_ambient_mode(self):
        self.protocol.goodnight()
        self.sensory.set_mode.reset_mock()
        self.protocol.wake()
        # Should set to ambient so alarm is heard
        self.sensory.set_mode.assert_called_with("ambient")

    def test_wake_turns_on_bedroom_lights(self):
        self.protocol.goodnight()
        self.smarthome.turn_on.reset_mock()
        self.protocol.wake()
        self.smarthome.turn_on.assert_called_with("light1")

    def test_wake_when_already_waking(self):
        self.protocol.goodnight()
        self.protocol.wake()
        result = self.protocol.wake()
        self.assertIn("error", result)

    def test_wake_without_session(self):
        result = self.protocol.wake()
        self.assertEqual(result["state"], "waking")

    # ===========================================================
    # ACCELEROMETER — wake detection
    # ===========================================================

    def test_accel_during_sleep_tracks_restlessness(self):
        self.protocol.goodnight()
        # Large movement during sleep
        result = self.protocol.process_accelerometer(5, 5, 5)  # magnitude ~8.66
        self.assertTrue(result.get("restlessness"))
        status = self.protocol.get_status()
        self.assertEqual(status["session"]["restlessness_events"], 1)

    def test_accel_during_sleep_small_movement_no_restlessness(self):
        self.protocol.goodnight()
        result = self.protocol.process_accelerometer(0.1, 0.1, 0.1)  # tiny
        self.assertNotIn("restlessness", result)

    def test_accel_during_wake_confirms_awake(self):
        self.protocol.goodnight()
        self.protocol.wake()
        # Significant movement = awake
        result = self.protocol.process_accelerometer(2, 2, 2)  # magnitude ~3.46
        self.assertTrue(result.get("confirmed_awake"))
        self.assertEqual(self.protocol.state, SleepState.AWAKE)

    def test_accel_during_wake_small_movement_no_confirm(self):
        self.protocol.goodnight()
        self.protocol.wake()
        result = self.protocol.process_accelerometer(0.1, 0.1, 0.1)
        self.assertNotIn("confirmed_awake", result)
        self.assertTrue(self.protocol.is_waking)

    # ===========================================================
    # HEART RATE
    # ===========================================================

    def test_heart_rate_normal_during_sleep(self):
        self.protocol.goodnight()
        result = self.protocol.process_heart_rate(65)
        self.assertEqual(result["heart_rate"], 65)
        self.assertNotIn("anomaly", result)

    def test_heart_rate_anomaly_low(self):
        self.protocol.goodnight()
        result = self.protocol.process_heart_rate(35)
        self.assertTrue(result.get("anomaly"))

    def test_heart_rate_anomaly_high(self):
        self.protocol.goodnight()
        result = self.protocol.process_heart_rate(130)
        self.assertTrue(result.get("anomaly"))

    def test_heart_rate_when_awake_no_tracking(self):
        result = self.protocol.process_heart_rate(65)
        self.assertEqual(result["heart_rate"], 65)
        self.assertNotIn("anomaly", result)

    # ===========================================================
    # GOOD MORNING
    # ===========================================================

    def test_good_morning_after_sleep(self):
        self.protocol.goodnight()
        time.sleep(0.01)  # ensure duration > 0
        result = self.protocol.good_morning()
        self.assertEqual(result["state"], "awake")
        self.assertIn("briefing", result)
        self.assertIn("briefing_text", result)

    def test_good_morning_restores_ambient_mode(self):
        self.protocol.goodnight()
        self.sensory.set_mode.reset_mock()
        self.protocol.good_morning()
        self.sensory.set_mode.assert_called_with("ambient")

    def test_good_morning_includes_calendar(self):
        self.protocol.goodnight()
        result = self.protocol.good_morning()
        self.assertEqual(len(result["briefing"]["calendar_today"]), 1)
        self.assertIn("Doctor appointment", result["briefing_text"])

    def test_good_morning_includes_mission_stats(self):
        self.protocol.goodnight()
        result = self.protocol.good_morning()
        self.assertEqual(result["briefing"]["mission_stats"]["total"], 10)
        self.assertIn("completed 7", result["briefing_text"])

    def test_good_morning_includes_skills_count(self):
        self.protocol.goodnight()
        result = self.protocol.good_morning()
        self.assertEqual(result["briefing"]["skills_promoted"], 3)

    def test_good_morning_includes_pending_approvals(self):
        self.protocol.goodnight()
        result = self.protocol.good_morning()
        self.assertEqual(len(result["briefing"]["pending_approvals"]), 1)
        self.assertIn("approval", result["briefing_text"])

    def test_good_morning_includes_weather(self):
        self.protocol.goodnight()
        result = self.protocol.good_morning()
        self.assertEqual(len(result["briefing"]["weather_forecast"]), 1)

    def test_good_morning_includes_sleep_stats(self):
        self.protocol.goodnight()
        # Add some restlessness
        self.protocol.process_accelerometer(5, 5, 5)
        result = self.protocol.good_morning()
        self.assertIn("sleep_stats", result["briefing"])
        self.assertEqual(result["briefing"]["sleep_stats"]["restlessness_events"], 1)
        self.assertIn("slept", result["briefing_text"])

    def test_good_morning_without_session(self):
        result = self.protocol.good_morning()
        self.assertEqual(result["state"], "awake")
        self.assertIn("briefing", result)

    def test_good_morning_clears_session(self):
        self.protocol.goodnight()
        self.protocol.good_morning()
        self.assertEqual(self.protocol.state, SleepState.AWAKE)
        self.assertIsNone(self.protocol.get_status()["session"])

    def test_good_morning_speaks_briefing(self):
        self.protocol.goodnight()
        self.sensory.speak.reset_mock()
        self.protocol.good_morning()
        self.sensory.speak.assert_called()
        # The briefing text should be spoken
        spoken_text = self.sensory.speak.call_args[0][0]
        self.assertIn("Good morning", spoken_text)

    # ===========================================================
    # CANCEL
    # ===========================================================

    def test_cancel_sleeping(self):
        self.protocol.goodnight()
        result = self.protocol.cancel()
        self.assertEqual(result["state"], "awake")
        self.assertEqual(self.protocol.state, SleepState.AWAKE)

    def test_cancel_restores_ambient(self):
        self.protocol.goodnight()
        self.sensory.set_mode.reset_mock()
        self.protocol.cancel()
        self.sensory.set_mode.assert_called_with("ambient")

    def test_cancel_when_awake(self):
        result = self.protocol.cancel()
        self.assertEqual(result["state"], "awake")

    # ===========================================================
    # HISTORY
    # ===========================================================

    def test_history_empty(self):
        self.assertEqual(self.protocol.get_history(), [])

    def test_history_after_session(self):
        self.protocol.goodnight()
        self.protocol.good_morning()
        history = self.protocol.get_history()
        self.assertEqual(len(history), 1)
        self.assertIn("session_id", history[0])

    def test_history_limit(self):
        for i in range(5):
            self.protocol.goodnight()
            self.protocol.good_morning()
        history = self.protocol.get_history(limit=3)
        self.assertEqual(len(history), 3)

    # ===========================================================
    # RECORD ALERT
    # ===========================================================

    def test_record_alert_during_sleep(self):
        self.protocol.goodnight()
        self.protocol.record_alert("intrusion", "Unknown person detected at front door")
        status = self.protocol.get_status()
        self.assertEqual(len(status["session"]["alerts_during_sleep"]), 1)

    def test_record_alert_when_awake(self):
        # Should not crash, just do nothing
        self.protocol.record_alert("test", "test alert")
        self.assertIsNone(self.protocol.get_status()["session"])

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def test_session_persists_across_restart(self):
        self.protocol.goodnight()
        # Create new protocol instance — should load current session
        protocol2 = SleepProtocol(
            self.root,
            smarthome=self.smarthome,
            sensory=self.sensory,
        )
        self.assertTrue(protocol2.is_sleeping)

    def test_session_cleared_after_good_morning(self):
        self.protocol.goodnight()
        self.protocol.good_morning()
        # New instance should not have a current session
        protocol2 = SleepProtocol(self.root)
        self.assertIsNone(protocol2.get_status()["session"])


if __name__ == "__main__":
    unittest.main()
