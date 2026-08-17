"""Tests for the knowledge bootstrapping system."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.knowledge_bootstrap import (
    KnowledgeBootstrapper,
    BootstrapResult,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = '["What is X?", "How does X work?"]'):
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


class TestBootstrapResult(unittest.TestCase):
    def test_defaults(self):
        result = BootstrapResult()
        self.assertEqual(result.total_documents, 0)
        self.assertEqual(result.pairs_generated, 0)

    def test_duration(self):
        result = BootstrapResult(started_at=100.0, completed_at=105.0)
        self.assertEqual(result.duration_s, 5.0)

    def test_to_dict(self):
        result = BootstrapResult(total_documents=10, pairs_generated=30)
        d = result.to_dict()
        self.assertEqual(d["total_documents"], 10)
        self.assertEqual(d["pairs_generated"], 30)


class TestKnowledgeBootstrapper(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Create test knowledge documents
        knowledge_dir = self.root / "knowledge" / "computing"
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        (knowledge_dir / "python_basics.md").write_text(
            "# Python Basics\n\nPython is a programming language.\n\n"
            "## Variables\n\n- int: integers\n- str: strings\n- float: decimals\n",
            encoding="utf-8",
        )

        (knowledge_dir / "data_structures.md").write_text(
            "# Data Structures\n\nCommon data structures include:\n\n"
            "- Lists: ordered, mutable\n- Dicts: key-value pairs\n- Sets: unique items\n\n"
            "```python\nmy_list = [1, 2, 3]\n```",
            encoding="utf-8",
        )

        # Another domain
        math_dir = self.root / "knowledge" / "mathematics"
        math_dir.mkdir(parents=True, exist_ok=True)
        (math_dir / "algebra.md").write_text(
            "# Algebra\n\nAlgebra deals with symbols and rules.\n\n"
            "## Equations\n\n- Linear: ax + b = 0\n- Quadratic: ax^2 + bx + c = 0\n",
            encoding="utf-8",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_bootstrap_no_knowledge_dir(self):
        import shutil
        shutil.rmtree(self.root / "knowledge", ignore_errors=True)
        boot = KnowledgeBootstrapper(self.root)
        result = boot.bootstrap()
        self.assertEqual(result.total_documents, 0)
        self.assertGreater(len(result.errors), 0)

    def test_bootstrap_finds_documents(self):
        boot = KnowledgeBootstrapper(self.root)
        result = boot.bootstrap()
        self.assertGreater(result.total_documents, 0)

    def test_bootstrap_generates_pairs(self):
        boot = KnowledgeBootstrapper(self.root)
        result = boot.bootstrap()
        self.assertGreater(result.pairs_generated, 0)

    def test_bootstrap_writes_to_queue(self):
        boot = KnowledgeBootstrapper(self.root)
        boot.bootstrap()
        queue_path = self.root / "distillation_queue.jsonl"
        self.assertTrue(queue_path.exists())
        lines = queue_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreater(len(lines), 0)
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            self.assertIn("prompt", data)
            self.assertIn("response", data)

    def test_bootstrap_categories(self):
        boot = KnowledgeBootstrapper(self.root)
        result = boot.bootstrap()
        self.assertGreater(len(result.pairs_by_category), 0)

    def test_bootstrap_strategies(self):
        boot = KnowledgeBootstrapper(self.root)
        result = boot.bootstrap()
        self.assertIn("title_to_content", result.pairs_by_strategy)

    def test_bootstrap_with_model(self):
        model = MockModel()
        boot = KnowledgeBootstrapper(self.root, model=model)
        result = boot.bootstrap()
        self.assertGreater(result.pairs_generated, 0)

    def test_bootstrap_max_pairs(self):
        boot = KnowledgeBootstrapper(self.root, max_total_pairs=2)
        result = boot.bootstrap()
        self.assertLessEqual(result.pairs_generated, 2)

    def test_bootstrap_max_per_doc(self):
        boot = KnowledgeBootstrapper(self.root, max_pairs_per_doc=1)
        result = boot.bootstrap()
        # Each doc should produce at most 1 pair
        self.assertGreater(result.pairs_generated, 0)

    def test_bootstrap_idempotent(self):
        """Running bootstrap twice should not duplicate pairs."""
        boot = KnowledgeBootstrapper(self.root)
        result1 = boot.bootstrap()
        result2 = boot.bootstrap()
        # Second run should produce 0 new pairs (all duplicates)
        self.assertEqual(result2.pairs_generated, 0)

    def test_extract_summary(self):
        boot = KnowledgeBootstrapper(self.root)
        content = "# Title\n\nFirst paragraph here.\nMore text.\n\nSecond paragraph."
        summary = boot._extract_summary(content)
        self.assertIn("First paragraph", summary)

    def test_extract_code_blocks(self):
        boot = KnowledgeBootstrapper(self.root)
        content = "Text\n```python\ncode here\n```\nMore text"
        blocks = boot._extract_code_blocks(content)
        self.assertEqual(len(blocks), 1)
        self.assertIn("code here", blocks[0])

    def test_map_category(self):
        boot = KnowledgeBootstrapper(self.root)
        self.assertEqual(boot._map_category("computing"), "coding")
        self.assertEqual(boot._map_category("mathematics"), "reasoning")
        self.assertEqual(boot._map_category("history"), "knowledge")

    def test_generate_reasoning_pair(self):
        boot = KnowledgeBootstrapper(self.root)
        content = "# Test\n\n- Item 1\n- Item 2\n- Item 3\n- Item 4"
        pair = boot._generate_reasoning_pair("Test", content, "general")
        self.assertIsNotNone(pair)
        self.assertEqual(pair["category"], "reasoning")

    def test_generate_reasoning_pair_no_lists(self):
        boot = KnowledgeBootstrapper(self.root)
        content = "Just some text without lists."
        pair = boot._generate_reasoning_pair("Test", content, "general")
        self.assertIsNone(pair)


if __name__ == "__main__":
    unittest.main()
