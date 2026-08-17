"""Tests for the A/B drive automation module.

Tests verify:
- State persistence (save/load)
- Drive staging and promotion
- Canary test passing and failing
- Automatic rollback on canary failure
- Environment variable abstraction
- Rollback history
- Status endpoint
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.ab_drive import (
    ABDriveManager,
    DriveState,
    CanaryMetrics,
    CanaryResult,
    DEFAULT_CANARY_DAYS,
)


class TestDriveState(unittest.TestCase):
    """Tests for DriveState dataclass."""

    def test_default_state(self):
        s = DriveState()
        self.assertEqual(s.active_drive, "A")
        self.assertEqual(s.staging_drive, "B")
        self.assertFalse(s.canary_active)

    def test_to_dict_and_from_dict(self):
        s = DriveState(
            active_drive="B",
            staging_drive="A",
            active_version="1.2.3",
            canary_active=True,
        )
        d = s.to_dict()
        s2 = DriveState.from_dict(d)
        self.assertEqual(s2.active_drive, "B")
        self.assertEqual(s2.staging_drive, "A")
        self.assertTrue(s2.canary_active)


class TestCanaryMetrics(unittest.TestCase):
    """Tests for CanaryMetrics."""

    def test_default(self):
        m = CanaryMetrics()
        self.assertEqual(m.api_errors, 0)

    def test_to_dict_and_from_dict(self):
        m = CanaryMetrics(api_errors=5, timeouts=2, crashes=1)
        d = m.to_dict()
        m2 = CanaryMetrics.from_dict(d)
        self.assertEqual(m2.api_errors, 5)
        self.assertEqual(m2.timeouts, 2)


class TestABDriveManager(unittest.TestCase):
    """Tests for the ABDriveManager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-abdrive-")
        self.mgr = ABDriveManager(
            state_path=Path(self.tmpdir) / "ab_state.json",
            canary_days=0,  # immediate pass for testing
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_state(self):
        self.assertEqual(self.mgr.get_active_drive(), "A")
        self.assertEqual(self.mgr.get_staging_drive(), "B")

    def test_state_persistence(self):
        self.mgr.stage_update("1.0.0")
        # Create new manager from same state file
        mgr2 = ABDriveManager(state_path=self.mgr.state_path)
        self.assertEqual(mgr2.state.staging_version, "1.0.0")
        self.assertTrue(mgr2.state.canary_active)

    def test_stage_update(self):
        result = self.mgr.stage_update("2.0.0")
        self.assertTrue(result["staged"])
        self.assertEqual(result["version"], "2.0.0")
        self.assertTrue(self.mgr.state.canary_active)

    def test_promote_no_staging(self):
        result = self.mgr.promote()
        self.assertFalse(result["promoted"])

    def test_promote_after_canary_pass(self):
        self.mgr.canary_days = 0  # immediate pass
        self.mgr.stage_update("2.0.0")
        result = self.mgr.promote()
        self.assertTrue(result["promoted"])
        self.assertEqual(self.mgr.get_active_drive(), "B")
        self.assertEqual(self.mgr.state.active_version, "2.0.0")

    def test_canary_check_pass(self):
        self.mgr.canary_days = 7
        self.mgr.stage_update("2.0.0")
        result = self.mgr.check_canary()
        self.assertTrue(result.passed)
        self.assertIn("in progress", result.reason)

    def test_canary_check_fail_api_errors(self):
        self.mgr.stage_update("2.0.0")
        self.mgr.record_canary_metric(api_errors=20)
        result = self.mgr.check_canary()
        self.assertFalse(result.passed)
        self.assertTrue(result.should_rollback)
        self.assertIn("API errors", result.reason)

    def test_canary_check_fail_timeouts(self):
        self.mgr.stage_update("2.0.0")
        self.mgr.record_canary_metric(timeouts=10)
        result = self.mgr.check_canary()
        self.assertFalse(result.passed)
        self.assertTrue(result.should_rollback)

    def test_canary_check_fail_crashes(self):
        self.mgr.stage_update("2.0.0")
        self.mgr.record_canary_metric(crashes=5)
        result = self.mgr.check_canary()
        self.assertFalse(result.passed)
        self.assertTrue(result.should_rollback)

    def test_canary_check_fail_fatal_loops(self):
        self.mgr.stage_update("2.0.0")
        self.mgr.record_canary_metric(fatal_loops=1)
        result = self.mgr.check_canary()
        self.assertFalse(result.passed)
        self.assertTrue(result.should_rollback)

    def test_rollback(self):
        # First promote to B
        self.mgr.canary_days = 0
        self.mgr.stage_update("2.0.0")
        self.mgr.promote()
        self.assertEqual(self.mgr.get_active_drive(), "B")
        # Now rollback
        result = self.mgr.rollback("canary failure")
        self.assertTrue(result["rolled_back"])
        self.assertEqual(self.mgr.get_active_drive(), "A")
        self.assertEqual(len(self.mgr.state.rollback_history), 1)

    def test_rollback_history_recorded(self):
        self.mgr.stage_update("2.0.0")
        self.mgr.rollback("test rollback")
        self.assertEqual(len(self.mgr.state.rollback_history), 1)
        self.assertEqual(self.mgr.state.rollback_history[0]["reason"], "test rollback")

    def test_status(self):
        status = self.mgr.status()
        self.assertIn("active_drive", status)
        self.assertIn("staging_drive", status)
        self.assertIn("canary_active", status)

    def test_get_active_path_with_env(self):
        os.environ["ANUBIS_ACTIVE_DRIVE"] = "/test/drive"
        try:
            path = self.mgr.get_active_path("models")
            self.assertIn("test", path)
            self.assertIn("models", path)
        finally:
            del os.environ["ANUBIS_ACTIVE_DRIVE"]

    def test_get_active_path_fallback(self):
        # No env var set, should fall back to state
        os.environ.pop("ANUBIS_ACTIVE_DRIVE", None)
        path = self.mgr.get_active_path()
        self.assertEqual(path, "A")

    def test_promote_swaps_drives(self):
        self.mgr.canary_days = 0
        self.mgr.stage_update("2.0.0")
        self.mgr.promote()
        # After promotion, staging should be the old active
        self.assertEqual(self.mgr.state.staging_drive, "A")
        self.assertEqual(self.mgr.state.active_drive, "B")

    def test_multiple_promotions(self):
        self.mgr.canary_days = 0
        # First promotion: A → B
        self.mgr.stage_update("2.0.0")
        self.mgr.promote()
        self.assertEqual(self.mgr.get_active_drive(), "B")
        # Second promotion: B → A
        self.mgr.stage_update("3.0.0")
        self.mgr.promote()
        self.assertEqual(self.mgr.get_active_drive(), "A")
        self.assertEqual(self.mgr.state.active_version, "3.0.0")


if __name__ == "__main__":
    unittest.main()
