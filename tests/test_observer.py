"""Tests for the observer engine."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.observer import (
    ObserverEngine,
    Observation,
    Correlation,
    RelevantOutput,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = '{"pattern": "test", "confidence": 0.7, "prediction": "test", "prediction_type": "insight"}'):
        self.response = response
        self.model = "mock:test"

    def chat(self, messages, *, temperature=0.2, max_tokens=None, timeout=180.0):
        return Completion(
            text=self.response,
            thinking="",
            tool_calls=[],
            model="mock:test",
            prompt_tokens=10,
            completion_tokens=20,
            duration_s=0.01,
        )


class TestObservation(unittest.TestCase):
    def test_to_dict(self):
        obs = Observation(obs_id="o1", source="system", event_type="alert", content="test")
        d = obs.to_dict()
        self.assertEqual(d["obs_id"], "o1")
        self.assertEqual(d["source"], "system")


class TestCorrelation(unittest.TestCase):
    def test_to_dict(self):
        corr = Correlation(
            corr_id="c1",
            observation_ids=["o1", "o2"],
            pattern="test pattern",
            confidence=0.8,
            prediction="test prediction",
            prediction_type="threat",
        )
        d = corr.to_dict()
        self.assertEqual(d["corr_id"], "c1")
        self.assertEqual(d["confidence"], 0.8)


class TestRelevantOutput(unittest.TestCase):
    def test_to_dict(self):
        out = RelevantOutput(
            output_id="r1",
            category="threat",
            title="Test",
            description="d",
        )
        d = out.to_dict()
        self.assertEqual(d["output_id"], "r1")
        self.assertFalse(d["acknowledged"])


class TestObserverEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Create some files to monitor
        (self.root / "config").mkdir(parents=True, exist_ok=True)
        (self.root / "config" / "test.json").write_text('{"test": true}', encoding="utf-8")
        (self.root / "anubis").mkdir(parents=True, exist_ok=True)
        (self.root / "anubis" / "test.py").write_text("# test", encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        obs = ObserverEngine(self.root)
        self.assertEqual(obs.sensitivity, "normal")

    def test_monitor_basic(self):
        obs = ObserverEngine(self.root)
        observations = obs.monitor()
        # First run establishes baseline, may not have changes
        self.assertIsInstance(observations, list)

    def test_monitor_detects_file_change(self):
        obs = ObserverEngine(self.root)
        # First run to establish baseline
        obs.monitor()
        # Change a file
        (self.root / "config" / "test.json").write_text('{"test": false}', encoding="utf-8")
        observations = obs.monitor()
        # Should detect the change
        file_obs = [o for o in observations if o.source == "file"]
        self.assertGreater(len(file_obs), 0)

    def test_monitor_detects_file_deletion(self):
        obs = ObserverEngine(self.root)
        obs.monitor()
        (self.root / "config" / "test.json").unlink()
        observations = obs.monitor()
        delete_obs = [o for o in observations if "deleted" in o.content]
        self.assertGreater(len(delete_obs), 0)

    def test_correlation(self):
        model = MockModel()
        obs = ObserverEngine(self.root, model=model)
        # Create some observations to correlate
        obs1 = Observation(obs_id="o1", source="system", event_type="alert", content="CPU high")
        obs2 = Observation(obs_id="o2", source="file", event_type="change", content="config changed")
        correlations = obs._correlate([obs1, obs2])
        # Should find file_change_with_system_alert pattern
        self.assertGreater(len(correlations), 0)

    def test_relevant_output_generation(self):
        obs = ObserverEngine(self.root, sensitivity="high")
        corr = Correlation(
            corr_id="c1",
            observation_ids=["o1"],
            pattern="test pattern",
            confidence=0.8,
            prediction="test prediction",
            prediction_type="threat",
        )
        outputs = obs._generate_relevant_outputs(corr)
        self.assertGreater(len(outputs), 0)
        self.assertEqual(outputs[0].category, "threat")

    def test_relevance_filter_low_confidence(self):
        obs = ObserverEngine(self.root, sensitivity="low")
        corr = Correlation(
            corr_id="c1",
            observation_ids=["o1"],
            pattern="test",
            confidence=0.5,  # below low threshold of 0.8
            prediction="test",
            prediction_type="insight",
        )
        outputs = obs._generate_relevant_outputs(corr)
        self.assertEqual(len(outputs), 0)

    def test_sensitivity_levels(self):
        obs = ObserverEngine(self.root)
        self.assertTrue(obs.set_sensitivity("paranoid"))
        self.assertEqual(obs.sensitivity, "paranoid")
        self.assertFalse(obs.set_sensitivity("invalid"))

    def test_get_observations(self):
        obs = ObserverEngine(self.root)
        obs.monitor()
        observations = obs.get_observations()
        self.assertIsInstance(observations, list)

    def test_get_correlations(self):
        obs = ObserverEngine(self.root)
        correlations = obs.get_correlations()
        self.assertIsInstance(correlations, list)

    def test_relevant_outputs_persistence(self):
        obs = ObserverEngine(self.root, sensitivity="high")
        corr = Correlation(
            corr_id="c1",
            observation_ids=["o1"],
            pattern="test",
            confidence=0.9,
            prediction="test",
            prediction_type="threat",
        )
        outputs = obs._generate_relevant_outputs(corr)
        # Reload
        obs2 = ObserverEngine(self.root, sensitivity="high")
        loaded = obs2.get_relevant_outputs()
        self.assertGreater(len(loaded), 0)

    def test_acknowledge_output(self):
        obs = ObserverEngine(self.root, sensitivity="high")
        corr = Correlation(
            corr_id="c1",
            observation_ids=["o1"],
            pattern="test",
            confidence=0.9,
            prediction="test",
            prediction_type="threat",
        )
        outputs = obs._generate_relevant_outputs(corr)
        if outputs:
            self.assertTrue(obs.acknowledge_output(outputs[0].output_id))

    def test_status(self):
        obs = ObserverEngine(self.root)
        status = obs.get_status()
        self.assertEqual(status["sensitivity"], "normal")
        self.assertIn("total_observations", status)

    def test_model_correlation(self):
        model = MockModel('{"pattern": "connected events", "confidence": 0.7, "prediction": "something", "prediction_type": "insight"}')
        obs = ObserverEngine(self.root, model=model)
        obs1 = Observation(obs_id="o1", source="system", event_type="alert", content="CPU high")
        obs2 = Observation(obs_id="o2", source="file", event_type="change", content="config changed")
        corr = obs._model_correlate([obs1, obs2])
        self.assertIsNotNone(corr)
        self.assertEqual(corr.pattern, "connected events")

    def test_file_hash_baseline(self):
        obs = ObserverEngine(self.root)
        obs.monitor()
        # File hashes should be established
        self.assertGreater(len(obs._file_hashes), 0)


if __name__ == "__main__":
    unittest.main()
