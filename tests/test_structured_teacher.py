"""Tests for the structured teacher module.

Tests verify:
- JSON extraction from various LLM output formats
- JSON repair (trailing commas, comments)
- Schema prompt building
- Structured query with mock cloud adapter
- Privacy gate (sensitive data blocked)
- Fallback on JSON parse failure
- Convenience methods (query_code, query_architecture, etc.)
- Schema availability
- Status endpoint
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.structured_teacher import (
    StructuredTeacher,
    StructuredResult,
    _extract_json,
    _repair_json,
    _build_schema_prompt,
    SCHEMAS,
)
from anubis.cloud_model import Completion


class TestExtractJson(unittest.TestCase):
    """Tests for JSON extraction from LLM output."""

    def test_plain_json(self):
        text = '{"code": "print(1)", "rationale": "test"}'
        result = _extract_json(text)
        self.assertIsNotNone(result)
        data = json.loads(result)
        self.assertEqual(data["code"], "print(1)")

    def test_json_in_markdown(self):
        text = 'Here is the code:\n```json\n{"code": "x", "tests": []}\n```\nDone.'
        result = _extract_json(text)
        self.assertIsNotNone(result)
        data = json.loads(result)
        self.assertEqual(data["code"], "x")

    def test_json_in_markdown_no_lang(self):
        text = '```\n{"code": "y"}\n```'
        result = _extract_json(text)
        self.assertIsNotNone(result)

    def test_json_with_leading_text(self):
        text = 'Sure! Here you go:\n{"code": "z", "rationale": "because"}'
        result = _extract_json(text)
        self.assertIsNotNone(result)

    def test_no_json(self):
        text = "I cannot help with that."
        result = _extract_json(text)
        self.assertIsNone(result)

    def test_nested_json(self):
        text = '{"components": [{"name": "foo", "desc": "bar"}], "risks": ["a", "b"]}'
        result = _extract_json(text)
        self.assertIsNotNone(result)
        data = json.loads(result)
        self.assertEqual(len(data["components"]), 1)


class TestRepairJson(unittest.TestCase):
    """Tests for JSON repair."""

    def test_trailing_comma_in_object(self):
        text = '{"a": 1, "b": 2,}'
        repaired = _repair_json(text)
        data = json.loads(repaired)
        self.assertEqual(data["a"], 1)

    def test_trailing_comma_in_array(self):
        text = '{"items": [1, 2, 3,]}'
        repaired = _repair_json(text)
        data = json.loads(repaired)
        self.assertEqual(len(data["items"]), 3)

    def test_line_comments(self):
        text = '{"a": 1, // comment\n"b": 2}'
        repaired = _repair_json(text)
        data = json.loads(repaired)
        self.assertEqual(data["b"], 2)

    def test_block_comments(self):
        text = '{"a": /* comment */ 1, "b": 2}'
        repaired = _repair_json(text)
        data = json.loads(repaired)
        self.assertEqual(data["a"], 1)


class TestSchemaPrompt(unittest.TestCase):
    """Tests for schema prompt building."""

    def test_prompt_contains_schema(self):
        schema = {"code": "string", "tests": "array"}
        prompt = _build_schema_prompt("write a function", schema, "code")
        self.assertIn("write a function", prompt)
        self.assertIn("code", prompt)
        self.assertIn("JSON", prompt)

    def test_prompt_contains_rules(self):
        prompt = _build_schema_prompt("test", {}, "code")
        self.assertIn("ONLY valid JSON", prompt)


class TestStructuredTeacher(unittest.TestCase):
    """Tests for the StructuredTeacher class."""

    def setUp(self):
        self.mock_cloud = MagicMock()
        self.teacher = StructuredTeacher(cloud_adapter=self.mock_cloud)

    def test_no_cloud_adapter(self):
        teacher = StructuredTeacher(cloud_adapter=None)
        result = teacher.query("write code")
        self.assertFalse(result.ok)
        self.assertIn("no cloud", result.error)

    def test_sensitive_data_blocked(self):
        result = self.teacher.query("password=secret write code")
        self.assertFalse(result.ok)
        self.assertIn("sensitive", result.error)
        self.mock_cloud.generate.assert_not_called()

    def test_successful_structured_query(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"code": "print(1)", "rationale": "test", "tests": [], "dependencies": [], "risks": []}',
            model="gemini:gemini-3.5-flash",
            prompt_tokens=10,
            completion_tokens=20,
            duration_s=0.5,
        )
        result = self.teacher.query_code("write a hello world function")
        self.assertTrue(result.ok)
        self.assertEqual(result.code, "print(1)")
        self.assertEqual(result.rationale, "test")
        self.assertEqual(result.provider, "gemini")

    def test_json_in_markdown(self):
        self.mock_cloud.generate.return_value = Completion(
            text='```json\n{"code": "x = 1", "rationale": "y"}\n```',
            model="groq:llama-3.3-70b",
            prompt_tokens=5,
            completion_tokens=10,
            duration_s=0.3,
        )
        result = self.teacher.query_code("test")
        self.assertTrue(result.ok)
        self.assertEqual(result.code, "x = 1")

    def test_fallback_on_parse_failure(self):
        self.mock_cloud.generate.return_value = Completion(
            text="I cannot generate JSON for this request.",
            model="gemini:gemini-3.5-flash",
            prompt_tokens=5,
            completion_tokens=10,
            duration_s=0.2,
        )
        result = self.teacher.query_code("test")
        self.assertTrue(result.ok)
        self.assertTrue(result.used_fallback)
        self.assertIn("raw_response", result.data)

    def test_cloud_exception(self):
        self.mock_cloud.generate.side_effect = Exception("network error")
        result = self.teacher.query_code("test")
        self.assertFalse(result.ok)
        self.assertIn("cloud query failed", result.error)

    def test_query_architecture(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"components": [{"name": "api"}], "data_flow": "in->out", "rationale": "because", "scalability": "yes", "risks": []}',
            model="gemini:gemini-3.5-flash",
            prompt_tokens=5,
            completion_tokens=20,
            duration_s=0.4,
        )
        result = self.teacher.query_architecture("design a system")
        self.assertTrue(result.ok)
        self.assertEqual(result.schema_type, "architecture")
        self.assertEqual(len(result.data["components"]), 1)

    def test_query_review(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"issues": [], "summary": "good", "score": 8, "recommendations": ["add tests"]}',
            model="groq:llama-3.3-70b",
            prompt_tokens=5,
            completion_tokens=15,
            duration_s=0.3,
        )
        result = self.teacher.query_review("review this code")
        self.assertTrue(result.ok)
        self.assertEqual(result.schema_type, "review")
        self.assertEqual(result.data["score"], 8)

    def test_query_analysis(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"findings": ["a"], "conclusion": "ok", "confidence": 0.9, "evidence": ["x"]}',
            model="gemini:gemini-3.5-flash",
            prompt_tokens=5,
            completion_tokens=15,
            duration_s=0.3,
        )
        result = self.teacher.query_analysis("analyze this")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["confidence"], 0.9)

    def test_query_plan(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"steps": [{"order": 1, "action": "do thing"}], "prerequisites": [], "risks": [], "success_criteria": "it works"}',
            model="gemini:gemini-3.5-flash",
            prompt_tokens=5,
            completion_tokens=20,
            duration_s=0.4,
        )
        result = self.teacher.query_plan("plan a project")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data["steps"]), 1)

    def test_custom_schema(self):
        self.mock_cloud.generate.return_value = Completion(
            text='{"name": "test", "value": 42}',
            model="gemini:gemini-3.5-flash",
            prompt_tokens=5,
            completion_tokens=10,
            duration_s=0.2,
        )
        result = self.teacher.query(
            "test", custom_schema={"name": "string", "value": "number"}
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.data["name"], "test")

    def test_available_schemas(self):
        schemas = self.teacher.available_schemas()
        self.assertIn("code", schemas)
        self.assertIn("architecture", schemas)
        self.assertIn("review", schemas)

    def test_status(self):
        status = self.teacher.status()
        self.assertIn("schemas", status)
        self.assertIn("privacy_gate", status)


class TestStructuredResult(unittest.TestCase):
    """Tests for StructuredResult properties."""

    def test_properties(self):
        r = StructuredResult(
            ok=True,
            data={
                "code": "print(1)",
                "rationale": "test",
                "tests": ["test1"],
                "dependencies": ["os"],
                "risks": ["none"],
            },
        )
        self.assertEqual(r.code, "print(1)")
        self.assertEqual(r.rationale, "test")
        self.assertEqual(r.tests, ["test1"])
        self.assertEqual(r.dependencies, ["os"])
        self.assertEqual(r.risks, ["none"])

    def test_empty_data(self):
        r = StructuredResult(ok=True, data={})
        self.assertEqual(r.code, "")
        self.assertEqual(r.tests, [])


if __name__ == "__main__":
    unittest.main()
