"""Tests for the Vast.ai adapter and automated training."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.vast_adapter import VastConfig, VastOffer, VastInstance, VastAdapter
from anubis.training_manager import AutomatedTrainingManager, TrainingJob


class TestVastConfig(unittest.TestCase):
    def test_config_from_file(self):
        config = VastConfig.from_file()
        self.assertTrue(config.is_configured)
        self.assertIn("vast.ai", config.endpoint.lower() + " console.vast.ai")

    def test_config_not_configured(self):
        config = VastConfig(api_key="")
        self.assertFalse(config.is_configured)


class TestVastAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = VastAdapter(VastConfig(api_key="test_key"))

    def test_is_configured(self):
        self.assertTrue(self.adapter.is_configured)

    def test_not_configured(self):
        adapter = VastAdapter(VastConfig(api_key=""))
        self.assertFalse(adapter.is_configured)

    def test_rent_without_approval(self):
        result = self.adapter.rent_instance(123, creator_approved=False, approval_token="")
        self.assertIn("error", result)
        self.assertIn("approval", result["error"].lower())

    def test_rent_with_wrong_token(self):
        result = self.adapter.rent_instance(123, creator_approved=True, approval_token="wrong")
        self.assertIn("error", result)

    def test_search_and_rent_without_approval(self):
        result = self.adapter.search_and_rent(creator_approved=False, approval_token="")
        self.assertIn("error", result)
        self.assertIn("approval", result["error"].lower())

    def test_get_status_overview_not_configured(self):
        adapter = VastAdapter(VastConfig(api_key=""))
        result = adapter.get_status_overview()
        self.assertFalse(result["configured"])


class TestAutomatedTrainingManagerVast(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = AutomatedTrainingManager(self.tmpdir, ledger=MagicMock())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_vast_search_not_configured(self):
        # Override with unconfigured adapter
        from anubis.vast_adapter import VastAdapter, VastConfig
        self.manager.vast_adapter = VastAdapter(VastConfig(api_key=""))
        result = self.manager.vast_search()
        self.assertIn("error", result)

    def test_vast_rent_without_approval(self):
        result = self.manager.vast_rent_and_train(
            creator_approved=False, approval_token=""
        )
        self.assertIn("error", result)
        self.assertIn("approval", result["error"].lower())

    def test_vast_full_automation_without_approval(self):
        result = self.manager.vast_full_automation(
            creator_approved=False, approval_token=""
        )
        self.assertIn("error", result)

    def test_vast_monitor_no_job(self):
        result = self.manager.vast_monitor("nonexistent")
        self.assertIn("error", result)

    def test_vast_download_no_job(self):
        result = self.manager.vast_download_model("nonexistent")
        self.assertIn("error", result)

    def test_vast_destroy_no_job(self):
        result = self.manager.vast_destroy_instance("nonexistent")
        self.assertIn("error", result)

    def test_status_overview_includes_vast(self):
        result = self.manager.get_status_overview()
        self.assertIn("vast_configured", result)

    def test_job_persistence_with_ssh(self):
        job = TrainingJob(
            job_id="test_ssh",
            ssh_host="1.2.3.4",
            ssh_port=22,
            status="running",
        )
        self.manager._save_job(job)
        loaded = self.manager._load_job("test_ssh")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.ssh_host, "1.2.3.4")
        self.assertEqual(loaded.ssh_port, 22)


class TestVastDataClasses(unittest.TestCase):
    def test_vast_offer(self):
        offer = VastOffer(id=123, gpu_name="H100 NVL", gpu_ram=94, dph_total=2.624)
        self.assertEqual(offer.id, 123)
        self.assertEqual(offer.gpu_name, "H100 NVL")
        self.assertEqual(offer.gpu_ram, 94)

    def test_vast_instance(self):
        inst = VastInstance(id=456, status="running", ssh_host="1.2.3.4", ssh_port=22)
        self.assertEqual(inst.id, 456)
        self.assertEqual(inst.status, "running")
        self.assertEqual(inst.ssh_host, "1.2.3.4")


if __name__ == "__main__":
    unittest.main()
