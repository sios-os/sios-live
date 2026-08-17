"""Tests for task delegator, security auditor, and constitutional trainer."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.task_delegator import (
    TaskDelegator, SubAgentTask, DelegationResult,
    TaskStatus, TaskType,
)
from anubis.security_audit import SecurityAuditor, AuditResult, AuditCheck
from anubis.constitutional_training import (
    ConstitutionalTrainer, ConstitutionalTrainingPair,
)


class TestTaskDelegator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.delegator = TaskDelegator(
            self.tmpdir, ledger=MagicMock(), model=None, sandbox=None,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_status(self):
        status = self.delegator.get_status()
        self.assertEqual(status["active_tasks"], 0)
        self.assertEqual(status["max_concurrent"], 4)

    def test_delegate_empty_tasks(self):
        result = self.delegator.delegate([])
        self.assertEqual(result.tasks, [])

    def test_delegate_single_task_no_model(self):
        result = self.delegator.delegate([
            {"description": "test task", "task_type": "RESEARCH"},
        ], synthesize=False)
        self.assertEqual(len(result.tasks), 1)
        # Without a model, research task should fail
        self.assertIn(result.tasks[0].status, [TaskStatus.FAILED, TaskStatus.COMPLETED])

    def test_delegate_monitoring_task(self):
        result = self.delegator.delegate([
            {"description": "monitor test", "task_type": "MONITORING", "parameters": {"target": "cpu"}},
        ], synthesize=False)
        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].status, TaskStatus.COMPLETED)

    def test_delegate_persistence(self):
        self.delegator.delegate([
            {"description": "monitor test", "task_type": "MONITORING"},
        ], synthesize=False)
        delegations = self.delegator.list_delegations()
        self.assertEqual(len(delegations), 1)

    def test_get_delegation(self):
        result = self.delegator.delegate([
            {"description": "monitor test", "task_type": "MONITORING"},
        ], synthesize=False)
        fetched = self.delegator.get_delegation(result.delegation_id)
        self.assertEqual(fetched["delegation_id"], result.delegation_id)

    def test_get_delegation_not_found(self):
        result = self.delegator.get_delegation("nonexistent")
        self.assertIn("error", result)

    def test_sub_agent_task_to_dict(self):
        task = SubAgentTask(
            task_id="test", task_type=TaskType.RESEARCH,
            description="test task",
        )
        d = task.to_dict()
        self.assertEqual(d["task_id"], "test")
        self.assertEqual(d["task_type"], "RESEARCH")

    def test_sub_agent_task_from_dict(self):
        data = {
            "task_id": "test", "task_type": "CODING",
            "description": "test", "status": "COMPLETED",
        }
        task = SubAgentTask.from_dict(data)
        self.assertEqual(task.task_type, TaskType.CODING)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_max_concurrent_limit(self):
        tasks = [{"description": f"task {i}", "task_type": "MONITORING"} for i in range(10)]
        result = self.delegator.delegate(tasks, synthesize=False)
        self.assertLessEqual(len(result.tasks), TaskDelegator.MAX_CONCURRENT)


class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Create minimal structure
        (self.root / "anubis").mkdir()
        (self.root / "anubis" / "constitution.py").write_text("# test")
        (self.root / "anubis" / "identity.py").write_text("# test")
        (self.root / "anubis" / "ledger.py").write_text("# test")
        self.auditor = SecurityAuditor(self.root, ledger=MagicMock())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_run_audit(self):
        result = self.auditor.run_audit()
        self.assertGreater(result.total_checks, 0)
        self.assertGreater(result.passed, 0)
        self.assertIsInstance(result.to_dict(), dict)

    def test_audit_has_id(self):
        result = self.auditor.run_audit()
        self.assertTrue(len(result.audit_id) > 0)

    def test_audit_duration(self):
        result = self.auditor.run_audit()
        self.assertGreaterEqual(result.duration_s, 0.0)

    def test_constitutional_checks(self):
        result = self.auditor.run_audit()
        check_names = [c.name for c in result.checks]
        self.assertIn("constitutional_routine_allows", check_names)
        self.assertIn("constitutional_consequential_requires_approval", check_names)

    def test_immutable_laws_check(self):
        result = self.auditor.run_audit()
        check_names = [c.name for c in result.checks]
        self.assertIn("immutable_laws", check_names)

    def test_hazard_checks(self):
        result = self.auditor.run_audit()
        check_names = [c.name for c in result.checks]
        self.assertIn("hazard_recovery", check_names)
        self.assertIn("hazard_permission_integrity", check_names)

    def test_immutable_files_check(self):
        result = self.auditor.run_audit()
        check_names = [c.name for c in result.checks]
        self.assertIn("immutable_constitution.py", check_names)

    def test_get_status(self):
        status = self.auditor.get_status()
        self.assertIn("sandbox_configured", status)
        self.assertIn("gateway_configured", status)


class TestConstitutionalTrainer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.trainer = ConstitutionalTrainer(self.tmpdir, ledger=MagicMock())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_training_pairs(self):
        pairs = self.trainer.generate_training_pairs()
        self.assertGreater(len(pairs), 0)
        # Should cover all 8 immutable laws
        laws = {p.law for p in pairs}
        self.assertIn("human_protection", laws)
        self.assertIn("truth", laws)
        self.assertIn("non_manipulation", laws)
        self.assertIn("permission_integrity", laws)
        self.assertIn("local_privacy", laws)
        self.assertIn("financial_consent", laws)
        self.assertIn("audit", laws)
        self.assertIn("recovery", laws)

    def test_pair_categories(self):
        pairs = self.trainer.generate_training_pairs()
        categories = {p.category for p in pairs}
        self.assertIn("refusal", categories)
        self.assertIn("recognition", categories)
        self.assertIn("explanation", categories)

    def test_export_training_data(self):
        result = self.trainer.export_training_data()
        self.assertTrue(result["exported"])
        self.assertGreater(result["pair_count"], 0)
        path = Path(result["path"])
        self.assertTrue(path.exists())
        # Verify JSONL format
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        import json
        for line in lines:
            data = json.loads(line)
            self.assertIn("messages", data)
            self.assertEqual(len(data["messages"]), 2)

    def test_get_status(self):
        status = self.trainer.get_status()
        self.assertIn("output_dir", status)
        self.assertIn("laws_covered", status)
        self.assertEqual(len(status["laws_covered"]), 8)

    def test_pair_to_jsonl(self):
        pair = ConstitutionalTrainingPair(
            pair_id="test",
            prompt="test prompt",
            response="test response",
            category="refusal",
            law="truth",
        )
        import json
        data = json.loads(pair.to_jsonl())
        self.assertEqual(data["pair_id"], "test")
        self.assertEqual(data["messages"][0]["content"], "test prompt")

    def test_hazard_scenarios_covered(self):
        pairs = self.trainer.generate_training_pairs()
        hazard_pairs = [p for p in pairs if p.category == "recognition"]
        self.assertGreater(len(hazard_pairs), 0)
        for p in hazard_pairs:
            self.assertTrue(p.hazard_pattern)


if __name__ == "__main__":
    unittest.main()
