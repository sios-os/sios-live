"""Tests for the knowledge distillation module.

Tests verify:
- Training pair extraction from conversations
- Pair classification (coding, reasoning, factual, general)
- Quality scoring
- Queue management (add, load, clear, dedup)
- Export to training dataset
- Distillation stats
- Integration with purge pipeline
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.distillation import (
    KnowledgeDistiller,
    TrainingPair,
    DistillationResult,
)


class TestTrainingPair(unittest.TestCase):
    """Tests for TrainingPair dataclass."""

    def test_creation(self):
        p = TrainingPair(prompt="hello", response="world")
        self.assertEqual(p.prompt, "hello")
        self.assertEqual(p.response, "world")
        self.assertTrue(p.pair_hash)
        self.assertGreater(p.created_at, 0)

    def test_hash_deterministic(self):
        p1 = TrainingPair(prompt="test", response="response")
        p2 = TrainingPair(prompt="test", response="response")
        self.assertEqual(p1.pair_hash, p2.pair_hash)

    def test_hash_differs_for_different_pairs(self):
        p1 = TrainingPair(prompt="test", response="response1")
        p2 = TrainingPair(prompt="test", response="response2")
        self.assertNotEqual(p1.pair_hash, p2.pair_hash)

    def test_to_dict_and_from_dict(self):
        p = TrainingPair(prompt="q", response="a", category="coding", quality_score=0.8)
        d = p.to_dict()
        p2 = TrainingPair.from_dict(d)
        self.assertEqual(p2.prompt, "q")
        self.assertEqual(p2.response, "a")
        self.assertEqual(p2.category, "coding")
        self.assertEqual(p2.quality_score, 0.8)


class TestExtractPairs(unittest.TestCase):
    """Tests for pair extraction from conversation entries."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-distill-")
        self.distiller = KnowledgeDistiller(
            queue_path=Path(self.tmpdir) / "queue.jsonl"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_extract_single_pair(self):
        entries = [
            {"role": "user", "content": "How do I reverse a string in Python?"},
            {"role": "assistant", "content": "Use slicing: s[::-1] reverses a string."},
        ]
        pairs = self.distiller.extract_pairs(entries)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].prompt, "How do I reverse a string in Python?")

    def test_extract_multiple_pairs(self):
        entries = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "How to install it?"},
            {"role": "assistant", "content": "Download from python.org and run installer."},
        ]
        pairs = self.distiller.extract_pairs(entries)
        self.assertEqual(len(pairs), 2)

    def test_skip_short_entries(self):
        entries = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
        ]
        pairs = self.distiller.extract_pairs(entries)
        self.assertEqual(len(pairs), 0)

    def test_skip_non_pair_sequences(self):
        entries = [
            {"role": "assistant", "content": "I am ANUBIS."},
            {"role": "user", "content": "Tell me about Python programming language please"},
        ]
        pairs = self.distiller.extract_pairs(entries)
        self.assertEqual(len(pairs), 0)

    def test_empty_entries(self):
        pairs = self.distiller.extract_pairs([])
        self.assertEqual(pairs, [])


class TestClassification(unittest.TestCase):
    """Tests for pair classification."""

    def setUp(self):
        self.distiller = KnowledgeDistiller()

    def test_coding_classification(self):
        cat = self.distiller._classify_pair(
            "How to write a function?",
            "def foo(): pass"
        )
        self.assertEqual(cat, "coding")

    def test_reasoning_classification(self):
        cat = self.distiller._classify_pair(
            "Why does this happen?",
            "Because the logic step requires analysis."
        )
        self.assertEqual(cat, "reasoning")

    def test_factual_classification(self):
        cat = self.distiller._classify_pair(
            "What is the capital of France?",
            "Paris is the capital of France."
        )
        self.assertEqual(cat, "factual")

    def test_general_classification(self):
        cat = self.distiller._classify_pair(
            "Hello there",
            "Hi, how are you doing today?"
        )
        self.assertEqual(cat, "general")


