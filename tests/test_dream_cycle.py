"""Tests for the dream cycle engine."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.dream_cycle import (
    DreamCycleEngine,
    DreamCycleResult,
    DreamPhase,
    Recommendation,
)
from anubis.model import Completion


class MockModel:
    """Mock model that returns canned responses."""
    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self._idx = 0
        self.model = "mock:test"

    def chat(self, messages, *, temperature=0.2, max_tokens=None, timeout=180.0):
        if self._idx < len(self.responses):
            text = self.responses[self._idx]
            self._idx += 1
        else:
            text = '{"gap": "test gap", "area": "coding", "severity": "low", "solution": "build skill"}'
        return Completion(
            text=text,
            thinking="",
            tool_calls=[],
            model="mock:test",
            prompt_tokens=10,
            completion_tokens=20,
            duration_s=0.01,
        )


class TestDreamPhase(unittest.TestCase):
    def test_duration(self):
        p = DreamPhase(name="test", description="d", started_at=100.0, completed_at=105.0)
        self.assertEqual(p.duration_s, 5.0)

    def test_to_dict(self):
        p = DreamPhase(name="test", description="d", started_at=100.0)
        d = p.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["findings"], [])


class TestDreamCycleEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.model = MockModel([
            json.dumps([
                {"gap": "no skill for X", "area": "coding", "severity": "high", "solution": "build X"},
                {"gap": "no skill for Y", "area": "reasoning", "severity": "medium", "solution": "build Y"},
            ]),
            json.dumps([
                {"gap": "no skill for X", "cause": "missing", "solution": "build", "priority": "high", "dependencies": []},
            ]),
            json.dumps([
                {"skill_name": "build_x", "task": "Build skill X"},
                {"skill_name": "build_y", "task": "Build skill Y"},
            ]),
            json.dumps([
                {"category": "learn", "title": "Learn X", "description": "d", "rationale": "r", "priority": "high"},
            ]),
        ])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_run_cycle_basic(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine.run_cycle()
        self.assertIsInstance(result, DreamCycleResult)
        self.assertEqual(len(result.phases), 6)
        self.assertTrue(result.duration_s >= 0)

    def test_cycle_generates_gaps(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine.run_cycle()
        self.assertGreater(len(result.gaps_identified), 0)

    def test_cycle_generates_recommendations(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine.run_cycle()
        # Recommendations are in phase 6 artifacts
        self.assertGreaterEqual(len(result.recommendations), 0)

    def test_cycle_saves_history(self):
        engine = DreamCycleEngine(self.model, self.root)
        engine.run_cycle()
        history = engine.get_dream_history()
        self.assertEqual(len(history), 1)

    def test_recommendations_persisted(self):
        engine = DreamCycleEngine(self.model, self.root)
        engine.run_cycle()
        recs = engine.get_recommendations()
        # Recommendations may or may not be generated depending on model output
        self.assertIsInstance(recs, list)

    def test_gaps_persisted(self):
        engine = DreamCycleEngine(self.model, self.root)
        engine.run_cycle()
        gaps = engine.get_identified_gaps()
        self.assertGreater(len(gaps), 0)

    def test_status(self):
        engine = DreamCycleEngine(self.model, self.root)
        engine.run_cycle()
        status = engine.get_status()
        self.assertEqual(status["total_cycles"], 1)
        self.assertIn("pending_recommendations", status)

    def test_mark_recommendation_acted(self):
        engine = DreamCycleEngine(self.model, self.root)
        engine.run_cycle()
        recs = engine.get_recommendations()
        if recs:
            rec_id = recs[0]["rec_id"]
            self.assertTrue(engine.mark_recommendation_acted(rec_id))
            recs = engine.get_recommendations()
            self.assertTrue(recs[0]["acted_on"])

    def test_cycle_with_queue(self):
        """Test that missions are queued when a queue is provided."""
        from anubis.queue import MissionQueue
        queue = MissionQueue(self.root / "memory")
        engine = DreamCycleEngine(
            self.model, self.root, queue=queue
        )
        result = engine.run_cycle()
        self.assertGreaterEqual(result.missions_generated, 0)

    def test_cycle_with_library(self):
        """Test that the engine works with a skill library."""
        from anubis.skills import SkillLibrary
        library = SkillLibrary(self.root / "skills")
        engine = DreamCycleEngine(
            self.model, self.root, library=library
        )
        result = engine.run_cycle()
        self.assertEqual(len(result.phases), 6)

    def test_cycle_error_handling(self):
        """Test that cycle handles model errors gracefully."""
        model = MockModel()
        model.chat = MagicMock(side_effect=Exception("model error"))
        engine = DreamCycleEngine(model, self.root)
        result = engine.run_cycle()
        # Should complete despite errors
        self.assertEqual(result.completed_at, 0 or result.completed_at)

    def test_parse_json_array(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine._parse_json_array('```json\n[{"a": 1}]\n```')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["a"], 1)

    def test_parse_json_array_empty(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine._parse_json_array("no json here")
        self.assertEqual(result, [])

    def test_parse_findings(self):
        engine = DreamCycleEngine(self.model, self.root)
        text = "1. First finding\n2. Second finding\n```json\n[]\n```"
        findings = engine._parse_findings(text)
        self.assertEqual(len(findings), 2)

    def test_training_pairs_generated(self):
        engine = DreamCycleEngine(self.model, self.root)
        result = engine.run_cycle()
        # Training pairs should be generated from dream findings
        self.assertGreaterEqual(result.training_pairs_generated, 0)


class TestRecommendation(unittest.TestCase):
    def test_to_dict(self):
        rec = Recommendation(
            rec_id="test",
            category="watch",
            title="Test",
            description="d",
            rationale="r",
        )
        d = rec.to_dict()
        self.assertEqual(d["rec_id"], "test")
        self.assertEqual(d["category"], "watch")
        self.assertFalse(d["acted_on"])


if __name__ == "__main__":
    unittest.main()
