"""Tests for the proactive engagement system."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.proactive import (
    ProactiveEngagement,
    Observation,
    ProactiveMessage,
    CreatorPattern,
    sanitize_content,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = '{"reaction": "ok", "questions": [], "suggestions": []}'):
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


class TestSanitizeContent(unittest.TestCase):
    def test_redacts_api_key(self):
        result = sanitize_content("api_key=abc123secret456")
        self.assertIn("[REDACTED]", result)

    def test_redacts_password(self):
        result = sanitize_content("password=mys3cr3tp@ss")
        self.assertIn("[REDACTED]", result)

    def test_redacts_hex_keys(self):
        result = sanitize_content("key: aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899")
        self.assertIn("[REDACTED]", result)

    def test_redacts_private_key(self):
        result = sanitize_content(
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----"
        )
        self.assertIn("[REDACTED]", result)

    def test_redacts_credit_card(self):
        result = sanitize_content("card: 1234-5678-9012-3456")
        self.assertIn("[REDACTED]", result)

    def test_redacts_ssn(self):
        result = sanitize_content("ssn: 123-45-6789")
        self.assertIn("[REDACTED]", result)

    def test_preserves_normal_text(self):
        text = "The quick brown fox jumps over the lazy dog"
        self.assertEqual(sanitize_content(text), text)

    def test_email_partial_redact(self):
        result = sanitize_content("contact: john@example.com")
        self.assertIn("***@", result)


class TestObservation(unittest.TestCase):
    def test_to_dict(self):
        obs = Observation(obs_id="t1", source="screen", content="test")
        d = obs.to_dict()
        self.assertEqual(d["obs_id"], "t1")
        self.assertEqual(d["source"], "screen")
        self.assertFalse(d["acted_on"])


class TestProactiveEngagement(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        self.assertEqual(eng.engagement_level, "active")

    def test_set_engagement_level(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        self.assertTrue(eng.set_engagement_level("eager"))
        self.assertEqual(eng.engagement_level, "eager")
        self.assertFalse(eng.set_engagement_level("invalid"))

    def test_observe_silent(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root, engagement_level="silent")
        obs = eng.observe("screen", "test content")
        self.assertEqual(obs.source, "screen")
        self.assertEqual(obs.reaction, "")  # no reaction in silent mode

    def test_observe_with_reaction(self):
        model = MockModel('{"reaction": "interesting", "questions": ["what?"], "suggestions": ["help"]}')
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        obs = eng.observe("screen", "test content")
        self.assertEqual(obs.reaction, "interesting")
        self.assertEqual(obs.questions, ["what?"])
        self.assertEqual(obs.suggestions, ["help"])

    def test_observe_sanitizes(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        obs = eng.observe("screen", "password=secret123")
        self.assertIn("[REDACTED]", obs.content)
        self.assertNotIn("secret123", obs.content)

    def test_observe_persists(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        eng.observe("screen", "test")
        obs = eng.get_observations()
        self.assertEqual(len(obs), 1)

    def test_patterns_tracked(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        eng.observe("screen", "working on python programming project")
        patterns = eng.get_patterns()
        self.assertGreater(len(patterns), 0)
        # Should have activity time pattern
        has_time = any(p["pattern_type"] == "activity_time" for p in patterns)
        self.assertTrue(has_time)

    def test_generate_proactive_message(self):
        model = MockModel(json.dumps({
            "message_type": "question",
            "content": "What are you working on?",
            "context": "noticed activity",
            "priority": "medium",
        }))
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        # First need an observation
        eng.observe("screen", "working on code")
        msg = eng.generate_proactive_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.message_type, "question")
        self.assertEqual(msg.content, "What are you working on?")

    def test_generate_proactive_message_silent(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root, engagement_level="silent")
        msg = eng.generate_proactive_message()
        self.assertIsNone(msg)

    def test_generate_proactive_message_empty(self):
        model = MockModel(json.dumps({
            "message_type": "observation",
            "content": "",
            "context": "",
            "priority": "low",
        }))
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        eng.observe("screen", "test")
        msg = eng.generate_proactive_message()
        self.assertIsNone(msg)

    def test_curiosity_question(self):
        model = MockModel('{"reaction": "ok", "questions": ["why does X happen?"], "suggestions": []}')
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        eng.observe("screen", "something confusing")
        question = eng.generate_curiosity_question()
        self.assertIsNotNone(question)
        self.assertEqual(question, "why does X happen?")

    def test_curiosity_silent(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root, engagement_level="silent")
        eng.observe("screen", "test")
        question = eng.generate_curiosity_question()
        self.assertIsNone(question)

    def test_mark_message_delivered(self):
        model = MockModel(json.dumps({
            "message_type": "question",
            "content": "test",
            "context": "c",
            "priority": "low",
        }))
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        eng.observe("screen", "test")
        msg = eng.generate_proactive_message()
        if msg:
            self.assertTrue(eng.mark_message_delivered(msg.msg_id))

    def test_dismiss_message(self):
        model = MockModel(json.dumps({
            "message_type": "question",
            "content": "test",
            "context": "c",
            "priority": "low",
        }))
        eng = ProactiveEngagement(model, self.root, engagement_level="active")
        eng.observe("screen", "test")
        msg = eng.generate_proactive_message()
        if msg:
            self.assertTrue(eng.dismiss_message(msg.msg_id))
            msgs = eng.get_all_messages()
            self.assertTrue(msgs[0]["dismissed"])

    def test_status(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        eng.observe("screen", "test")
        status = eng.get_status()
        self.assertEqual(status["engagement_level"], "active")
        self.assertEqual(status["total_observations"], 1)

    def test_parse_json(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        result = eng._parse_json('```json\n{"a": 1}\n```')
        self.assertEqual(result["a"], 1)

    def test_parse_json_empty(self):
        model = MockModel()
        eng = ProactiveEngagement(model, self.root)
        result = eng._parse_json("no json")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
