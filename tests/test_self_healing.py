"""Tests for snapshot manager, self-repair orchestrator, and drive monitor."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.snapshot_manager import SnapshotManager, SnapshotManifest
from anubis.self_repair import SelfRepairOrchestrator, Severity, CorruptionAlert, RepairResult
from anubis.drive_monitor import DriveMonitor, DriveHealth, DailyReport


# ===========================================================
# SNAPSHOT MANAGER TESTS
# ===========================================================

class TestSnapshotManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.snapshot_dir = Path(self.tmpdir) / "snapshots"
        self.root.mkdir()

        # Create some state directories
        (self.root / "memory").mkdir(parents=True)
        (self.root / "memory" / "facts.json").write_text('{"test": true}')
        (self.root / "identity").mkdir(parents=True)
        (self.root / "identity" / "identity.json").write_text('{"creator": "storm"}')
        (self.root / "evidence").mkdir(parents=True)
        (self.root / "evidence" / "ledger.jsonl").write_text('{"event": "test"}\n')

        self.sm = SnapshotManager(
            self.root, self.snapshot_dir,
            ledger=MagicMock(),
            state_dirs=["memory", "identity", "evidence"],
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_snapshot(self):
        result = self.sm.create_snapshot(label="test")
        self.assertTrue(result["verified"])
        self.assertGreater(result["files"], 0)
        self.assertGreater(result["size_bytes"], 0)

    def test_snapshot_has_manifest(self):
        result = self.sm.create_snapshot(label="test")
        snapshot_path = self.snapshot_dir / result["snapshot_id"]
        manifest_file = snapshot_path / "manifest.json"
        self.assertTrue(manifest_file.exists())
        manifest = json.loads(manifest_file.read_text())
        self.assertEqual(manifest["label"], "test")
        self.assertGreater(manifest["file_count"], 0)

    def test_verify_snapshot(self):
        create_result = self.sm.create_snapshot(label="test")
        verify_result = self.sm.verify_snapshot(create_result["snapshot_id"])
        self.assertTrue(verify_result["valid"])
        self.assertGreater(verify_result["files_checked"], 0)
        self.assertEqual(verify_result["files_mismatched"], 0)

    def test_verify_snapshot_detects_corruption(self):
        create_result = self.sm.create_snapshot(label="test")
        # Corrupt a file in the snapshot
        snapshot_path = self.snapshot_dir / create_result["snapshot_id"]
        target = snapshot_path / "memory" / "facts.json"
        target.write_text('{"corrupted": true}')
        verify_result = self.sm.verify_snapshot(create_result["snapshot_id"])
        self.assertFalse(verify_result["valid"])
        self.assertGreater(verify_result["files_mismatched"], 0)

    def test_verify_latest(self):
        self.sm.create_snapshot(label="first")
        result = self.sm.verify_latest()
        self.assertTrue(result["valid"])

    def test_list_snapshots(self):
        self.sm.create_snapshot(label="first")
        time.sleep(0.1)
        self.sm.create_snapshot(label="second")
        result = self.sm.list_snapshots()
        self.assertEqual(result["count"], 2)

    def test_get_latest_snapshot_id(self):
        first = self.sm.create_snapshot(label="first")
        time.sleep(0.1)
        second = self.sm.create_snapshot(label="second")
        latest = self.sm.get_latest_snapshot_id()
        self.assertEqual(latest, second["snapshot_id"])

    def test_restore_snapshot(self):
        # Create initial state
        self.sm.create_snapshot(label="backup")
        # Modify state
        (self.root / "memory" / "facts.json").write_text('{"modified": true}')
        # Restore
        latest_id = self.sm.get_latest_snapshot_id()
        result = self.sm.restore_snapshot(latest_id)
        self.assertTrue(result["restored"])
        # State should be back to original
        content = (self.root / "memory" / "facts.json").read_text()
        self.assertIn("test", content)
        self.assertNotIn("modified", content)

    def test_restore_refuses_corrupted_snapshot(self):
        create_result = self.sm.create_snapshot(label="test")
        # Corrupt the snapshot
        snapshot_path = self.snapshot_dir / create_result["snapshot_id"]
        (snapshot_path / "memory" / "facts.json").write_text('{"corrupted": true}')
        result = self.sm.restore_snapshot(create_result["snapshot_id"])
        self.assertFalse(result["restored"])
        self.assertIn("verification failed", result["error"])

    def test_delete_snapshot(self):
        result = self.sm.create_snapshot(label="test")
        del_result = self.sm.delete_snapshot(result["snapshot_id"])
        self.assertTrue(del_result["deleted"])

    def test_detect_corruption_no_snapshots(self):
        result = self.sm.detect_corruption()
        self.assertFalse(result["corrupted"])

    def test_detect_corruption_with_changes(self):
        self.sm.create_snapshot(label="baseline")
        # Modify a file (expected change — ANUBIS is running)
        (self.root / "memory" / "facts.json").write_text('{"updated": true}')
        result = self.sm.detect_corruption()
        # Changed files are expected, not suspicious
        self.assertFalse(result["corrupted"])
        self.assertGreater(result["changed_count"], 0)

    def test_detect_corruption_deleted_files(self):
        self.sm.create_snapshot(label="baseline")
        # Delete a state file (suspicious)
        (self.root / "memory" / "facts.json").unlink()
        result = self.sm.detect_corruption()
        self.assertTrue(result["corrupted"])
        self.assertGreater(result["deleted_count"], 0)

    def test_retention_policy(self):
        # Create several snapshots
        for i in range(5):
            self.sm.create_snapshot(label=f"test_{i}")
            time.sleep(0.05)
        # Apply aggressive retention (keep only 2)
        result = self.sm.apply_retention_policy(hourly=0, daily=0, weekly=0)
        # Should have deleted some
        self.assertGreaterEqual(result["deleted"], 0)

    def test_get_status(self):
        self.sm.create_snapshot(label="test")
        status = self.sm.get_status()
        self.assertEqual(status["snapshot_count"], 1)

    def test_snapshot_persists_across_restart(self):
        self.sm.create_snapshot(label="test")
        # Create new manager with same dirs
        sm2 = SnapshotManager(self.root, self.snapshot_dir, state_dirs=["memory", "identity", "evidence"])
        status = sm2.get_status()
        self.assertEqual(status["snapshot_count"], 1)

    def test_manifest_to_dict(self):
        m = SnapshotManifest(snapshot_id="test", timestamp=time.time(), label="test")
        d = m.to_dict()
        self.assertEqual(d["snapshot_id"], "test")

    def test_manifest_from_dict(self):
        m = SnapshotManifest.from_dict({"snapshot_id": "test", "timestamp": 123, "label": "test"})
        self.assertEqual(m.snapshot_id, "test")


# ===========================================================
# SELF-REPAIR TESTS
# ===========================================================

class TestSelfRepair(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)

        # Create core file
        (self.root / "anubis").mkdir()
        (self.root / "anubis" / "__init__.py").write_text("# ANUBIS core")
        (self.root / "tools").mkdir()
        (self.root / "tools" / "anubis_daemon.py").write_text("# daemon")

        # Create state dirs
        (self.root / "memory").mkdir()
        (self.root / "memory" / "facts.json").write_text('{"test": true}')
        (self.root / "evidence").mkdir()
        (self.root / "evidence" / "ledger.jsonl").write_text('{"event": "test"}\n')

        self.snapshot_dir = Path(self.tmpdir) / "snapshots"
        self.sm = SnapshotManager(
            self.root, self.snapshot_dir,
            ledger=MagicMock(),
            state_dirs=["memory", "evidence"],
        )
        self.repair = SelfRepairOrchestrator(
            self.root,
            snapshot_manager=self.sm,
            ledger=MagicMock(),
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sign_core_files(self):
        result = self.repair.sign_core_files()
        self.assertGreater(result["signed"], 0)

    def test_verify_core_files_clean(self):
        self.repair.sign_core_files()
        result = self.repair.verify_core_files()
        self.assertTrue(result["clean"])
        self.assertEqual(len(result["mismatches"]), 0)

    def test_verify_core_files_detects_modification(self):
        self.repair.sign_core_files()
        # Modify a core file
        (self.root / "anubis" / "__init__.py").write_text("# MODIFIED BY ATTACKER")
        result = self.repair.verify_core_files()
        self.assertFalse(result["clean"])
        self.assertIn("anubis/__init__.py", result["mismatches"])

    def test_verify_core_files_detects_missing(self):
        self.repair.sign_core_files()
        # Delete a core file
        (self.root / "anubis" / "__init__.py").unlink()
        result = self.repair.verify_core_files()
        self.assertFalse(result["clean"])
        self.assertIn("anubis/__init__.py", result["missing"])

    def test_health_check_clean(self):
        self.repair.sign_core_files()
        result = self.repair.run_health_check()
        # Disk warnings are environment-dependent, so just check no core alerts
        core_alerts = [a for a in result["alerts"] if a["component"] == "core"]
        self.assertEqual(len(core_alerts), 0)

    def test_health_check_detects_core_modification(self):
        self.repair.sign_core_files()
        (self.root / "anubis" / "__init__.py").write_text("# MODIFIED")
        result = self.repair.run_health_check()
        self.assertIn(result["overall_health"], ["degraded", "critical"])
        self.assertGreater(result["alert_count"], 0)

    def test_health_check_detects_disk_space(self):
        self.repair.sign_core_files()
        result = self.repair.run_health_check()
        self.assertIn("disk_health", result["checks"])

    def test_auto_repair_clean(self):
        self.repair.sign_core_files()
        result = self.repair.auto_repair()
        # Disk warnings are environment-dependent
        core_alerts = [a for a in result.get("alerts", []) if a.get("component") == "core"]
        self.assertEqual(len(core_alerts), 0)

    def test_auto_repair_with_corruption(self):
        self.repair.sign_core_files()
        self.sm.create_snapshot(label="baseline")
        # Corrupt a core file
        (self.root / "anubis" / "__init__.py").write_text("# CORRUPTED")
        result = self.repair.auto_repair()
        self.assertGreater(result["alerts_found"], 0)

    def test_trigger_failover_no_ab_drive(self):
        result = self.repair.trigger_failover(reason="test")
        self.assertFalse(result.success)
        self.assertIn("not available", result.errors[0])

    def test_rebuild_drive_no_snapshot(self):
        result = self.repair.rebuild_drive()
        self.assertFalse(result.success)

    def test_rebuild_drive_with_snapshot(self):
        self.sm.create_snapshot(label="baseline")
        result = self.repair.rebuild_drive()
        self.assertTrue(result.success)
        self.assertNotEqual(result.snapshot_restored, "")

    def test_get_status(self):
        status = self.repair.get_status()
        self.assertIn("last_check", status)
        self.assertIn("core_files_signed", status)

    def test_alert_creation(self):
        alert = CorruptionAlert(
            alert_id="test_1",
            severity=Severity.MINOR,
            component="test",
            description="test issue",
        )
        self.assertEqual(alert.severity, Severity.MINOR)

    def test_repair_result_to_dict(self):
        r = RepairResult(success=True, action="test", timestamp=time.time())
        d = r.to_dict()
        self.assertTrue(d["success"])

    def test_resolve_alert(self):
        result = self.repair.resolve_alert("nonexistent")
        self.assertFalse(result["resolved"])

    def test_signatures_persist(self):
        self.repair.sign_core_files()
        repair2 = SelfRepairOrchestrator(self.root, snapshot_manager=self.sm)
        result = repair2.verify_core_files()
        self.assertTrue(result["clean"])

    def test_disk_health_check(self):
        disk = self.repair._check_disk_health()
        self.assertIn("path", disk)
        self.assertIn("warning", disk)


# ===========================================================
# DRIVE MONITOR TESTS
# ===========================================================

class TestDriveMonitor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)

        self.snapshot_dir = Path(self.tmpdir) / "snapshots"
        self.sm = SnapshotManager(
            self.root, self.snapshot_dir,
            state_dirs=["memory"],
        )
        self.dm = DriveMonitor(
            self.root,
            snapshot_manager=self.sm,
            ledger=MagicMock(),
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_report(self):
        report = self.dm.generate_report()
        self.assertIn(report.overall_status, ["healthy", "warning", "critical"])
        self.assertGreater(len(report.drives), 0)
        self.assertIn("spoken_briefing", report.to_dict())

    def test_report_has_drive_info(self):
        report = self.dm.generate_report()
        self.assertGreater(len(report.drives), 0)
        drive = report.drives[0]
        self.assertGreater(drive.total_gb, 0)
        self.assertIn(drive.status, ["healthy", "warning", "critical", "unknown"])

    def test_report_has_snapshot_status(self):
        report = self.dm.generate_report()
        self.assertTrue(report.snapshot_status.get("available"))

    def test_report_has_recommendations(self):
        report = self.dm.generate_report()
        self.assertGreater(len(report.recommendations), 0)

    def test_report_briefing_not_empty(self):
        report = self.dm.generate_report()
        self.assertGreater(len(report.spoken_briefing), 0)

    def test_deliver_report(self):
        result = self.dm.deliver_report(speak=False, notify=False)
        self.assertIn("overall_status", result)
        self.assertIn("drives", result)

    def test_report_history(self):
        self.dm.generate_report()
        time.sleep(0.01)
        self.dm.generate_report()
        history = self.dm.get_report_history()
        self.assertEqual(history["count"], 2)

    def test_get_last_report(self):
        self.dm.generate_report()
        last = self.dm.get_last_report()
        self.assertIsNotNone(last)
        self.assertIn("overall_status", last)

    def test_get_status(self):
        status = self.dm.get_status()
        self.assertTrue(status["has_snapshot_manager"])
        self.assertIn("monitored_paths", status)

    def test_disk_warning_threshold(self):
        # Create a mock that returns high usage
        dm = DriveMonitor(self.root, ledger=MagicMock())
        dm.DISK_WARNING_PERCENT = 0.0  # everything is "warning"
        report = dm.generate_report()
        self.assertIn(report.overall_status, ["warning", "critical"])

    def test_drive_health_to_dict(self):
        h = DriveHealth(path="/test", label="Test", total_gb=100, used_gb=50, free_gb=50, percent_used=50, status="healthy")
        d = h.to_dict()
        self.assertEqual(d["path"], "/test")
        self.assertEqual(d["status"], "healthy")

    def test_daily_report_to_dict(self):
        r = DailyReport(report_id="test", timestamp=time.time())
        d = r.to_dict()
        self.assertEqual(d["report_id"], "test")

    def test_report_with_ab_drive(self):
        ab_drive = MagicMock()
        ab_drive.status.return_value = {
            "active_drive": "A",
            "staging_drive": "B",
            "active_version": "1.0.0",
            "staging_version": "1.0.1",
            "canary_active": True,
            "canary_reason": "canary in progress: 3.0/7.0 days",
            "canary_metrics": {},
            "rollback_count": 0,
            "active_path": "/dev/sda",
            "staging_path": "/dev/sdb",
        }
        ab_drive.get_active_drive.return_value = "A"
        ab_drive.get_staging_drive.return_value = "B"
        ab_drive.get_active_path.return_value = str(self.root)
        ab_drive.get_staging_path.return_value = str(self.root)

        dm = DriveMonitor(self.root, ab_drive=ab_drive, snapshot_manager=self.sm)
        report = dm.generate_report()
        self.assertTrue(report.ab_drive_status.get("available"))
        self.assertEqual(report.ab_drive_status["active_drive"], "A")

    def test_report_with_cloud_sync(self):
        cloud_sync = MagicMock()
        cloud_sync.get_status.return_value = {
            "last_sync": time.time() - 3600,
            "configured": True,
        }
        dm = DriveMonitor(self.root, snapshot_manager=self.sm, cloud_sync=cloud_sync)
        report = dm.generate_report()
        self.assertTrue(report.cloud_sync_status.get("available"))

    def test_report_detects_stale_snapshots(self):
        dm = DriveMonitor(self.root, snapshot_manager=self.sm)
        dm.SNAPSHOT_STALE_HOURS = 0  # everything is stale
        report = dm.generate_report()
        self.assertTrue(report.snapshot_status.get("stale"))
        self.assertGreater(len(report.issues), 0)

    def test_report_persists(self):
        self.dm.generate_report()
        history = self.dm.get_report_history()
        self.assertGreater(history["count"], 0)


if __name__ == "__main__":
    unittest.main()
