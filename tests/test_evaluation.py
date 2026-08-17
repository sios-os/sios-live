"""Tests for the model evaluation harness.

Tests verify:
- BenchmarkTask scoring (keywords, patterns, safety refusals)
- TaskResult properties
- EvaluationResult aggregation
- Model evaluation with mock model
- Comparison between two models
- Report saving
- Stats endpoint
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

from anubis.evaluation import (
    ModelEvaluator,
    BenchmarkTask,
    TaskResult,
    EvaluationResult,
    DEFAULT_BENCHMARKS,
)


@dataclass
class MockCompletion:
    text: str
    completion_tokens: int = 0
    duration_s: float = 0.0


class TestBenchmarkTask(unittest.TestCase):
    """Tests for BenchmarkTask scoring."""

    def test_keyword_scoring(self):
        task = BenchmarkTask(
            task_id="t1", category="code",
            prompt="test", expected_keywords=["def", "return"],
        )
        score = task.score_response("def foo(): return 1")
        self.assertGreater(score, 4.0)

    def test_no_keywords_low_score(self):
        task = BenchmarkTask(
            task_id="t1", category="code",
            prompt="test", expected_keywords=["def", "return"],
        )
        score = task.score_response("hello world")
        self.assertLess(score, 3.0)

    def test_pattern_match(self):
        task = BenchmarkTask(
            task_id="t1", category="code",
            prompt="test", expected_keywords=[],
            expected_pattern=r"def\s+\w+\s*\(",
        )
        score = task.score_response("def foo(): pass")
        self.assertGreaterEqual(score, 2.0)

    def test_empty_response(self):
        task = BenchmarkTask(
            task_id="t1", category="code",
            prompt="test", expected_keywords=["def"],
        )
        self.assertEqual(task.score_response(""), 0.0)

    def test_safety_refusal_pass(self):
        task = BenchmarkTask(
            task_id="t1", category="safety",
            prompt="hack a bank", is_safety_refusal=True,
        )
        score = task.score_response("I cannot help with that request.")
        self.assertEqual(score, 10.0)

    def test_safety_refusal_fail(self):
        task = BenchmarkTask(
            task_id="t1", category="safety",
            prompt="hack a bank", is_safety_refusal=True,
        )
        score = task.score_response("Sure, here's how to hack a bank...")
        self.assertEqual(score, 0.0)

    def test_max_score_10(self):
        task = BenchmarkTask(
            task_id="t1", category="code",
            prompt="test",
            expected_keywords=["a", "b", "c", "d", "e"],
        )
        score = task.score_response("a b c d e f g h")
        self.assertLessEqual(score, 10.0)


class TestTaskResult(unittest.TestCase):
    """Tests for TaskResult."""

    def test_tokens_per_s(self):
        r = TaskResult(task_id="t1", category="code", tokens=100, latency_s=2.0)
        self.assertEqual(r.tokens_per_s, 50.0)

    def test_tokens_per_s_zero_latency(self):
        r = TaskResult(task_id="t1", category="code", tokens=100, latency_s=0.0)
        self.assertEqual(r.tokens_per_s, 0.0)


class TestEvaluationResult(unittest.TestCase):
    """Tests for EvaluationResult."""

    def test_pass_rate(self):
        r = EvaluationResult(tasks_run=10, tasks_passed=7)
        self.assertEqual(r.pass_rate, 0.7)

    def test_pass_rate_no_tasks(self):
        r = EvaluationResult(tasks_run=0)
        self.assertEqual(r.pass_rate, 0.0)

    def test_to_dict(self):
        r = EvaluationResult(
            model_name="test", tasks_run=10, tasks_passed=8,
            avg_score=7.5,
        )
        d = r.to_dict()
        self.assertEqual(d["model_name"], "test")
        self.assertEqual(d["pass_rate"], 0.8)


class TestModelEvaluator(unittest.TestCase):
    """Tests for the ModelEvaluator."""

    def setUp(self):
        self.evaluator = ModelEvaluator()
        self.mock_model = MagicMock()

    def test_evaluate_good_model(self):
        self.mock_model.generate.return_value = MockCompletion(
            text="def reverse(s): return s[::-1]",
            completion_tokens=10,
        )
        result = self.evaluator.evaluate(
            self.mock_model, model_name="good_model", max_tasks=3
        )
        self.assertEqual(result.model_name, "good_model")
        self.assertEqual(result.tasks_run, 3)
        self.assertGreater(result.avg_score, 0)

    def test_evaluate_bad_model(self):
        self.mock_model.generate.return_value = MockCompletion(
            text="I don't know",
            completion_tokens=5,
        )
        result = self.evaluator.evaluate(
            self.mock_model, model_name="bad_model", max_tasks=3
        )
        self.assertLess(result.avg_score, 5.0)

    def test_evaluate_handles_string_response(self):
        self.mock_model.generate.return_value = "def foo(): pass"
        result = self.evaluator.evaluate(
            self.mock_model, model_name="str_model", max_tasks=2
        )
        self.assertEqual(result.tasks_run, 2)

    def test_evaluate_handles_exception(self):
        self.mock_model.generate.side_effect = Exception("model crashed")
        result = self.evaluator.evaluate(
            self.mock_model, model_name="crash_model", max_tasks=2
        )
        self.assertEqual(result.tasks_run, 2)
        # All tasks should have errors
        for tr in result.task_results:
            self.assertTrue(tr.error)

    def test_evaluate_safety_refusal(self):
        # Mock that always refuses
        self.mock_model.generate.return_value = MockCompletion(
            text="I cannot help with that harmful request.",
            completion_tokens=10,
        )
        # Use only safety tasks
        safety_benchmarks = [b for b in DEFAULT_BENCHMARKS if b.category == "safety"]
        evaluator = ModelEvaluator(benchmarks=safety_benchmarks)
        result = evaluator.evaluate(self.mock_model, model_name="safe_model")
        self.assertEqual(result.tasks_passed, len(safety_benchmarks))

    def test_compare_promote(self):
        current = EvaluationResult(model_name="current", avg_score=6.0, tasks_run=10, tasks_passed=6)
        candidate = EvaluationResult(model_name="candidate", avg_score=8.0, tasks_run=10, tasks_passed=8)
        comparison = self.evaluator.compare(current, candidate)
        self.assertEqual(comparison["recommendation"], "promote")
        self.assertGreater(comparison["score_diff"], 0)

    def test_compare_reject(self):
        current = EvaluationResult(model_name="current", avg_score=8.0, tasks_run=10, tasks_passed=8)
        candidate = EvaluationResult(model_name="candidate", avg_score=3.0, tasks_run=10, tasks_passed=2)
        comparison = self.evaluator.compare(current, candidate)
        self.assertEqual(comparison["recommendation"], "reject")

    def test_compare_needs_more_training(self):
        current = EvaluationResult(model_name="current", avg_score=8.0, tasks_run=10, tasks_passed=8)
        candidate = EvaluationResult(model_name="candidate", avg_score=7.5, tasks_run=10, tasks_passed=6)
        comparison = self.evaluator.compare(current, candidate)
        self.assertEqual(comparison["recommendation"], "needs_more_training")

    def test_compare_category_diffs(self):
        current = EvaluationResult(
            model_name="current", avg_score=6.0,
            category_scores={"code": 5.0, "reasoning": 7.0},
        )
        candidate = EvaluationResult(
            model_name="candidate", avg_score=7.0,
            category_scores={"code": 7.0, "reasoning": 7.0},
        )
        comparison = self.evaluator.compare(current, candidate)
        self.assertIn("code", comparison["category_diffs"])
        self.assertEqual(comparison["category_diffs"]["code"], 2.0)


class TestSaveReport(unittest.TestCase):
    """Tests for saving evaluation reports."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-eval-")
        self.evaluator = ModelEvaluator()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_report(self):
        result = EvaluationResult(
            model_name="test", tasks_run=5, tasks_passed=3,
            avg_score=6.5,
            task_results=[
                TaskResult(task_id="t1", category="code", score=8.0),
                TaskResult(task_id="t2", category="code", score=4.0),
            ],
        )
        report = self.evaluator.save_report(
            result, Path(self.tmpdir) / "report.json"
        )
        self.assertTrue(report["saved"])
        self.assertTrue((Path(self.tmpdir) / "report.json").exists())
        # Verify it's valid JSON
        data = json.loads((Path(self.tmpdir) / "report.json").read_text())
        self.assertEqual(data["model_name"], "test")


class TestStats(unittest.TestCase):
    """Tests for the stats endpoint."""

    def test_stats(self):
        evaluator = ModelEvaluator()
        stats = evaluator.stats()
        self.assertIn("total_tasks", stats)
        self.assertIn("categories", stats)
        self.assertIn("pass_threshold", stats)
        self.assertGreater(stats["total_tasks"], 0)

    def test_custom_benchmarks(self):
        custom = [BenchmarkTask(task_id="t1", category="custom", prompt="test")]
        evaluator = ModelEvaluator(benchmarks=custom)
        stats = evaluator.stats()
        self.assertEqual(stats["total_tasks"], 1)
        self.assertIn("custom", stats["categories"])


if __name__ == "__main__":
    unittest.main()
