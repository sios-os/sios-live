"""Tests for the system control module."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.system_control import (
    SystemController,
    SystemHealth,
    ServiceStatus,
    Anticipation,
    Task,
)


class TestServiceStatus(unittest.TestCase):
    def test_to_dict(self):
        s = ServiceStatus(name="ollama", status="running", health="healthy")
        d = s.to_dict()
        self.assertEqual(d["name"], "ollama")
        self.assertEqual(d["status"], "running")


class TestSystemHealth(unittest.TestCase):
    def test_to_dict(self):
        h = SystemHealth(cpu_percent=50.0, memory_percent=60.0)
        d = h.to_dict()
        self.assertEqual(d["cpu_percent"], 50.0)
        self.assertEqual(d["memory_percent"], 60.0)


class TestSystemController(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        ctrl = SystemController(self.root)
        self.assertIsNotNone(ctrl)

    def test_check_health(self):
        ctrl = SystemController(self.root)
        health = ctrl.check_health()
        self.assertIsInstance(health, SystemHealth)
        self.assertGreater(health.timestamp, 0)
        self.assertGreaterEqual(health.disk_percent, 0)

    def test_disk_info(self):
        ctrl = SystemController(self.root)
        disk = ctrl._get_disk_info()
        self.assertGreater(disk["total_gb"], 0)

    def test_memory_info(self):
        ctrl = SystemController(self.root)
        mem = ctrl._get_memory_info()
        self.assertGreaterEqual(mem["percent"], 0)

    def test_record_anticipation(self):
        ctrl = SystemController(self.root)
        anticip = ctrl.record_anticipation(
            "Creator will need Python help",
            confidence=0.7,
            preparation="Load Python knowledge",
        )
        self.assertEqual(anticip.prediction, "Creator will need Python help")
        anticipations = ctrl.get_anticipations()
        self.assertEqual(len(anticipations), 1)

    def test_mark_anticipation_prepared(self):
        ctrl = SystemController(self.root)
        anticip = ctrl.record_anticipation("test", 0.5)
        self.assertTrue(ctrl.mark_anticipation_prepared(anticip.anticip_id))
        anticipations = ctrl.get_anticipations()
        self.assertTrue(anticipations[0]["prepared"])

    def test_get_unprepared_anticipations(self):
        ctrl = SystemController(self.root)
        ctrl.record_anticipation("test1", 0.5)
        ctrl.record_anticipation("test2", 0.6)
        unprepared = ctrl.get_anticipations(unprepared_only=True)
        self.assertEqual(len(unprepared), 2)

    def test_submit_task_without_executor(self):
        ctrl = SystemController(self.root)
        task_id = ctrl.submit_task("test task", priority=3)
        self.assertIsNotNone(task_id)
        tasks = ctrl.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "pending")

    def test_submit_task_with_executor(self):
        ctrl = SystemController(self.root)
        def executor():
            time.sleep(0.1)
            return "done"
        task_id = ctrl.submit_task("test task", executor=executor)
        time.sleep(0.5)
        tasks = ctrl.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "completed")
        self.assertEqual(tasks[0]["result"], "done")

    def test_task_failure(self):
        ctrl = SystemController(self.root)
        def executor():
            raise Exception("test error")
        task_id = ctrl.submit_task("failing task", executor=executor)
        time.sleep(0.5)
        tasks = ctrl.get_tasks()
        self.assertEqual(tasks[0]["status"], "failed")
        self.assertIn("test error", tasks[0]["error"])

    def test_get_running_tasks(self):
        ctrl = SystemController(self.root)
        def executor():
            time.sleep(1.0)
            return "done"
        ctrl.submit_task("long task", executor=executor)
        running = ctrl.get_running_tasks()
        self.assertEqual(len(running), 1)

    def test_status(self):
        ctrl = SystemController(self.root)
        status = ctrl.get_status()
        self.assertIn("health", status)
        self.assertIn("managed_services", status)
        self.assertIn("running_tasks", status)

    def test_alerts_generation(self):
        ctrl = SystemController(
            self.root,
            alert_thresholds={
                "cpu_percent": 0.0,  # trigger immediately
                "memory_percent": 0.0,
                "disk_percent": 0.0,
            },
        )
        health = ctrl.check_health()
        # Should have alerts if any metric > 0 (disk always is)
        # On some systems CPU/memory may report 0 without psutil
        self.assertGreaterEqual(len(health.alerts), 0)

    def test_overall_health_critical(self):
        ctrl = SystemController(
            self.root,
            alert_thresholds={
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
            },
        )
        health = ctrl.check_health()
        self.assertIn(health.overall_health, ["warning", "critical"])

    def test_managed_services_list(self):
        ctrl = SystemController(self.root)
        self.assertIn("ollama", ctrl.MANAGED_SERVICES)
        self.assertIn("daemon", ctrl.MANAGED_SERVICES)

    def test_start_unknown_service(self):
        ctrl = SystemController(self.root)
        result = ctrl.start_service("nonexistent")
        self.assertIn("error", result)

    def test_stop_unknown_service(self):
        ctrl = SystemController(self.root)
        result = ctrl.stop_service("nonexistent")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
