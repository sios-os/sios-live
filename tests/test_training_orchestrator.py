"""Tests for the training orchestrator.

Tests verify:
- Training plan preparation (dataset export, script generation)
- Plan approval and rejection
- Candidate evaluation and comparison
- Staging on A/B drive
- Canary check and promotion
- Full cycle execution
- Status and plan listing
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

from anubis.training_orchestrator import (
    TrainingOrchestrator,
    TrainingPlan,
    TrainingCycleResult,
)
from anubis.distillation import KnowledgeDistiller, TrainingPair
from anubis.unsloth_adapter import UnslothAdapter, TrainingConfig
from anubis.evaluation import ModelEvaluator, EvaluationResult
from anubis.ab_drive import ABDriveManager


@dataclass
class MockCompletion:
    text: str
    completion_tokens: int = 10
    duration_s: float = 0.1


class TestTrainingOrchestrator(unittest.TestCase):
    """Tests for the TrainingOrchestrator."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-orch-")
        self.distiller = KnowledgeDistiller(
            queue_path=Path(self.tmpdir) / "queue.jsonl"
        )
        # Pre-populate the queue
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.5, category="coding"),
            TrainingPair(prompt="q2", response="r2", quality_score=0.6, category="general"),
        ]
        self.distiller.queue_pairs(pairs)

        self.orchestrator = TrainingOrchestrator(
            distiller=self.distiller,
            unsloth=UnslothAdapter(),
            evaluator=ModelEvaluator(),
            ab_drive=ABDriveManager(
                state_path=Path(self.tmpdir) / "ab_state.json",
                canary_days=0,
            ),
            output_dir=Path(self.tmpdir) / "training",
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_prepare_training_plan(self):
        plan = self.orchestrator.prepare_training_plan()
        self.assertEqual(plan.status, "pending_approval")
        self.assertEqual(plan.queue_size, 2)
        self.assertTrue(Path(plan.dataset_path).exists())
        self.assertTrue(Path(plan.script_path).exists())

    def test_prepare_plan_empty_queue(self):
        # Clear queue
        self.distiller.clear_queue()
        plan = self.orchestrator.prepare_training_plan()
        self.assertEqual(plan.status, "empty_queue")

    def test_approve_plan(self):
        plan = self.orchestrator.prepare_training_plan()
        result = self.orchestrator.approve_plan(plan.plan_id)
        self.assertTrue(result["approved"])
        self.assertEqual(self.orchestrator.get_plan(plan.plan_id).status, "approved")

    def test_reject_plan(self):
        plan = self.orchestrator.prepare_training_plan()
        result = self.orchestrator.reject_plan(plan.plan_id, "too risky")
        self.assertTrue(result["rejected"])
        self.assertEqual(self.orchestrator.get_plan(plan.plan_id).status, "rejected")

    def test_approve_nonexistent_plan(self):
        result = self.orchestrator.approve_plan("nonexistent")
        self.assertFalse(result["approved"])

    def test_evaluate_candidate(self):
        # Mock models
        good_model = MagicMock()
        good_model.generate.return_value = MockCompletion(
            text="def foo(): return 42"
        )
        bad_model = MagicMock()
        bad_model.generate.return_value = MockCompletion(text="I don't know")

        comparison = self.orchestrator.evaluate_candidate(
            good_model, bad_model,
            candidate_name="good",
            current_name="bad",
        )
        self.assertIn("recommendation", comparison)
        self.assertIn(comparison["recommendation"], ["promote", "reject", "needs_more_training"])

    def test_stage_candidate_promote(self):
        comparison = {"recommendation": "promote"}
        result = self.orchestrator.stage_candidate("2.0.0", comparison)
        self.assertTrue(result.get("staged"))

    def test_stage_candidate_reject(self):
        comparison = {"recommendation": "reject"}
        result = self.orchestrator.stage_candidate("2.0.0", comparison)
        self.assertFalse(result.get("staged"))

    def test_check_canary_and_promote(self):
        # Stage first
        self.orchestrator.ab_drive.canary_days = 0
        self.orchestrator.ab_drive.stage_update("2.0.0")
        result = self.orchestrator.check_canary_and_promote()
        # With canary_days=0, should promote immediately
        self.assertTrue(result.get("promoted"))

    def test_check_canary_rollback(self):
        # Stage and then record failures
        self.orchestrator.ab_drive.stage_update("2.0.0")
        self.orchestrator.ab_drive.record_canary_metric(crashes=10)
        result = self.orchestrator.check_canary_and_promote()
        self.assertTrue(result.get("rolled_back"))

    def test_run_cycle(self):
        good_model = MagicMock()
        good_model.generate.return_value = MockCompletion(text="def foo(): pass")
        bad_model = MagicMock()
        bad_model.generate.return_value = MockCompletion(text="nope")

        result = self.orchestrator.run_cycle(
            good_model, bad_model, "2.0.0",
            candidate_name="good",
            current_name="bad",
        )
        self.assertTrue(result.evaluated)
        self.assertIn(result.recommendation, ["promote", "reject", "needs_more_training"])

    def test_status(self):
        status = self.orchestrator.status()
        self.assertIn("queue_pairs", status)
        self.assertIn("unsloth_available", status)
        self.assertIn("ab_drive", status)
        self.assertIn("evaluator", status)

    def test_list_plans(self):
        self.orchestrator.prepare_training_plan()
        plans = self.orchestrator.list_plans()
        self.assertEqual(len(plans), 1)

    def test_get_plan(self):
        plan = self.orchestrator.prepare_training_plan()
        retrieved = self.orchestrator.get_plan(plan.plan_id)
        self.assertEqual(retrieved.plan_id, plan.plan_id)

    def test_get_nonexistent_plan(self):
        self.assertIsNone(self.orchestrator.get_plan("nonexistent"))


class TestTrainingPlan(unittest.TestCase):
    """Tests for TrainingPlan dataclass."""

    def test_to_dict(self):
        plan = TrainingPlan(
            plan_id="test",
            queue_size=100,
            status="pending_approval",
        )
        d = plan.to_dict()
        self.assertEqual(d["plan_id"], "test")
        self.assertEqual(d["queue_size"], 100)
        self.assertEqual(d["status"], "pending_approval")


class TestTrainingCycleResult(unittest.TestCase):
    """Tests for TrainingCycleResult."""

    def test_defaults(self):
        r = TrainingCycleResult()
        self.assertFalse(r.trained)
        self.assertFalse(r.evaluated)
        self.assertEqual(r.recommendation, "")


if __name__ == "__main__":
    unittest.main()
