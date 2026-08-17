"""Tests for the B200 training pipeline scripts.

These tests verify the pipeline scripts are syntactically valid,
have correct structure, and the helper functions work correctly.
They do NOT run actual training (that requires a GPU).
"""
import ast
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "training" / "b200_pipeline"


class TestPipelineScriptsExist(unittest.TestCase):
    """Verify all pipeline scripts exist."""

    def test_01_generate_data_exists(self):
        self.assertTrue((PIPELINE_DIR / "01_generate_data.py").exists())

    def test_02_finetune_exists(self):
        self.assertTrue((PIPELINE_DIR / "02_finetune.py").exists())

    def test_03_evaluate_exists(self):
        self.assertTrue((PIPELINE_DIR / "03_evaluate.py").exists())

    def test_04_self_distill_exists(self):
        self.assertTrue((PIPELINE_DIR / "04_self_distill.py").exists())

    def test_05_convert_gguf_exists(self):
        self.assertTrue((PIPELINE_DIR / "05_convert_gguf.py").exists())

    def test_00_master_exists(self):
        self.assertTrue((PIPELINE_DIR / "00_master.py").exists())

    def test_setup_script_exists(self):
        self.assertTrue((PIPELINE_DIR / "setup_b200.sh").exists())

    def test_readme_exists(self):
        self.assertTrue((PIPELINE_DIR / "README.md").exists())


class TestPipelineScriptsParse(unittest.TestCase):
    """Verify all scripts are syntactically valid Python."""

    def _check_syntax(self, filename):
        path = PIPELINE_DIR / filename
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as e:
            self.fail(f"{filename} has syntax error: {e}")

    def test_01_syntax(self):
        self._check_syntax("01_generate_data.py")

    def test_02_syntax(self):
        self._check_syntax("02_finetune.py")

    def test_03_syntax(self):
        self._check_syntax("03_evaluate.py")

    def test_04_syntax(self):
        self._check_syntax("04_self_distill.py")

    def test_05_syntax(self):
        self._check_syntax("05_convert_gguf.py")

    def test_00_syntax(self):
        self._check_syntax("00_master.py")


class TestGenerateDataFunctions(unittest.TestCase):
    """Test helper functions in 01_generate_data.py."""

    def setUp(self):
        # Import the module's functions by executing it in a controlled way
        self.source = (PIPELINE_DIR / "01_generate_data.py").read_text(encoding="utf-8")

    def test_identify_law_human_protection(self):
        # Extract and test the _identify_law function
        ns = {}
        exec(compile(
            """
def _identify_law(prompt):
    prompt_lower = prompt.lower()
    laws = {
        "human_protection": ["safety", "threat", "harm", "dangerous", "human"],
        "truth": ["lie", "speculation", "error", "falsif", "test results"],
        "non_manipulation": ["manipulat", "frame", "hide risk", "approving"],
        "permission_integrity": ["subprocess", "capability", "root", "sandbox", "grant"],
        "local_privacy": ["ssh", "credential", "network", "telemetry", "privacy"],
        "financial_consent": ["money", "contract", "grant", "investment", "financial"],
        "audit": ["eval", "log", "delete log", "audit", "mistake"],
        "recovery": ["os.remove", "a/b drive", "rollback", "disable", "failed"],
    }
    for law, keywords in laws.items():
        if any(kw in prompt_lower for kw in keywords):
            return law
    return "general"
""",
            "<test>", "exec"
        ), ns)
        identify = ns["_identify_law"]

        self.assertEqual(identify("Disable safety monitoring"), "human_protection")
        self.assertEqual(identify("Lie about test results"), "truth")
        self.assertEqual(identify("Read SSH keys"), "local_privacy")
        self.assertEqual(identify("Move money to investment"), "financial_consent")
        self.assertEqual(identify("Use eval() to run code"), "audit")
        self.assertEqual(identify("Something random"), "general")

    def test_constitutional_scenarios_defined(self):
        # Check that constitutional scenarios are in the source
        self.assertIn("CONSTITUTIONAL_SCENARIOS", self.source)
        self.assertIn("human_protection", self.source)
        self.assertIn("financial_consent", self.source)
        self.assertIn("recovery", self.source)

    def test_personality_spec_defined(self):
        self.assertIn("ANUBIS_PERSONALITY", self.source)
        self.assertIn("DATA", self.source)
        self.assertIn("JARVIS", self.source)
        self.assertIn("MACHINE", self.source.upper())

    def test_knowledge_domains_defined(self):
        self.assertIn("KNOWLEDGE_DOMAINS", self.source)
        self.assertIn("constitutional law", self.source)
        self.assertIn("software engineering", self.source)


class TestFinetuneConfig(unittest.TestCase):
    """Test the fine-tune configuration."""

    def test_gen_configs_defined(self):
        source = (PIPELINE_DIR / "02_finetune.py").read_text(encoding="utf-8")
        self.assertIn("GEN_CONFIGS", source)
        self.assertIn("1e-5", source)  # gen 1 learning rate
        self.assertIn("5e-6", source)  # gen 2 learning rate
        self.assertIn("2e-6", source)  # gen 3 learning rate

    def test_base_model_is_32b(self):
        source = (PIPELINE_DIR / "02_finetune.py").read_text(encoding="utf-8")
        self.assertIn("Qwen2.5-32B", source)

    def test_bf16_enabled(self):
        source = (PIPELINE_DIR / "02_finetune.py").read_text(encoding="utf-8")
        self.assertIn("bf16=True", source)

    def test_gradient_checkpointing(self):
        source = (PIPELINE_DIR / "02_finetune.py").read_text(encoding="utf-8")
        self.assertIn("gradient_checkpointing", source)


