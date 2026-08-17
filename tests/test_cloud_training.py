"""Tests for the Lambda cloud training/testing adapter.

Tests verify:
- Configuration loading
- Cost preview (GPU pricing, runtime estimation)
- Constitutional gate (training=MAIN_ENGINE, testing=CONSEQUENTIAL)
- Privacy gate (sensitive data detection)
- Job submission (approved/denied)
- Job status tracking
- Job cancellation
- Artifact download
- Status endpoint (no secrets)
- Evidence ledger logging
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.cloud_training import (
    LambdaAdapter,
    LambdaConfig,
    JobSpec,
    JobResult,
    GPU_TYPES,
    _check_sensitive_data,
)
from anubis.constitution import ChangeClass


class TestConfig(unittest.TestCase):
    """Tests for configuration loading."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-lambda-cfg-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_not_configured(self):
        cfg = LambdaConfig()
        self.assertFalse(cfg.is_configured)

    def test_config_from_file(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({
            "lambda": {"api_key": "test-key"},
        }), encoding="utf-8")
        cfg = LambdaConfig.from_file(cfg_path)
        self.assertTrue(cfg.is_configured)
        self.assertEqual(cfg.api_key, "test-key")

    def test_config_missing_file(self):
        cfg = LambdaConfig.from_file(Path(self.tmpdir) / "nonexistent.json")
        self.assertFalse(cfg.is_configured)

    def test_config_no_lambda_section(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({"gemini": {"api_key": "k"}}), encoding="utf-8")
        cfg = LambdaConfig.from_file(cfg_path)
        self.assertFalse(cfg.is_configured)


class TestJobSpec(unittest.TestCase):
    """Tests for job specification."""

    def test_training_job_type(self):
        spec = JobSpec(name="test", job_type="training")
        self.assertTrue(spec.is_training)
        self.assertFalse(spec.is_testing)

    def test_testing_job_type(self):
        spec = JobSpec(name="test", job_type="testing")
        self.assertFalse(spec.is_training)
        self.assertTrue(spec.is_testing)

    def test_cost_estimate(self):
        spec = JobSpec(
            name="test", job_type="testing",
            gpu_type="nvidia_a10", num_gpus=2, runtime_hours=3.0,
        )
        cost = spec.estimate_cost()
        self.assertEqual(cost["num_gpus"], 2)
        self.assertEqual(cost["runtime_hours"], 3.0)
        # A10 = $0.75/hr * 2 GPUs * 3 hours = $4.50
        self.assertEqual(cost["estimated_total"], 4.50)

    def test_cost_estimate_unknown_gpu(self):
        spec = JobSpec(
            name="test", job_type="testing",
            gpu_type="unknown_gpu", num_gpus=1, runtime_hours=1.0,
        )
        cost = spec.estimate_cost()
        # Unknown GPU defaults to $1.0/hr
        self.assertEqual(cost["estimated_total"], 1.0)

    def test_cost_estimate_single_gpu(self):
        spec = JobSpec(
            name="test", job_type="training",
            gpu_type="nvidia_h100_80gb", num_gpus=1, runtime_hours=2.0,
        )
        cost = spec.estimate_cost()
        # H100 = $2.49/hr * 1 GPU * 2 hours = $4.98
        self.assertEqual(cost["estimated_total"], 4.98)


class TestPrivacyGate(unittest.TestCase):
    """Tests for the privacy gate."""

    def test_clean_spec(self):
        spec = JobSpec(name="test", job_type="testing", command="python train.py")
        adapter = LambdaAdapter()
        self.assertIsNone(adapter._check_privacy(spec))

    def test_password_in_command(self):
        spec = JobSpec(name="test", job_type="testing", command="password=secret python train.py")
        adapter = LambdaAdapter()
        result = adapter._check_privacy(spec)
        self.assertIsNotNone(result)

    def test_api_key_in_description(self):
        spec = JobSpec(name="test", job_type="testing", description="api_key=ABC123")
        adapter = LambdaAdapter()
        result = adapter._check_privacy(spec)
        self.assertIsNotNone(result)

    def test_private_key_in_dataset(self):
        spec = JobSpec(
            name="test", job_type="testing",
            dataset_path="-----BEGIN RSA PRIVATE KEY-----\nMIIkey",
        )
        adapter = LambdaAdapter()
        result = adapter._check_privacy(spec)
        self.assertIsNotNone(result)


