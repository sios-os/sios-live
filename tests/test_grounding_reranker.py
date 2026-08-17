"""Tests for grounding with vector index and reranker integration.

Tests verify:
- Keyword retrieval still works (backward compat)
- Reranker improves result ordering
- Semantic search with vector index
- Over-fetch and rerank pipeline
- Reranker failure falls back gracefully
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.grounding import KnowledgeGrounding
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.reranker import LocalReranker


class TestGroundingReranker(unittest.TestCase):
    """Tests that grounding uses the reranker correctly."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-grounding-")
        self.registry = Registry(self.tmpdir)
        self.kb = KnowledgeBase(Path(self.tmpdir) / "knowledge", self.registry)
        # Add documents via quarantine → promote
        docs = [
            ("Python String Reversal",
             "Python function to reverse a string using slicing and iteration."),
            ("Java Database Connection",
             "Java class for establishing JDBC database connections with pooling."),
            ("Python Data Analysis",
             "Python script using pandas for data analysis and visualization."),
            ("JavaScript Callbacks",
             "JavaScript callback function examples for async programming."),
        ]
        for title, content in docs:
            doc_id = self.kb.ingest_to_quarantine(title=title, content=content)
            self.kb.promote_from_quarantine(doc_id)

    def test_keyword_retrieval_with_reranker(self):
        g = KnowledgeGrounding(self.kb)
        context = g.ground("python string reversal", max_docs=2)
        self.assertIn("Python String Reversal", context)

    def test_reranker_improves_ordering(self):
        g = KnowledgeGrounding(self.kb)
        docs = g._retrieve_docs("python code", "", limit=2)
        # Should return 2 docs
        self.assertEqual(len(docs), 2)
        # Python docs should be favored
        titles = [d.title for d in docs]
        self.assertTrue(
            any("Python" in t for t in titles),
            f"Expected Python docs in results: {titles}"
        )

    def test_reranker_failure_falls_back(self):
        """If reranker raises, grounding should still return results."""
        bad_reranker = MagicMock()
        bad_reranker.rerank.side_effect = Exception("reranker broken")
        g = KnowledgeGrounding(self.kb, reranker=bad_reranker)
        docs = g._retrieve_docs("python", "", limit=2)
        # Should still return docs (fallback to original order)
        self.assertGreater(len(docs), 0)

    def test_empty_query(self):
        g = KnowledgeGrounding(self.kb)
        context = g.ground("", max_docs=2)
        # Should not crash, may return empty or minimal context
        # Just verify no exception

    def test_ground_with_citations(self):
        g = KnowledgeGrounding(self.kb)
        result = g.ground_with_citations("python", max_docs=2)
        self.assertIn("context", result)
        self.assertIn("citations", result)
        self.assertIsInstance(result["citations"], list)

    def test_stats(self):
        g = KnowledgeGrounding(self.kb)
        stats = g.stats()
        self.assertIn("library_size", stats)
        self.assertIn("semantic_enabled", stats)


class TestSemanticIntegration(unittest.TestCase):
    """Tests for semantic search integration with vector index."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sem-int-")

    def test_semantic_index_rebuild(self):
        from anubis.semantic import SemanticIndex
        idx = SemanticIndex(cache_path=Path(self.tmpdir) / "emb.json")
        # Manually add some embeddings
        idx._embeddings = {
            "d1": [1.0, 0.0, 0.0] * 256,  # 768-dim
            "d2": [0.0, 1.0, 0.0] * 256,
        }
        idx._doc_meta = {
            "d1": {"title": "Doc 1", "specialty_id": "gen", "snippet": "hello"},
            "d2": {"title": "Doc 2", "specialty_id": "gen", "snippet": "world"},
        }
        idx._loaded = True
        idx._rebuild_vindex()
        stats = idx.stats()
        self.assertTrue(stats["vector_index_active"])
        self.assertEqual(stats["indexed_docs"], 2)

    def test_semantic_search_uses_vindex(self):
        from anubis.semantic import SemanticIndex
        idx = SemanticIndex(cache_path=Path(self.tmpdir) / "emb.json")
        idx._embeddings = {
            "d1": [1.0, 0.0, 0.0] * 256,
            "d2": [0.0, 1.0, 0.0] * 256,
            "d3": [0.9, 0.1, 0.0] * 256,
        }
        idx._doc_meta = {
            "d1": {"title": "D1", "specialty_id": "", "snippet": ""},
            "d2": {"title": "D2", "specialty_id": "", "snippet": ""},
            "d3": {"title": "D3", "specialty_id": "", "snippet": ""},
        }
        idx._loaded = True
        idx._rebuild_vindex()

        # Mock the _embed function to return a query vector
        with unittest.mock.patch("anubis.semantic._embed", return_value=[1.0, 0.0, 0.0] * 256):
            results = idx.search("test query", top_k=2)
        self.assertEqual(len(results), 2)
        # d1 should be most similar (identical vector)
        self.assertEqual(results[0].doc_id, "d1")


if __name__ == "__main__":
    unittest.main()
