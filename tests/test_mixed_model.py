"""Tests for the mixed model training strategy."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.mixed_model import (
    MixedModelStrategy,
    ModelGeneration,
    StageProgress,
    STAGES,
    STAGE_DESCRIPTIONS,
)


class TestStages(unittest.TestCase):
    def test_six_stages(self):
        self.assertEqual(len(STAGES), 6)
        self.assertEqual(STAGES[1], "distillation")
        self.assertEqual(STAGES[6], "full_sovereignty")

    def test_descriptions_exist(self):
        for stage in STAGES:
            self.assertIn(stage, STAGE_DESCRIPTIONS)


class TestModelGeneration(unittest.TestCase):
    def test_to_dict(self):
        gen = ModelGeneration(
            gen_id="g1",
            version="0.1",
            stage=2,
            base_model="qwen2.5-coder:7b",
        )
        d = gen.to_dict()
        self.assertEqual(d["gen_id"], "g1")
        self.assertEqual(d["version"], "0.1")
        self.assertEqual(d["stage"], 2)

    def test_from_dict(self):
        gen = ModelGeneration.from_dict({
            "gen_id": "g2",
            "version": "0.2",
            "stage": 3,
            "base_model": "test",
        })
        self.assertEqual(gen.gen_id, "g2")
        self.assertEqual(gen.stage, 3)


class TestStageProgress(unittest.TestCase):
    def test_progress(self):
        p = StageProgress(stage=1, requirements_total=4, requirements_met=2)
        self.assertEqual(p.progress_pct, 50.0)
        self.assertFalse(p.is_complete)

    def test_complete(self):
        p = StageProgress(stage=1, requirements_total=4, requirements_met=4)
        self.assertTrue(p.is_complete)
        self.assertEqual(p.progress_pct, 100.0)

    def test_zero_requirements(self):
        p = StageProgress(stage=1)
        self.assertEqual(p.progress_pct, 0.0)
        self.assertFalse(p.is_complete)


class TestMixedModelStrategy(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_initial_stage(self):
        strategy = MixedModelStrategy(self.root)
        self.assertEqual(strategy.get_current_stage(), 1)

    def test_stage_info(self):
        strategy = MixedModelStrategy(self.root)
        info = strategy.get_stage_info()
        self.assertEqual(info["current_stage"], 1)
        self.assertEqual(info["stage_name"], "distillation")
        self.assertIn("requirements", info)

    def test_record_generation(self):
        strategy = MixedModelStrategy(self.root)
        gen = ModelGeneration(
            gen_id="g1",
            version="0.1",
            stage=2,
            base_model="test",
            overall_score=0.4,
        )
        strategy.record_generation(gen)
        gens = strategy.get_generations()
        self.assertEqual(len(gens), 1)
        # Stage should advance
        self.assertEqual(strategy.get_current_stage(), 2)

    def test_check_advancement_stage1(self):
        strategy = MixedModelStrategy(self.root)
        result = strategy.check_advancement({
            "min_training_pairs": 500,
            "min_teachers": 2,
            "min_categories": 3,
        })
        self.assertTrue(result["can_advance"])
        self.assertEqual(result["next_stage"], 2)

    def test_check_advancement_insufficient(self):
        strategy = MixedModelStrategy(self.root)
        result = strategy.check_advancement({
            "min_training_pairs": 100,  # need 500
            "min_teachers": 2,
            "min_categories": 3,
        })
        self.assertFalse(result["can_advance"])
        self.assertGreater(len(result["missing"]), 0)

    def test_advance_stage(self):
        strategy = MixedModelStrategy(self.root)
        result = strategy.advance_stage()
        self.assertEqual(result["advanced_to"], 2)
        self.assertEqual(strategy.get_current_stage(), 2)

    def test_advance_max_stage(self):
        strategy = MixedModelStrategy(self.root)
        for _ in range(6):
            strategy.advance_stage()
        result = strategy.advance_stage()
        self.assertIn("error", result)

    def test_teacher_dependency(self):
        strategy = MixedModelStrategy(self.root)
        dep = strategy.get_teacher_dependency()
        self.assertEqual(dep["current_stage"], 1)
        self.assertEqual(dep["teacher_dependency"], 1.0)
        self.assertEqual(dep["self_sovereignty"], 0.0)

    def test_teacher_dependency_stage3(self):
        strategy = MixedModelStrategy(self.root)
        strategy.advance_stage()  # stage 2
        strategy.advance_stage()  # stage 3
        dep = strategy.get_teacher_dependency()
        self.assertEqual(dep["teacher_dependency"], 0.5)

    def test_teacher_dependency_stage6(self):
        strategy = MixedModelStrategy(self.root)
        for _ in range(5):
            strategy.advance_stage()
        dep = strategy.get_teacher_dependency()
        self.assertEqual(dep["teacher_dependency"], 0.0)
        self.assertEqual(dep["self_sovereignty"], 1.0)

    def test_update_progress(self):
        strategy = MixedModelStrategy(self.root)
        result = strategy.update_progress(1, requirements_met=2, requirements_total=4)
        self.assertEqual(result["requirements_met"], 2)
        self.assertEqual(result["requirements_total"], 4)

    def test_status(self):
        strategy = MixedModelStrategy(self.root)
        status = strategy.get_status()
        self.assertEqual(status["current_stage"], 1)
        self.assertIn("stage_info", status)
        self.assertIn("teacher_dependency", status)

    def test_persistence(self):
        strategy = MixedModelStrategy(self.root)
        strategy.advance_stage()
        strategy2 = MixedModelStrategy(self.root)
        self.assertEqual(strategy2.get_current_stage(), 2)


if __name__ == "__main__":
    unittest.main()