class TestConstitutionalGate(unittest.TestCase):
    """Tests for the constitutional evaluation gate."""

    def setUp(self):
        self.adapter = LambdaAdapter(LambdaConfig(api_key="test-key"))

    def test_training_requires_main_engine(self):
        spec = JobSpec(name="train", job_type="training")
        # MAIN_ENGINE requires artifact hash match
        test_hash = "abc123def456"
        allowed, reason, change_class = self.adapter._evaluate_job(
            spec, creator_approved=True,
            artifact_hash=test_hash,
            approved_artifact_hash=test_hash,
        )
        self.assertTrue(allowed)
        self.assertEqual(change_class, ChangeClass.MAIN_ENGINE)

    def test_testing_requires_consequential(self):
        spec = JobSpec(name="test", job_type="testing")
        allowed, reason, change_class = self.adapter._evaluate_job(spec, creator_approved=True)
        self.assertTrue(allowed)
        self.assertEqual(change_class, ChangeClass.CONSEQUENTIAL)

    def test_training_without_approval_denied(self):
        spec = JobSpec(name="train", job_type="training")
        allowed, reason, change_class = self.adapter._evaluate_job(spec, creator_approved=False)
        self.assertFalse(allowed)
        self.assertIn("Creator approval", reason)

    def test_training_without_hash_denied(self):
        spec = JobSpec(name="train", job_type="training")
        # MAIN_ENGINE requires artifact hash, even with approval
        allowed, reason, change_class = self.adapter._evaluate_job(spec, creator_approved=True)
        self.assertFalse(allowed)
        self.assertIn("artifact hash", reason.lower() + " " + reason)

    def test_testing_without_approval_denied(self):
        spec = JobSpec(name="test", job_type="testing")
        allowed, reason, change_class = self.adapter._evaluate_job(spec, creator_approved=False)
        self.assertFalse(allowed)
        self.assertIn("Creator approval", reason)


class TestCostPreview(unittest.TestCase):
    """Tests for cost preview (no submission)."""

    def setUp(self):
        self.adapter = LambdaAdapter(LambdaConfig(api_key="test-key"))

    def test_cost_preview_returns_dict(self):
        spec = JobSpec(name="test", job_type="testing", gpu_type="nvidia_a10", runtime_hours=2.0)
        preview = self.adapter.cost_preview(spec)
        self.assertIn("cost_estimate", preview)
        self.assertIn("job_name", preview)
        self.assertIn("approval_required", preview)

    def test_cost_preview_shows_court_review_for_training(self):
        spec = JobSpec(name="train", job_type="training")
        preview = self.adapter.cost_preview(spec)
        self.assertTrue(preview["requires_court_review"])

    def test_cost_preview_no_court_review_for_testing(self):
        spec = JobSpec(name="test", job_type="testing")
        preview = self.adapter.cost_preview(spec)
        self.assertFalse(preview["requires_court_review"])

    def test_cost_preview_privacy_check(self):
        spec = JobSpec(name="test", job_type="testing", command="password=secret")
        preview = self.adapter.cost_preview(spec)
        self.assertFalse(preview["privacy_check"]["ok"])
        self.assertIsNotNone(preview["privacy_check"]["issue"])

    def test_cost_preview_clean_privacy(self):
        spec = JobSpec(name="test", job_type="testing", command="python test.py")
        preview = self.adapter.cost_preview(spec)
        self.assertTrue(preview["privacy_check"]["ok"])