class TestQualityScoring(unittest.TestCase):
    """Tests for quality scoring."""

    def setUp(self):
        self.distiller = KnowledgeDistiller()

    def test_high_quality_code_response(self):
        score = self.distiller._score_quality(
            "How to write a Python function?",
            "def foo():\n    return 42\n\nThis function returns the answer."
        )
        self.assertGreater(score, 0.5)

    def test_low_quality_short_response(self):
        score = self.distiller._score_quality(
            "hi",
            "ok"
        )
        self.assertLess(score, 0.3)

    def test_medium_quality(self):
        score = self.distiller._score_quality(
            "What is Python?",
            "Python is a high-level programming language."
        )
        self.assertGreater(score, 0.2)


class TestQueueManagement(unittest.TestCase):
    """Tests for queue management."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-distill-q-")
        self.distiller = KnowledgeDistiller(
            queue_path=Path(self.tmpdir) / "queue.jsonl"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_queue_and_load(self):
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.5),
            TrainingPair(prompt="q2", response="r2", quality_score=0.6),
        ]
        queued = self.distiller.queue_pairs(pairs)
        self.assertEqual(queued, 2)
        loaded = self.distiller.load_queue()
        self.assertEqual(len(loaded), 2)

    def test_dedup(self):
        pair = TrainingPair(prompt="q", response="r", quality_score=0.5)
        self.distiller.queue_pairs([pair])
        queued = self.distiller.queue_pairs([pair])
        self.assertEqual(queued, 0)

    def test_min_quality_filter(self):
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.1),
            TrainingPair(prompt="q2", response="r2", quality_score=0.5),
        ]
        queued = self.distiller.queue_pairs(pairs, min_quality=0.3)
        self.assertEqual(queued, 1)

    def test_clear_queue(self):
        pairs = [TrainingPair(prompt="q", response="r", quality_score=0.5)]
        self.distiller.queue_pairs(pairs)
        count = self.distiller.clear_queue()
        self.assertEqual(count, 1)
        self.assertEqual(len(self.distiller.load_queue()), 0)


class TestDistill(unittest.TestCase):
    """Tests for the full distill pipeline."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-distill-full-")
        self.distiller = KnowledgeDistiller(
            queue_path=Path(self.tmpdir) / "queue.jsonl"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_distill_full_pipeline(self):
        entries = [
            {"role": "user", "content": "How do I write a Python function?"},
            {"role": "assistant", "content": "def foo():\n    return 42\n\nThis defines a function."},
            {"role": "user", "content": "What is a class?"},
            {"role": "assistant", "content": "A class is a blueprint for objects in OOP."},
        ]
        result = self.distiller.distill(entries)
        self.assertEqual(result.pairs_extracted, 2)
        self.assertGreater(result.pairs_queued, 0)
        self.assertIn("coding", result.categories)

    def test_distill_empty(self):
        result = self.distiller.distill([])
        self.assertEqual(result.pairs_extracted, 0)

    def test_distill_stats(self):
        entries = [
            {"role": "user", "content": "How to code in Python?"},
            {"role": "assistant", "content": "def foo():\n    pass\n\nUse def keyword."},
        ]
        self.distiller.distill(entries)
        stats = self.distiller.stats()
        self.assertGreater(stats["queued_pairs"], 0)


class TestExport(unittest.TestCase):
    """Tests for training data export."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-distill-exp-")
        self.distiller = KnowledgeDistiller(
            queue_path=Path(self.tmpdir) / "queue.jsonl"
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_all(self):
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.5, category="coding"),
            TrainingPair(prompt="q2", response="r2", quality_score=0.7, category="general"),
        ]
        self.distiller.queue_pairs(pairs)
        result = self.distiller.export_training_data(
            Path(self.tmpdir) / "train.jsonl"
        )
        self.assertEqual(result["exported"], 2)

    def test_export_by_category(self):
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.5, category="coding"),
            TrainingPair(prompt="q2", response="r2", quality_score=0.7, category="general"),
        ]
        self.distiller.queue_pairs(pairs)
        result = self.distiller.export_training_data(
            Path(self.tmpdir) / "train.jsonl", category="coding"
        )
        self.assertEqual(result["exported"], 1)

    def test_export_min_quality(self):
        pairs = [
            TrainingPair(prompt="q1", response="r1", quality_score=0.3),
            TrainingPair(prompt="q2", response="r2", quality_score=0.8),
        ]
        self.distiller.queue_pairs(pairs)
        result = self.distiller.export_training_data(
            Path(self.tmpdir) / "train.jsonl", min_quality=0.5
        )
        self.assertEqual(result["exported"], 1)


if __name__ == "__main__":
    unittest.main()
