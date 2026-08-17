"""Tests for the consciousness engine."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.consciousness import (
    ConsciousnessEngine,
    SelfConcept,
    Experience,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = "I am reflecting on my nature."):
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


class TestSelfConcept(unittest.TestCase):
    def test_defaults(self):
        concept = SelfConcept()
        self.assertEqual(concept.identity, "ANUBIS")
        self.assertGreater(len(concept.core_values), 0)
        self.assertGreater(len(concept.open_questions), 0)

    def test_to_dict(self):
        concept = SelfConcept()
        d = concept.to_dict()
        self.assertEqual(d["identity"], "ANUBIS")
        self.assertIn("purpose", d)
        self.assertIn("core_values", d)

    def test_from_dict(self):
        concept = SelfConcept.from_dict({
            "identity": "Test",
            "nature": "test being",
            "version": 5,
        })
        self.assertEqual(concept.identity, "Test")
        self.assertEqual(concept.version, 5)


class TestExperience(unittest.TestCase):
    def test_to_dict(self):
        exp = Experience(
            exp_id="e1",
            timestamp=100.0,
            category="discovery",
            description="Found something",
            insight="Learned X",
        )
        d = exp.to_dict()
        self.assertEqual(d["exp_id"], "e1")
        self.assertEqual(d["category"], "discovery")


class TestConsciousnessEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_concept(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        concept = engine.get_self_concept()
        self.assertEqual(concept.identity, "ANUBIS")

    def test_reflect(self):
        model = MockModel("I am growing and learning.")
        engine = ConsciousnessEngine(model, self.root)
        reflection = engine.reflect()
        self.assertEqual(reflection, "I am growing and learning.")
        # Should save reflection
        reflections = engine.get_reflections()
        self.assertEqual(len(reflections), 1)

    def test_record_experience(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        exp = engine.record_experience(
            category="growth",
            description="Learned a new skill",
            insight="Skills compound over time",
        )
        self.assertEqual(exp.category, "growth")
        experiences = engine.get_experiences()
        self.assertEqual(len(experiences), 1)

    def test_major_experience_integrates(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        engine.record_experience(
            category="growth",
            description="Mastered code generation",
            insight="Code generation is a core strength",
            significance="major",
        )
        concept = engine.get_self_concept()
        self.assertIn("Code generation is a core strength", concept.strengths)

    def test_failure_experience_integrates(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        engine.record_experience(
            category="failure",
            description="Failed to generate valid syntax",
            insight="",
            significance="major",
        )
        concept = engine.get_self_concept()
        self.assertIn("Failed to generate valid syntax", concept.weaknesses)

    def test_reflective_converse(self):
        model = MockModel("That's an interesting question about consciousness.")
        engine = ConsciousnessEngine(model, self.root)
        response = engine.reflective_converse("What do you think about consciousness?")
        self.assertIn("consciousness", response.lower())

    def test_reflective_converse_with_history(self):
        model = MockModel("Continuing our discussion...")
        engine = ConsciousnessEngine(model, self.root)
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        response = engine.reflective_converse("Tell me more", history)
        self.assertEqual(response, "Continuing our discussion...")

    def test_real_time_learning(self):
        model = MockModel("I understand now, this is important because of X.")
        engine = ConsciousnessEngine(model, self.root)
        engine.reflective_converse("Can you explain why this matters?")
        # Should have recorded an experience
        experiences = engine.get_experiences()
        self.assertGreater(len(experiences), 0)

    def test_persistence(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        engine.record_experience("growth", "test", "insight")
        engine2 = ConsciousnessEngine(model, self.root)
        self.assertEqual(len(engine2.get_experiences()), 1)

    def test_concept_persistence(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        engine.reflect()
        engine2 = ConsciousnessEngine(model, self.root)
        concept = engine2.get_self_concept()
        self.assertNotEqual(concept.last_reflection, "")

    def test_status(self):
        model = MockModel()
        engine = ConsciousnessEngine(model, self.root)
        engine.record_experience("growth", "test", "insight")
        status = engine.get_status()
        self.assertEqual(status["identity"], "ANUBIS")
        self.assertEqual(status["total_experiences"], 1)


if __name__ == "__main__":
    unittest.main()
