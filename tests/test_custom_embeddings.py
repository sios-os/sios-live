"""Tests for the custom embedding module.

Tests verify:
- Tokenization
- EmbeddingModel embed (dimension, normalization, empty handling)
- EmbeddingModel save/load round-trip
- EmbeddingTrainer vocabulary building
- EmbeddingTrainer IDF computation
- Training pair generation (positive and negative)
- Full training pipeline
- Retrieval evaluation
- CustomEmbeddingAdapter interface
- Status endpoint
"""
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.custom_embeddings import (
    EmbeddingModel,
    EmbeddingTrainer,
    EmbeddingTrainingPair,
    CustomEmbeddingAdapter,
    _tokenize,
    DEFAULT_DIM,
)


class TestTokenize(unittest.TestCase):
    """Tests for the tokenizer."""

    def test_basic(self):
        tokens = _tokenize("Hello World 123")
        self.assertEqual(tokens, ["hello", "world", "123"])

    def test_punctuation(self):
        tokens = _tokenize("def foo(): return 42!")
        self.assertIn("def", tokens)
        self.assertIn("foo", tokens)
        self.assertIn("return", tokens)
        self.assertIn("42", tokens)

    def test_empty(self):
        self.assertEqual(_tokenize(""), [])

    def test_uppercase(self):
        tokens = _tokenize("PYTHON")
        self.assertEqual(tokens, ["python"])


class TestEmbeddingModel(unittest.TestCase):
    """Tests for EmbeddingModel."""

    def setUp(self):
        self.model = EmbeddingModel(
            model_name="test-embed",
            dimensions=128,
            vocabulary={"python": 0, "code": 1, "function": 2},
            idf_weights={"python": 1.5, "code": 2.0, "function": 1.8},
        )

    def test_embed_correct_dimension(self):
        vec = self.model.embed("python code function")
        self.assertEqual(len(vec), 128)

    def test_embed_normalized(self):
        vec = self.model.embed("python code function")
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_embed_empty_text(self):
        vec = self.model.embed("")
        self.assertEqual(len(vec), 128)
        self.assertTrue(all(v == 0.0 for v in vec))

    def test_embed_different_texts_different_vectors(self):
        vec1 = self.model.embed("python code")
        vec2 = self.model.embed("java database")
        self.assertNotEqual(vec1, vec2)

    def test_embed_similar_texts_similar_vectors(self):
        vec1 = self.model.embed("python function code")
        vec2 = self.model.embed("python code function")
        # Same tokens should produce same vector
        self.assertEqual(vec1, vec2)

    def test_to_dict_and_from_dict(self):
        d = self.model.to_dict()
        m2 = EmbeddingModel.from_dict(d)
        self.assertEqual(m2.model_name, "test-embed")
        self.assertEqual(m2.dimensions, 128)
        self.assertEqual(m2.vocabulary, self.model.vocabulary)

    def test_save_and_load(self):
        tmpdir = tempfile.mkdtemp(prefix="anubis-embed-")
        try:
            result = self.model.save(Path(tmpdir) / "model.json")
            self.assertTrue(result["saved"])
            loaded = EmbeddingModel.load(Path(tmpdir) / "model.json")
            self.assertEqual(loaded.model_name, "test-embed")
            self.assertEqual(loaded.dimensions, 128)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestEmbeddingTrainer(unittest.TestCase):
    """Tests for EmbeddingTrainer."""

    def setUp(self):
        self.trainer = EmbeddingTrainer(dimensions=64, min_doc_freq=1)
        self.documents = [
            "Python is a programming language for data science",
            "Java is a programming language for enterprise applications",
            "Python function definitions use the def keyword",
            "Database connections in Java use JDBC drivers",
            "Machine learning models require training data",
        ]

    def test_build_vocabulary(self):
        vocab, idf = self.trainer._build_vocabulary(self.documents)
        self.assertGreater(len(vocab), 0)
        self.assertIn("python", vocab)
        self.assertIn("java", vocab)

    def test_idf_weights(self):
        vocab, idf = self.trainer._build_vocabulary(self.documents)
        # Terms that appear in more documents should have lower IDF
        self.assertGreater(idf["python"], 0)
        # "programming" appears in 2 docs, "python" in 2 docs
        # IDF should be log(5/2) + 1 for both
        self.assertAlmostEqual(idf["python"], idf["programming"], places=5)

    def test_min_doc_freq_filter(self):
        trainer = EmbeddingTrainer(min_doc_freq=3)
        vocab, _ = trainer._build_vocabulary(self.documents)
        # Only terms appearing in 3+ documents
        for term in vocab:
            count = sum(1 for doc in self.documents if term in _tokenize(doc))
            self.assertGreaterEqual(count, 3)

    def test_generate_training_pairs(self):
        pairs = self.trainer.generate_training_pairs(self.documents)
        self.assertGreater(len(pairs), 0)
        # Should have both positive and negative pairs
        positive = [p for p in pairs if p.label == 1.0]
        negative = [p for p in pairs if p.label == 0.0]
        self.assertGreater(len(positive), 0)
        self.assertGreater(len(negative), 0)

    def test_training_pairs_have_text(self):
        pairs = self.trainer.generate_training_pairs(self.documents)
        for pair in pairs:
            self.assertTrue(pair.text_a)
            self.assertTrue(pair.text_b)

    def test_train(self):
        model = self.trainer.train(self.documents, model_name="test-v1")
        self.assertEqual(model.model_name, "test-v1")
        self.assertEqual(model.dimensions, 64)
        self.assertGreater(len(model.vocabulary), 0)
        self.assertEqual(model.document_count, 5)
        self.assertGreater(model.trained_at, 0)

    def test_train_empty_corpus(self):
        model = self.trainer.train([], model_name="empty")
        self.assertEqual(model.document_count, 0)
        self.assertEqual(len(model.vocabulary), 0)

    def test_evaluate_retrieval(self):
        model = self.trainer.train(self.documents)
        # Use the documents themselves as queries
        result = self.trainer.evaluate_retrieval(
            model, self.documents, self.documents, top_k=3
        )
        self.assertEqual(result["queries"], 5)
        self.assertGreaterEqual(result["hits"], 0)
        self.assertGreaterEqual(result["hit_rate"], 0.0)


