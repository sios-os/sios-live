"""Tests for the autonomous scheduler."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.scheduler import (
    AutonomousScheduler,
    ScheduleConfig,
    SchedulerState,
)


class TestScheduleConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = ScheduleConfig()
        self.assertEqual(cfg.check_interval_s, 60.0)
        self.assertEqual(cfg.idle_threshold_s, 300.0)
        self.assertTrue(cfg.enabled)

    def test_custom(self):
        cfg = ScheduleConfig(check_interval_s=1.0, idle_threshold_s=10.0)
        self.assertEqual(cfg.check_interval_s, 1.0)
        self.assertEqual(cfg.idle_threshold_s, 10.0)


class TestSchedulerState(unittest.TestCase):
    def test_to_dict(self):
        state = SchedulerState(last_interaction=100.0)
        d = state.to_dict()
        self.assertEqual(d["last_interaction"], 100.0)
        self.assertFalse(d["running"])

    def test_from_dict(self):
        state = SchedulerState.from_dict({
            "last_interaction": 200.0,
            "last_dream_cycle": 150.0,
            "running": True,
        })
        self.assertEqual(state.last_interaction, 200.0)
        self.assertTrue(state.running)


class TestAutonomousScheduler(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_state_persistence(self):
        scheduler = AutonomousScheduler(self.root)
        scheduler.notify_interaction()
        # Reload
        scheduler2 = AutonomousScheduler(self.root)
        self.assertGreater(scheduler2._state.last_interaction, 0)

    def test_notify_interaction(self):
        scheduler = AutonomousScheduler(self.root)
        before = time.time()
        scheduler.notify_interaction()
        self.assertGreaterEqual(scheduler._state.last_interaction, before)

    def test_trigger_dream_cycle(self):
        called = []
        def on_dream():
            called.append(True)
            return {"result": "ok"}
        scheduler = AutonomousScheduler(
            self.root, on_dream_cycle=on_dream
        )
        result = scheduler.trigger_dream_cycle()
        self.assertEqual(result["result"], "ok")
        self.assertEqual(len(called), 1)
        self.assertGreater(scheduler._state.last_dream_cycle, 0)

    def test_trigger_purge(self):
        called = []
        def on_purge():
            called.append(True)
            return {"archived": 5}
        scheduler = AutonomousScheduler(
            self.root, on_purge=on_purge
        )
        result = scheduler.trigger_purge()
        self.assertEqual(result["archived"], 5)
        self.assertGreater(scheduler._state.last_purge, 0)

    def test_trigger_mission_processing(self):
        called = []
        def on_missions(count):
            called.append(count)
            return {"processed": count}
        scheduler = AutonomousScheduler(
            self.root, on_process_missions=on_missions
        )
        result = scheduler.trigger_mission_processing(5)
        self.assertEqual(result["processed"], 5)
        self.assertEqual(called, [5])

    def test_no_handler(self):
        scheduler = AutonomousScheduler(self.root)
        result = scheduler.trigger_dream_cycle()
        self.assertIn("error", result)

    def test_status(self):
        scheduler = AutonomousScheduler(self.root)
        status = scheduler.get_status()
        self.assertIn("config", status)
        self.assertIn("next_actions", status)
        self.assertFalse(status["running"])

    def test_start_stop(self):
        cfg = ScheduleConfig(
            check_interval_s=0.1,
            idle_threshold_s=0.0,
            dream_cycle_interval_s=0.0,
        )
        called = []
        def on_dream():
            called.append(True)
            return {"ok": True}
        scheduler = AutonomousScheduler(
            self.root, config=cfg, on_dream_cycle=on_dream
        )
        scheduler.start()
        time.sleep(0.5)
        scheduler.stop()
        self.assertGreater(len(called), 0)

    def test_idle_prevents_dream(self):
        """Dream cycle should not trigger when Creator is active."""
        cfg = ScheduleConfig(
            check_interval_s=0.1,
            idle_threshold_s=100.0,  # high threshold
            dream_cycle_interval_s=0.0,
        )
        called = []
        def on_dream():
            called.append(True)
            return {"ok": True}
        scheduler = AutonomousScheduler(
            self.root, config=cfg, on_dream_cycle=on_dream
        )
        scheduler.notify_interaction()  # mark as active
        scheduler.start()
        time.sleep(0.3)
        scheduler.stop()
        self.assertEqual(len(called), 0)  # no dream while active

    def test_compute_next_actions(self):
        scheduler = AutonomousScheduler(self.root)
        actions = scheduler._compute_next_actions(time.time())
        self.assertEqual(len(actions), 11)
        # Should be sorted by next_in_s
        for i in range(len(actions) - 1):
            self.assertLessEqual(
                actions[i]["next_in_s"],
                actions[i + 1]["next_in_s"],
            )

    def test_action_error_handling(self):
        """Scheduler should not crash on action errors."""
        def on_dream():
            raise Exception("test error")
        scheduler = AutonomousScheduler(
            self.root, on_dream_cycle=on_dream
        )
        result = scheduler.trigger_dream_cycle()
        self.assertIn("error", result)
        # State should still be updated
        self.assertGreater(scheduler._state.last_dream_cycle, 0)

    def test_disabled_config(self):
        cfg = ScheduleConfig(enabled=False, check_interval_s=0.1)
        called = []
        def on_dream():
            called.append(True)
            return {"ok": True}
        scheduler = AutonomousScheduler(
            self.root, config=cfg, on_dream_cycle=on_dream
        )
        scheduler.start()
        time.sleep(0.3)
        scheduler.stop()
        self.assertEqual(len(called), 0)


if __name__ == "__main__":
    unittest.main()
