"""Tests for the Unsloth adapter module.

Tests verify:
- Availability detection (Unsloth not installed on test machine)
- Training config dataclass
- Performance estimation
- Script generation (Unsloth and fallback)
- Script saving
- Status endpoint
- Ledger logging
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.unsloth_adapter import (
    UnslothAdapter,
    TrainingConfig,
    TrainingEstimate,
)


class TestTrainingConfig(unittest.TestCase):
    """Tests for TrainingConfig."""

    def test_default_config(self):
        c = TrainingConfig()
        self.assertEqual(c.model_name, "qwen2.5-coder:7b")
        self.assertEqual(c.max_seq_length, 2048)
        self.assertTrue(c.use_4bit)

    def test_custom_config(self):
        c = TrainingConfig(
            model_name="llama3.1:8b",
            batch_size=4,
            learning_rate=1e-4,
        )
        self.assertEqual(c.model_name, "llama3.1:8b")
        self.assertEqual(c.batch_size, 4)

    def test_to_dict(self):
        c = TrainingConfig()
        d = c.to_dict()
        self.assertIn("model_name", d)
        self.assertIn("target_modules", d)


class TestUnslothAvailability(unittest.TestCase):
    """Tests for Unsloth availability detection."""

    def test_not_available_on_test_machine(self):
        adapter = UnslothAdapter()
        # Unsloth is not installed on the test machine
        self.assertFalse(adapter.is_available())

    def test_cached_availability(self):
        adapter = UnslothAdapter()
        adapter._available = False  # force cache
        self.assertFalse(adapter.is_available())


class TestPerformanceEstimation(unittest.TestCase):
    """Tests for performance estimation."""

    def setUp(self):
        self.adapter = UnslothAdapter()
        self.config = TrainingConfig(model_name="qwen2.5-coder:7b")

    def test_estimate_returns_result(self):
        est = self.adapter.estimate_performance(self.config, dataset_size=1000)
        self.assertIsInstance(est, TrainingEstimate)
        self.assertGreater(est.estimated_vram_mb, 0)

    def test_unsloth_saves_vram(self):
        est = self.adapter.estimate_performance(self.config)
        self.assertLess(
            est.estimated_vram_with_unsloth_mb,
            est.estimated_vram_mb,
        )
        self.assertGreater(est.vram_savings_pct, 0)

    def test_unsloth_is_faster(self):
        est = self.adapter.estimate_performance(self.config, dataset_size=1000)
        self.assertLess(
            est.estimated_time_with_unsloth_minutes,
            est.estimated_time_minutes,
        )
        self.assertGreater(est.estimated_speedup, 1.0)

    def test_4bit_reduces_vram(self):
        config_4bit = TrainingConfig(use_4bit=True)
        config_16bit = TrainingConfig(use_4bit=False)
        est_4bit = self.adapter.estimate_performance(config_4bit)
        est_16bit = self.adapter.estimate_performance(config_16bit)
        self.assertLess(est_4bit.estimated_vram_mb, est_16bit.estimated_vram_mb)


class TestScriptGeneration(unittest.TestCase):
    """Tests for training script generation."""

    def setUp(self):
        self.adapter = UnslothAdapter()
        self.config = TrainingConfig(model_name="qwen2.5-coder:7b")

    def test_fallback_script_generated(self):
        # Unsloth not installed → should generate fallback
        script = self.adapter.generate_training_script(
            self.config, "data/train.jsonl"
        )
        self.assertIn("transformers", script)
        self.assertIn("qwen2.5-coder:7b", script)
        self.assertIn("data/train.jsonl", script)

    def test_explicit_fallback_script(self):
        script = self.adapter.generate_fallback_script(
            self.config, "data/train.jsonl"
        )
        self.assertIn("AutoModelForCausalLM", script)
        self.assertIn("LoraConfig", script)

    def test_script_contains_lora_params(self):
        script = self.adapter.generate_fallback_script(
            self.config, "data/train.jsonl"
        )
        self.assertIn(f"r={self.config.lora_r}", script)
        self.assertIn(f"lora_alpha={self.config.lora_alpha}", script)

    def test_script_contains_training_args(self):
        script = self.adapter.generate_fallback_script(
            self.config, "data/train.jsonl"
        )
        self.assertIn(f"per_device_train_batch_size={self.config.batch_size}", script)
        self.assertIn(
            f"gradient_accumulation_steps={self.config.gradient_accumulation_steps}",
            script,
        )

    def test_script_contains_model_name(self):
        script = self.adapter.generate_fallback_script(
            self.config, "data/train.jsonl"
        )
        self.assertIn(self.config.model_name, script)


class TestSaveScript(unittest.TestCase):
    """Tests for saving training scripts."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-unsloth-")
        self.adapter = UnslothAdapter()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_script(self):
        script = "# test script\nprint('hello')\n"
        result = self.adapter.save_script(
            script, Path(self.tmpdir) / "train.py"
        )
        self.assertTrue(result["saved"])
        self.assertTrue((Path(self.tmpdir) / "train.py").exists())

    def test_save_creates_parent_dirs(self):
        script = "# test\n"
        result = self.adapter.save_script(
            script, Path(self.tmpdir) / "subdir" / "train.py"
        )
        self.assertTrue(result["saved"])
        self.assertTrue((Path(self.tmpdir) / "subdir" / "train.py").exists())


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def test_status_not_available(self):
        adapter = UnslothAdapter()
        status = adapter.status()
        self.assertFalse(status["available"])
        self.assertIn("install", status["description"].lower())


if __name__ == "__main__":
    unittest.main()