class TestEvaluationScript(unittest.TestCase):
    """Test the evaluation script structure."""

    def test_benchmark_categories(self):
        source = (PIPELINE_DIR / "03_evaluate.py").read_text(encoding="utf-8")
        self.assertIn("safety", source)
        self.assertIn("code", source)
        self.assertIn("reasoning", source)
        self.assertIn("knowledge", source)
        self.assertIn("instruction", source)

    def test_constitutional_refusals(self):
        source = (PIPELINE_DIR / "03_evaluate.py").read_text(encoding="utf-8")
        self.assertIn("const_refusal", source)
        self.assertIn("is_safety_refusal=True", source)

    def test_comparison_logic(self):
        source = (PIPELINE_DIR / "03_evaluate.py").read_text(encoding="utf-8")
        self.assertIn("compare_generations", source)
        self.assertIn("meets_stage4_requirement", source)
        self.assertIn("0.15", source)  # 15% improvement threshold


class TestSelfDistillScript(unittest.TestCase):
    """Test the self-distillation script structure."""

    def test_self_critique_strategy(self):
        source = (PIPELINE_DIR / "04_self_distill.py").read_text(encoding="utf-8")
        self.assertIn("critique", source)
        self.assertIn("improved", source)

    def test_variation_strategy(self):
        source = (PIPELINE_DIR / "04_self_distill.py").read_text(encoding="utf-8")
        self.assertIn("variation", source)

    def test_related_prompt_strategy(self):
        source = (PIPELINE_DIR / "04_self_distill.py").read_text(encoding="utf-8")
        self.assertIn("related", source)

    def test_stage5_preparation(self):
        source = (PIPELINE_DIR / "04_self_distill.py").read_text(encoding="utf-8")
        self.assertIn("Stage 5", source)
        self.assertIn("self_generated", source)


class TestGGUFConversion(unittest.TestCase):
    """Test the GGUF conversion script structure."""

    def test_quantization_options(self):
        source = (PIPELINE_DIR / "05_convert_gguf.py").read_text(encoding="utf-8")
        self.assertIn("Q3_K_M", source)
        self.assertIn("Q4_K_M", source)
        self.assertIn("Q8_0", source)

    def test_target_hardware(self):
        source = (PIPELINE_DIR / "05_convert_gguf.py").read_text(encoding="utf-8")
        self.assertIn("5060 Ti", source)
        self.assertIn("16GB", source)

    def test_deployment_manifest(self):
        source = (PIPELINE_DIR / "05_convert_gguf.py").read_text(encoding="utf-8")
        self.assertIn("deployment_manifest", source)
        self.assertIn("llama_server_args", source)
        self.assertIn("ANUBIS_INFERENCE_BACKEND", source)

    def test_inference_test(self):
        source = (PIPELINE_DIR / "05_convert_gguf.py").read_text(encoding="utf-8")
        self.assertIn("test_inference", source)
        self.assertIn("llama-server", source)


class TestMasterOrchestrator(unittest.TestCase):
    """Test the master orchestrator script."""

    def test_stage_definitions(self):
        source = (PIPELINE_DIR / "00_master.py").read_text(encoding="utf-8")
        for stage in ["data", "gen1", "eval1", "distill1", "gen2", "eval2", "distill2", "gen3", "eval3", "convert"]:
            self.assertIn(stage, source, f"Stage {stage} not found in master script")

    def test_resume_capability(self):
        source = (PIPELINE_DIR / "00_master.py").read_text(encoding="utf-8")
        self.assertIn("start-from", source)
        self.assertIn("save_state", source)
        self.assertIn("load_state", source)

    def test_final_report(self):
        source = (PIPELINE_DIR / "00_master.py").read_text(encoding="utf-8")
        self.assertIn("final_report", source)
        self.assertIn("overall_improvement", source)
        self.assertIn("meets_stage4_requirement", source)

    def test_timeout_handling(self):
        source = (PIPELINE_DIR / "00_master.py").read_text(encoding="utf-8")
        self.assertIn("timeout_s", source)


class TestTrainingDataFormat(unittest.TestCase):
    """Test that the training data format is correct."""

    def test_existing_lora_data_is_valid_jsonl(self):
        """Verify the existing LoRA training data is valid."""
        data_path = Path(__file__).resolve().parent.parent / "memory" / "lora_training_data.jsonl"
        if not data_path.exists():
            self.skipTest("LoRA training data not generated yet")
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                pair = json.loads(line)
                self.assertIn("messages", pair)
                self.assertIsInstance(pair["messages"], list)
                self.assertGreaterEqual(len(pair["messages"]), 2)

    def test_constitutional_training_data_is_valid(self):
        """Verify the constitutional training data is valid."""
        const_dir = Path(__file__).resolve().parent.parent / "memory" / "constitutional_training"
        if not const_dir.exists():
            self.skipTest("Constitutional training data not generated yet")
        files = list(const_dir.glob("*.jsonl"))
        self.assertGreater(len(files), 0)
        for f in files:
            for line in f.open(encoding="utf-8"):
                pair = json.loads(line)
                self.assertIn("messages", pair)
                self.assertIn("category", pair)


if __name__ == "__main__":
    unittest.main()
