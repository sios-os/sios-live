"""Tests for the cloud phase-out module.

Tests verify:
- CapabilityStatus properties (success rate, cloud usage)
- PhaseOutPlan initialization and serialization
- CloudPhaseOutManager state persistence
- should_use_cloud routing logic
- record_local_result (confidence update, graduation)
- record_cloud_result
- record_evaluation (head-to-head comparison)
- Graduation and regression logic
- PhaseOutRouter routing (local, cloud, fallback)
- Status and progress reporting
"""
import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.cloud_phaseout import (
    CloudPhaseOutManager,
    PhaseOutPlan,
    PhaseOutRouter,
    CapabilityStatus,
    CAPABILITIES,
)


@dataclass
class MockCompletion:
    text: str
    completion_tokens: int = 10


class TestCapabilityStatus(unittest.TestCase):
    """Tests for CapabilityStatus."""

    def test_defaults(self):
        cap = CapabilityStatus(name="test")
        self.assertEqual(cap.confidence, 0.0)
        self.assertFalse(cap.graduated)

    def test_local_success_rate(self):
        cap = CapabilityStatus(
            name="test", local_successes=8, local_failures=2
        )
        self.assertEqual(cap.local_success_rate, 0.8)

    def test_local_success_rate_no_calls(self):
        cap = CapabilityStatus(name="test")
        self.assertEqual(cap.local_success_rate, 0.0)

    def test_cloud_usage_pct(self):
        cap = CapabilityStatus(
            name="test", cloud_calls=30, local_calls=70
        )
        self.assertEqual(cap.cloud_usage_pct, 30.0)

    def test_to_dict(self):
        cap = CapabilityStatus(name="test", confidence=0.5)
        d = cap.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["confidence"], 0.5)


class TestPhaseOutPlan(unittest.TestCase):
    """Tests for PhaseOutPlan."""

    def test_initializes_all_capabilities(self):
        plan = PhaseOutPlan()
        for cap in CAPABILITIES:
            self.assertIn(cap, plan.capabilities)

    def test_to_dict(self):
        plan = PhaseOutPlan()
        d = plan.to_dict()
        self.assertIn("capabilities", d)
        self.assertIn("graduation_threshold", d)