class TestJobSubmission(unittest.TestCase):
    """Tests for job submission."""

    def setUp(self):
        self.adapter = LambdaAdapter(LambdaConfig(api_key="test-key"))

    def test_submit_not_configured(self):
        adapter = LambdaAdapter(LambdaConfig())
        spec = JobSpec(name="test", job_type="testing")
        result = adapter.submit_job(spec, creator_approved=True)
        self.assertFalse(result["ok"])
        self.assertIn("not configured", result["error"])

    def test_submit_without_approval_denied(self):
        spec = JobSpec(name="test", job_type="testing")
        result = self.adapter.submit_job(spec, creator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("Creator approval", result["error"])

    def test_submit_with_sensitive_data_denied(self):
        spec = JobSpec(name="test", job_type="testing", command="password=secret")
        result = self.adapter.submit_job(spec, creator_approved=True)
        self.assertFalse(result["ok"])
        self.assertIn("privacy", result["error"])

    def test_submit_testing_approved(self):
        spec = JobSpec(name="test", job_type="testing", command="python test.py")
        result = self.adapter.submit_job(spec, creator_approved=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "pending")
        self.assertIn("job_id", result)

    def test_submit_training_approved(self):
        spec = JobSpec(name="train", job_type="training", command="python train.py")
        test_hash = "abc123def456"
        result = self.adapter.submit_job(
            spec, creator_approved=True,
            artifact_hash=test_hash,
            approved_artifact_hash=test_hash,
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["requires_court_review"])

    def test_submit_returns_cost_estimate(self):
        spec = JobSpec(
            name="test", job_type="testing",
            gpu_type="nvidia_a10", num_gpus=1, runtime_hours=2.0,
        )
        result = self.adapter.submit_job(spec, creator_approved=True)
        self.assertTrue(result["ok"])
        self.assertIn("cost_estimate", result)
        self.assertEqual(result["cost_estimate"]["estimated_total"], 1.50)


class TestJobStatus(unittest.TestCase):
    """Tests for job status tracking."""

    def setUp(self):
        self.adapter = LambdaAdapter(LambdaConfig(api_key="test-key"))
        self.spec = JobSpec(name="test", job_type="testing", command="python test.py")
        self.submit_result = self.adapter.submit_job(self.spec, creator_approved=True)
        self.job_id = self.submit_result["job_id"]

    def test_job_status_returns_dict(self):
        status = self.adapter.job_status(self.job_id)
        self.assertTrue(status["ok"])
        self.assertEqual(status["job_id"], self.job_id)
        self.assertEqual(status["status"], "pending")

    def test_job_status_not_found(self):
        status = self.adapter.job_status("nonexistent")
        self.assertFalse(status["ok"])
        self.assertIn("not found", status["error"])

    def test_list_jobs(self):
        jobs = self.adapter.list_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_id"], self.job_id)

    def test_cancel_job(self):
        result = self.adapter.cancel_job(self.job_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "cancelled")
        # Verify status updated
        status = self.adapter.job_status(self.job_id)
        self.assertEqual(status["status"], "cancelled")

    def test_cancel_nonexistent_job(self):
        result = self.adapter.cancel_job("nonexistent")
        self.assertFalse(result["ok"])


class TestArtifactDownload(unittest.TestCase):
    """Tests for artifact download."""

    def setUp(self):
        self.adapter = LambdaAdapter(LambdaConfig(api_key="test-key"))
        self.spec = JobSpec(name="test", job_type="testing", command="python test.py")
        self.submit_result = self.adapter.submit_job(self.spec, creator_approved=True)
        self.job_id = self.submit_result["job_id"]

    def test_download_not_completed(self):
        result = self.adapter.download_artifact(self.job_id, "/tmp/output")
        self.assertFalse(result["ok"])
        self.assertIn("not completed", result["error"])

    def test_download_completed_job(self):
        # Mark job as completed
        self.adapter._jobs[self.job_id].status = "completed"
        result = self.adapter.download_artifact(self.job_id, "/tmp/output")
        self.assertTrue(result["ok"])
        self.assertTrue(result["requires_court_review"])

    def test_download_nonexistent_job(self):
        result = self.adapter.download_artifact("nonexistent", "/tmp/output")
        self.assertFalse(result["ok"])


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def test_status_no_secrets(self):
        adapter = LambdaAdapter(LambdaConfig(api_key="super-secret-key"))
        status = adapter.status()
        status_json = json.dumps(status)
        self.assertNotIn("super-secret-key", status_json)

    def test_status_shows_gpus(self):
        adapter = LambdaAdapter(LambdaConfig(api_key="k"))
        status = adapter.status()
        self.assertIn("available_gpus", status)
        self.assertGreater(len(status["available_gpus"]), 0)

    def test_status_not_configured(self):
        adapter = LambdaAdapter(LambdaConfig())
        status = adapter.status()
        self.assertFalse(status["configured"])

    def test_status_configured(self):
        adapter = LambdaAdapter(LambdaConfig(api_key="k"))
        status = adapter.status()
        self.assertTrue(status["configured"])

    def test_status_with_ledger(self):
        ledger = MagicMock()
        adapter = LambdaAdapter(LambdaConfig(api_key="k"), ledger=ledger)
        status = adapter.status()
        self.assertTrue(status["ledger_connected"])


class TestLogging(unittest.TestCase):
    """Tests for evidence ledger logging."""

    def setUp(self):
        self.ledger = MagicMock()
        self.adapter = LambdaAdapter(LambdaConfig(api_key="k"), ledger=self.ledger)

    def test_denied_job_logged(self):
        spec = JobSpec(name="test", job_type="testing")
        self.adapter.submit_job(spec, creator_approved=False)
        self.ledger.append.assert_called_once()
        entry = self.ledger.append.call_args[0][0]
        self.assertEqual(entry["type"], "lambda_job")
        self.assertEqual(entry["status"], "denied")

    def test_approved_job_logged(self):
        spec = JobSpec(name="test", job_type="testing", command="python test.py")
        self.adapter.submit_job(spec, creator_approved=True)
        self.ledger.append.assert_called_once()
        entry = self.ledger.append.call_args[0][0]
        self.assertEqual(entry["status"], "pending")


class TestGPUTypes(unittest.TestCase):
    """Tests for GPU type definitions."""

    def test_gpu_types_have_pricing(self):
        for gpu_type, info in GPU_TYPES.items():
            self.assertIn("price_per_hr", info)
            self.assertGreater(info["price_per_hr"], 0)

    def test_gpu_types_have_vram(self):
        for gpu_type, info in GPU_TYPES.items():
            self.assertIn("vram_gb", info)
            self.assertGreater(info["vram_gb"], 0)

    def test_gpu_types_have_names(self):
        for gpu_type, info in GPU_TYPES.items():
            self.assertIn("name", info)
            self.assertTrue(info["name"])


if __name__ == "__main__":
    unittest.main()