class TestCustomEmbeddingAdapter(unittest.TestCase):
    """Tests for CustomEmbeddingAdapter."""

    def setUp(self):
        self.model = EmbeddingModel(
            model_name="anubis-embed-v1",
            dimensions=128,
            vocabulary={"test": 0},
            idf_weights={"test": 1.0},
        )
        self.adapter = CustomEmbeddingAdapter(self.model)

    def test_embed(self):
        vec = self.adapter.embed("test text")
        self.assertEqual(len(vec), 128)

    def test_dimensions(self):
        self.assertEqual(self.adapter.dimensions, 128)

    def test_model_name(self):
        self.assertEqual(self.adapter.model_name, "anubis-embed-v1")

    def test_status(self):
        status = self.adapter.status()
        self.assertEqual(status["model_name"], "anubis-embed-v1")
        self.assertEqual(status["dimensions"], 128)
        self.assertEqual(status["replaces"], "nomic-embed-text")


class TestEmbeddingTrainingPair(unittest.TestCase):
    """Tests for EmbeddingTrainingPair."""

    def test_creation(self):
        pair = EmbeddingTrainingPair("text a", "text b", 1.0)
        self.assertEqual(pair.text_a, "text a")
        self.assertEqual(pair.label, 1.0)

    def test_to_dict(self):
        pair = EmbeddingTrainingPair("a", "b", 0.0)
        d = pair.to_dict()
        self.assertEqual(d["text_a"], "a")
        self.assertEqual(d["label"], 0.0)


if __name__ == "__main__":
    unittest.main()
