"""Tests for the automated training manager."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.training_manager import (
    AutomatedTrainingManager, TrainingJob,
)


class TestAutomatedTrainingManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = AutomatedTrainingManager(self.tmpdir, ledger=MagicMock())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_prepare_h100_nvl(self):
        result = self.manager.prepare(
            gpu_type="nvidia_h100_nvl",
            runtime_hours=24.0,
        )
        self.assertTrue(result["status"] == "prepared")
        self.assertEqual(result["gpu_type"], "nvidia_h100_nvl")
        self.assertAlmostEqual(result["estimated_cost"], 40.42, places=1)
        self.assertTrue(result["requires_creator_approval"])

    def test_prepare_b200(self):
        result = self.manager.prepare(
            gpu_type="nvidia_b200_sxm6",
            runtime_hours=8.0,
        )
        self.assertTrue(result["status"] == "prepared")
        self.assertAlmostEqual(result["estimated_cost"], 53.52, places=1)

    def test_prepare_unknown_gpu(self):
        result = self.manager.prepare(gpu_type="unknown_gpu")
        self.assertIn("error", result)

    def test_submit_without_approval(self):
        prep = self.manager.prepare()
        result = self.manager.submit(
            prep["job_id"], creator_approved=False, approval_token=""
        )
        self.assertIn("error", result)
        self.assertIn("approval", result["error"].lower())

    def test_submit_with_wrong_token(self):
        prep = self.manager.prepare()
        result = self.manager.submit(
            prep["job_id"], creator_approved=True, approval_token="wrong"
        )
        self.assertIn("error", result)

    def test_submit_nonexistent_job(self):
        result = self.manager.submit("nonexistent", creator_approved=True, approval_token="creator-approved")
        self.assertIn("error", result)

    def test_status_no_jobs(self):
        result = self.manager.get_status()
        self.assertIn("error", result)

    def test_list_jobs_empty(self):
        result = self.manager.get_status_overview()
        self.assertEqual(result["total_jobs"], 0)

    def test_list_jobs_after_prepare(self):
        self.manager.prepare()
        self.manager.prepare()
        result = self.manager.get_status_overview()
        self.assertEqual(result["total_jobs"], 2)

    def test_cancel_nonexistent(self):
        result = self.manager.cancel("nonexistent")
        self.assertIn("error", result)

    def test_download_not_completed(self):
        # Create a job manually
        job = TrainingJob(job_id="test", status="running")
        self.manager._save_job(job)
        result = self.manager.download_model("test")
        self.assertIn("error", result)

    def test_deploy_not_downloaded(self):
        job = TrainingJob(job_id="test", status="completed")
        self.manager._save_job(job)
        result = self.manager.deploy_model("test")
        # Should try to download first, which will fail since no instance
        self.assertIn("error", result)

    def test_training_job_to_dict(self):
        job = TrainingJob(job_id="test", gpu_type="nvidia_b200_sxm6", status="running")
        d = job.to_dict()
        self.assertEqual(d["job_id"], "test")
        self.assertEqual(d["gpu_type"], "nvidia_b200_sxm6")
        self.assertEqual(d["status"], "running")

    def test_job_persistence(self):
        job = TrainingJob(job_id="persist_test", status="running")
        self.manager._save_job(job)
        loaded = self.manager._load_job("persist_test")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.job_id, "persist_test")
        self.assertEqual(loaded.status, "running")

    def test_b200_in_gpu_types(self):
        from anubis.cloud_training import GPU_TYPES
        self.assertIn("nvidia_b200_sxm6", GPU_TYPES)
        self.assertEqual(GPU_TYPES["nvidia_b200_sxm6"]["vram_gb"], 180)

    def test_h100_nvl_in_gpu_types(self):
        from anubis.cloud_training import GPU_TYPES
        self.assertIn("nvidia_h100_nvl", GPU_TYPES)
        self.assertEqual(GPU_TYPES["nvidia_h100_nvl"]["vram_gb"], 94)

    def test_h100_sxm_in_gpu_types(self):
        from anubis.cloud_training import GPU_TYPES
        self.assertIn("nvidia_h100_sxm", GPU_TYPES)
        self.assertEqual(GPU_TYPES["nvidia_h100_sxm"]["vram_gb"], 80)


if __name__ == "__main__":
    unittest.main()