class TestCloudPhaseOutManager(unittest.TestCase):
    """Tests for CloudPhaseOutManager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-phaseout-")
        self.mgr = CloudPhaseOutManager(
            state_path=Path(self.tmpdir) / "phase_out.json",
            graduation_threshold=0.85,
            regression_threshold=0.60,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_state(self):
        plan = self.mgr.plan
        for cap in CAPABILITIES:
            self.assertIn(cap, plan.capabilities)
            self.assertFalse(plan.capabilities[cap].graduated)

    def test_should_use_cloud_low_confidence(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.3
        self.assertTrue(self.mgr.should_use_cloud("code_generation"))

    def test_should_use_cloud_high_confidence(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.9
        self.assertFalse(self.mgr.should_use_cloud("code_generation"))

    def test_should_use_cloud_graduated(self):
        cap = self.mgr.plan.capabilities["code_generation"]
        cap.confidence = 0.95
        cap.graduated = True
        self.assertFalse(self.mgr.should_use_cloud("code_generation"))

    def test_should_use_cloud_unknown_capability(self):
        self.assertTrue(self.mgr.should_use_cloud("unknown_cap"))

    def test_record_local_success(self):
        self.mgr.record_local_result("code_generation", success=True)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertEqual(cap.local_calls, 1)
        self.assertEqual(cap.local_successes, 1)
        self.assertGreater(cap.confidence, 0)

    def test_record_local_failure(self):
        self.mgr.record_local_result("code_generation", success=False)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertEqual(cap.local_failures, 1)

    def test_graduation_after_enough_successes(self):
        # Record 20 successes with high scores to reach confidence > 0.85
        for _ in range(20):
            self.mgr.record_local_result("code_generation", success=True, score=9.0)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertTrue(cap.graduated)
        self.assertGreater(cap.graduated_at, 0)

    def test_no_graduation_without_enough_calls(self):
        # Only 5 calls — not enough for graduation
        for _ in range(5):
            self.mgr.record_local_result("code_generation", success=True, score=9.0)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertFalse(cap.graduated)

    def test_regression_re_enables_cloud(self):
        # Graduate first
        for _ in range(20):
            self.mgr.record_local_result("code_generation", success=True, score=9.0)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertTrue(cap.graduated)

        # Now cause regression
        cap.confidence = 0.5
        self.mgr.record_local_result("code_generation", success=False)
        cap = self.mgr.get_capability_status("code_generation")
        self.assertFalse(cap.graduated)

    def test_record_cloud_result(self):
        self.mgr.record_cloud_result("reasoning", score=8.0)
        cap = self.mgr.get_capability_status("reasoning")
        self.assertEqual(cap.cloud_calls, 1)
        self.assertEqual(cap.last_cloud_score, 8.0)

    def test_record_evaluation_local_better(self):
        result = self.mgr.record_evaluation("planning", 8.0, 6.0)
        self.assertTrue(result["local_better"])
        cap = self.mgr.get_capability_status("planning")
        self.assertGreater(cap.confidence, 0)

    def test_record_evaluation_cloud_better(self):
        result = self.mgr.record_evaluation("planning", 4.0, 8.0)
        self.assertFalse(result["local_better"])

    def test_state_persistence(self):
        self.mgr.record_local_result("code_generation", success=True)
        # Create new manager from same state
        mgr2 = CloudPhaseOutManager(state_path=self.mgr.state_path)
        cap = mgr2.get_capability_status("code_generation")
        self.assertEqual(cap.local_calls, 1)

    def test_graduated_capabilities(self):
        for _ in range(20):
            self.mgr.record_local_result("summarization", success=True, score=9.0)
        graduated = self.mgr.graduated_capabilities()
        self.assertIn("summarization", graduated)

    def test_active_cloud_dependencies(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.3
        deps = self.mgr.active_cloud_dependencies()
        self.assertIn("code_generation", deps)

    def test_overall_progress(self):
        progress = self.mgr.overall_progress()
        self.assertIn("total_capabilities", progress)
        self.assertIn("graduated", progress)
        self.assertIn("graduation_pct", progress)

    def test_status(self):
        status = self.mgr.status()
        self.assertIn("overall", status)
        self.assertIn("graduated", status)
        self.assertIn("capabilities", status)


class TestPhaseOutRouter(unittest.TestCase):
    """Tests for PhaseOutRouter."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-router-")
        self.mgr = CloudPhaseOutManager(
            state_path=Path(self.tmpdir) / "phase_out.json",
        )
        self.local_model = MagicMock()
        self.cloud_model = MagicMock()
        self.router = PhaseOutRouter(
            self.mgr, local_model=self.local_model, cloud_model=self.cloud_model
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_routes_to_cloud_when_low_confidence(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.3
        self.cloud_model.generate.return_value = MockCompletion(text="cloud response")
        result = self.router.route("code_generation", "write code")
        self.assertEqual(result["source"], "cloud")
        self.assertEqual(result["response"], "cloud response")

    def test_routes_to_local_when_high_confidence(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.9
        self.local_model.generate.return_value = MockCompletion(text="local response")
        result = self.router.route("code_generation", "write code")
        self.assertEqual(result["source"], "local")
        self.assertEqual(result["response"], "local response")

    def test_fallback_to_local_on_cloud_failure(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.3
        self.cloud_model.generate.side_effect = Exception("cloud down")
        self.local_model.generate.return_value = MockCompletion(text="local response")
        result = self.router.route("code_generation", "write code")
        self.assertEqual(result["source"], "local_fallback")

    def test_fallback_to_cloud_on_local_failure(self):
        self.mgr.plan.capabilities["code_generation"].confidence = 0.9
        self.local_model.generate.side_effect = Exception("local down")
        self.cloud_model.generate.return_value = MockCompletion(text="cloud response")
        result = self.router.route("code_generation", "write code")
        self.assertEqual(result["source"], "cloud_fallback")

    def test_no_models_available(self):
        router = PhaseOutRouter(self.mgr, local_model=None, cloud_model=None)
        result = router.route("code_generation", "write code")
        self.assertEqual(result["source"], "no_model")

    def test_routes_to_local_when_graduated(self):
        cap = self.mgr.plan.capabilities["code_generation"]
        cap.confidence = 0.95
        cap.graduated = True
        self.local_model.generate.return_value = MockCompletion(text="local response")
        result = self.router.route("code_generation", "write code")
        self.assertEqual(result["source"], "local")


if __name__ == "__main__":
    unittest.main()
