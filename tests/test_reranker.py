"""Tests for the reranker module.

Tests verify:
- Local BM25 reranker (scoring, ranking, top_k)
- Cloud reranker (with mock, privacy fallback, parse errors)
- Hybrid reranker (combining local + cloud)
- Convenience function
- Edge cases (empty, single candidate)
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.reranker import (
    LocalReranker,
    CloudReranker,
    HybridReranker,
    RerankResult,
    rerank,
    _tokenize,
    _bm25_score,
)


class TestTokenizer(unittest.TestCase):
    """Tests for the tokenizer."""

    def test_simple(self):
        self.assertEqual(_tokenize("hello world"), ["hello", "world"])

    def test_mixed_case(self):
        self.assertEqual(_tokenize("Hello WORLD"), ["hello", "world"])

    def test_punctuation(self):
        self.assertEqual(_tokenize("hello, world!"), ["hello", "world"])

    def test_empty(self):
        self.assertEqual(_tokenize(""), [])

    def test_numbers(self):
        self.assertEqual(_tokenize("test 123"), ["test", "123"])


class TestBM25(unittest.TestCase):
    """Tests for BM25 scoring."""

    def test_exact_match(self):
        score = _bm25_score(
            ["python"], ["python", "code"],
            {"python": 1, "code": 1}, 2, 2.0,
        )
        self.assertGreater(score, 0)

    def test_no_match(self):
        score = _bm25_score(
            ["java"], ["python", "code"],
            {"python": 1, "code": 1}, 2, 2.0,
        )
        self.assertEqual(score, 0.0)

    def test_empty_query(self):
        score = _bm25_score([], ["python"], {}, 1, 1.0)
        self.assertEqual(score, 0.0)

    def test_empty_doc(self):
        score = _bm25_score(["python"], [], {"python": 1}, 1, 0.0)
        self.assertEqual(score, 0.0)


class TestLocalReranker(unittest.TestCase):
    """Tests for the local BM25 reranker."""

    def setUp(self):
        self.reranker = LocalReranker()
        self.candidates = [
            {"id": "c1", "content": "Python function to reverse a string"},
            {"id": "c2", "content": "Java class for database connection"},
            {"id": "c3", "content": "Python script for data analysis"},
            {"id": "c4", "content": "JavaScript callback example"},
        ]

    def test_rerank_returns_results(self):
        results = self.reranker.rerank("python code", self.candidates, top_k=3)
        self.assertEqual(len(results), 3)

    def test_rerank_ranks_relevant_first(self):
        results = self.reranker.rerank("python", self.candidates, top_k=4)
        # c1 and c3 both contain "python"
        top_ids = [r.id for r in results[:2]]
        self.assertIn("c1", top_ids)
        self.assertIn("c3", top_ids)

    def test_rerank_empty_candidates(self):
        results = self.reranker.rerank("test", [], top_k=5)
        self.assertEqual(results, [])

    def test_rerank_single_candidate(self):
        results = self.reranker.rerank("python", [self.candidates[0]], top_k=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "c1")

    def test_rerank_top_k_larger_than_candidates(self):
        results = self.reranker.rerank("python", self.candidates, top_k=10)
        self.assertEqual(len(results), 4)

    def test_rerank_preserves_original_rank(self):
        results = self.reranker.rerank("python", self.candidates, top_k=4)
        # Original ranks should be 0, 1, 2, 3 (in some order)
        original_ranks = {r.original_rank for r in results}
        self.assertEqual(original_ranks, {0, 1, 2, 3})

    def test_rerank_assigns_new_ranks(self):
        results = self.reranker.rerank("python", self.candidates, top_k=4)
        # Reranked ranks should be 0, 1, 2, 3
        reranked_ranks = sorted(r.reranked_rank for r in results)
        self.assertEqual(reranked_ranks, [0, 1, 2, 3])

    def test_rerank_content_preserved(self):
        results = self.reranker.rerank("python", self.candidates, top_k=1)
        # Content should match one of the candidates
        all_contents = [c["content"] for c in self.candidates]
        self.assertIn(results[0].content, all_contents)


class TestCloudReranker(unittest.TestCase):
    """Tests for the cloud teacher reranker."""

    def setUp(self):
        self.candidates = [
            {"id": "c1", "content": "Python function to reverse a string"},
            {"id": "c2", "content": "Java class for database connection"},
            {"id": "c3", "content": "Python script for data analysis"},
        ]

    def test_no_cloud_adapter_uses_local(self):
        reranker = CloudReranker(cloud_adapter=None)
        results = reranker.rerank("python code", self.candidates, top_k=2)
        self.assertEqual(len(results), 2)

    @patch("anubis.reranker._check_sensitive_data", return_value=None)
    def test_cloud_success(self, mock_privacy):
        mock_cloud = MagicMock()
        mock_cloud.generate.return_value = MagicMock(text="[0.9, 0.2, 0.8]")
        reranker = CloudReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank("python code", self.candidates, top_k=3)
        self.assertEqual(len(results), 3)
        # c1 should be highest (0.9)
        self.assertEqual(results[0].id, "c1")
        self.assertAlmostEqual(results[0].score, 0.9)

    def test_cloud_sensitive_falls_back_to_local(self):
        mock_cloud = MagicMock()
        reranker = CloudReranker(cloud_adapter=mock_cloud)
        # Query with sensitive data
        results = reranker.rerank(
            "password=secret python", self.candidates, top_k=2
        )
        # Should not have called cloud
        mock_cloud.generate.assert_not_called()
        self.assertEqual(len(results), 2)

    @patch("anubis.reranker._check_sensitive_data", return_value=None)
    def test_cloud_parse_failure_falls_back(self, mock_privacy):
        mock_cloud = MagicMock()
        mock_cloud.generate.return_value = MagicMock(text="I can't score these")
        reranker = CloudReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank("python code", self.candidates, top_k=2)
        # Should fall back to local
        self.assertEqual(len(results), 2)

    @patch("anubis.reranker._check_sensitive_data", return_value=None)
    def test_cloud_exception_falls_back(self, mock_privacy):
        mock_cloud = MagicMock()
        mock_cloud.generate.side_effect = Exception("network error")
        reranker = CloudReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank("python code", self.candidates, top_k=2)
        self.assertEqual(len(results), 2)

    @patch("anubis.reranker._check_sensitive_data", return_value=None)
    def test_cloud_wrong_count_falls_back(self, mock_privacy):
        mock_cloud = MagicMock()
        # Return wrong number of scores
        mock_cloud.generate.return_value = MagicMock(text="[0.9, 0.2]")
        reranker = CloudReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank("python code", self.candidates, top_k=3)
        # Should fall back to local (3 results)
        self.assertEqual(len(results), 3)


class TestHybridReranker(unittest.TestCase):
    """Tests for the hybrid reranker."""

    def setUp(self):
        self.candidates = [
            {"id": "c1", "content": "Python function to reverse a string"},
            {"id": "c2", "content": "Java class for database connection"},
            {"id": "c3", "content": "Python script for data analysis"},
        ]

    def test_hybrid_no_cloud(self):
        reranker = HybridReranker(cloud_adapter=None)
        results = reranker.rerank("python", self.candidates, top_k=2)
        self.assertEqual(len(results), 2)

    @patch("anubis.reranker._check_sensitive_data", return_value=None)
    def test_hybrid_with_cloud(self, mock_privacy):
        mock_cloud = MagicMock()
        mock_cloud.generate.return_value = MagicMock(text="[0.9, 0.1, 0.8]")
        reranker = HybridReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank("python", self.candidates, top_k=3)
        self.assertEqual(len(results), 3)
        # c1 should be top (both local and cloud favor it)
        self.assertEqual(results[0].id, "c1")

    def test_hybrid_sensitive_falls_back(self):
        mock_cloud = MagicMock()
        reranker = HybridReranker(cloud_adapter=mock_cloud)
        results = reranker.rerank(
            "password=secret python", self.candidates, top_k=2
        )
        mock_cloud.generate.assert_not_called()
        self.assertEqual(len(results), 2)


class TestConvenienceFunction(unittest.TestCase):
    """Tests for the rerank convenience function."""

    def setUp(self):
        self.candidates = [
            {"id": "c1", "content": "Python code"},
            {"id": "c2", "content": "Java code"},
        ]

    def test_local_strategy(self):
        results = rerank("python", self.candidates, top_k=2, strategy="local")
        self.assertEqual(len(results), 2)

    def test_cloud_strategy_no_adapter(self):
        results = rerank("python", self.candidates, top_k=2, strategy="cloud")
        self.assertEqual(len(results), 2)

    def test_hybrid_strategy(self):
        results = rerank("python", self.candidates, top_k=2, strategy="hybrid")
        self.assertEqual(len(results), 2)

    def test_unknown_strategy_defaults_hybrid(self):
        results = rerank("python", self.candidates, top_k=2, strategy="unknown")
        self.assertEqual(len(results), 2)

    def test_empty_candidates(self):
        results = rerank("python", [], top_k=5, strategy="local")
        self.assertEqual(results, [])


class TestRerankResult(unittest.TestCase):
    """Tests for RerankResult dataclass."""

    def test_default_metadata(self):
        r = RerankResult(id="x", score=0.5, original_rank=0, reranked_rank=0)
        self.assertEqual(r.metadata, {})

    def test_with_metadata(self):
        r = RerankResult(
            id="x", score=0.5, original_rank=0, reranked_rank=0,
            metadata={"source": "test"},
        )
        self.assertEqual(r.metadata["source"], "test")


if __name__ == "__main__":
    unittest.main()
