"""Tests for the in-process vector index.

Tests verify:
- Insert and search
- Cosine and dot product metrics
- Batch insert
- Remove entries
- Rebuild after purge
- Persistence (save/load)
- Filtering in search
- Dimension mismatch handling
- Empty index handling
- Statistics
"""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.vector_index import VectorIndex, VectorEntry, _cosine_similarity, _dot_product


class TestSimilarityFunctions(unittest.TestCase):
    """Tests for similarity functions."""

    def test_cosine_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(_cosine_similarity(v, v), 1.0)

    def test_cosine_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        self.assertAlmostEqual(_cosine_similarity(a, b), 0.0)

    def test_cosine_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        self.assertAlmostEqual(_cosine_similarity(a, b), -1.0)

    def test_cosine_zero_vector(self):
        self.assertEqual(_cosine_similarity([0, 0], [1, 0]), 0.0)

    def test_dot_product(self):
        self.assertEqual(_dot_product([1, 2, 3], [4, 5, 6]), 32)


class TestInsertAndSearch(unittest.TestCase):
    """Tests for insert and search operations."""

    def setUp(self):
        self.idx = VectorIndex(dim=3, max_connections=4, ef_construction=10, ef_search=10)

    def test_empty_index_search(self):
        results = self.idx.search([1, 0, 0], k=5)
        self.assertEqual(results, [])

    def test_insert_single(self):
        entry = VectorEntry(id="e1", vector=[1.0, 0.0, 0.0])
        self.idx.insert(entry)
        self.assertEqual(len(self.idx), 1)

    def test_search_single(self):
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        results = self.idx.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "e1")
        self.assertAlmostEqual(results[0][1], 1.0)

    def test_search_multiple(self):
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        self.idx.insert(VectorEntry(id="e2", vector=[0.0, 1.0, 0.0]))
        self.idx.insert(VectorEntry(id="e3", vector=[0.0, 0.0, 1.0]))
        results = self.idx.search([1.0, 0.1, 0.0], k=2)
        self.assertEqual(len(results), 2)
        # e1 should be most similar
        self.assertEqual(results[0][0], "e1")

    def test_search_returns_entry(self):
        self.idx.insert(VectorEntry(
            id="e1", vector=[1.0, 0.0, 0.0],
            metadata={"text": "hello"},
        ))
        results = self.idx.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(results[0][2].metadata["text"], "hello")

    def test_search_increments_access_count(self):
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        self.idx.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(self.idx.get("e1").access_count, 1)
        self.idx.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(self.idx.get("e1").access_count, 2)

    def test_search_k_larger_than_index(self):
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        results = self.idx.search([1.0, 0.0, 0.0], k=10)
        self.assertEqual(len(results), 1)

    def test_dimension_mismatch_insert(self):
        with self.assertRaises(ValueError):
            self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0]))

    def test_dimension_mismatch_search(self):
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        with self.assertRaises(ValueError):
            self.idx.search([1.0, 0.0], k=1)


class TestBatchInsert(unittest.TestCase):
    """Tests for batch insertion."""

    def setUp(self):
        self.idx = VectorIndex(dim=3)

    def test_batch_insert(self):
        entries = [
            VectorEntry(id=f"e{i}", vector=[float(i), 0.0, 0.0])
            for i in range(10)
        ]
        count = self.idx.insert_batch(entries)
        self.assertEqual(count, 10)
        self.assertEqual(len(self.idx), 10)

    def test_batch_insert_with_bad_dimensions(self):
        entries = [
            VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]),
            VectorEntry(id="e2", vector=[1.0, 0.0]),  # wrong dim
            VectorEntry(id="e3", vector=[1.0, 0.0, 0.0]),
        ]
        count = self.idx.insert_batch(entries)
        self.assertEqual(count, 2)


class TestRemove(unittest.TestCase):
    """Tests for entry removal."""

    def setUp(self):
        self.idx = VectorIndex(dim=3)
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        self.idx.insert(VectorEntry(id="e2", vector=[0.0, 1.0, 0.0]))

    def test_remove_existing(self):
        self.assertTrue(self.idx.remove("e1"))
        self.assertIsNone(self.idx.get("e1"))
        self.assertEqual(len(self.idx), 1)

    def test_remove_nonexistent(self):
        self.assertFalse(self.idx.remove("nonexistent"))

    def test_search_after_remove(self):
        self.idx.remove("e1")
        results = self.idx.search([1.0, 0.0, 0.0], k=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "e2")


class TestRebuild(unittest.TestCase):
    """Tests for index rebuild."""

    def setUp(self):
        self.idx = VectorIndex(dim=3, max_connections=4)
        for i in range(20):
            self.idx.insert(VectorEntry(
                id=f"e{i}",
                vector=[float(i) / 20, float(i % 3) / 3, float(i % 5) / 5],
            ))

    def test_rebuild_preserves_entries(self):
        count_before = len(self.idx)
        result = self.idx.rebuild()
        self.assertTrue(result["rebuilt"])
        self.assertEqual(len(self.idx), count_before)

    def test_rebuild_maintains_search(self):
        # Search before rebuild
        results_before = self.idx.search([0.5, 0.5, 0.5], k=5)
        self.idx.rebuild()
        results_after = self.idx.search([0.5, 0.5, 0.5], k=5)
        self.assertEqual(len(results_after), 5)
        # The top result should likely be the same
        self.assertEqual(results_before[0][0], results_after[0][0])

    def test_rebuild_empty_index(self):
        idx = VectorIndex(dim=3)
        result = idx.rebuild()
        self.assertTrue(result["rebuilt"])
        self.assertEqual(result["count"], 0)

    def test_rebuild_after_remove(self):
        # Remove several entries (simulating purge)
        for i in range(10):
            self.idx.remove(f"e{i}")
        self.assertEqual(len(self.idx), 10)
        # Rebuild should work
        result = self.idx.rebuild()
        self.assertEqual(result["count"], 10)
        # Search should still work
        results = self.idx.search([0.5, 0.5, 0.5], k=5)
        self.assertEqual(len(results), 5)


class TestPersistence(unittest.TestCase):
    """Tests for save/load."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-vector-idx-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        idx = VectorIndex(dim=3)
        idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0], metadata={"text": "hello"}))
        idx.insert(VectorEntry(id="e2", vector=[0.0, 1.0, 0.0]))

        path = Path(self.tmpdir) / "index.json"
        idx.save(path)
        self.assertTrue(path.exists())

        loaded = VectorIndex.load(path)
        self.assertEqual(len(loaded), 2)
        self.assertIsNotNone(loaded.get("e1"))
        self.assertEqual(loaded.get("e1").metadata["text"], "hello")

    def test_load_nonexistent(self):
        loaded = VectorIndex.load(Path(self.tmpdir) / "nonexistent.json")
        self.assertTrue(loaded.is_empty)

    def test_search_after_load(self):
        idx = VectorIndex(dim=3)
        idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        idx.insert(VectorEntry(id="e2", vector=[0.0, 1.0, 0.0]))

        path = Path(self.tmpdir) / "index.json"
        idx.save(path)
        loaded = VectorIndex.load(path)
        results = loaded.search([1.0, 0.0, 0.0], k=1)
        self.assertEqual(results[0][0], "e1")


class TestFilter(unittest.TestCase):
    """Tests for search filtering."""

    def setUp(self):
        self.idx = VectorIndex(dim=3)
        self.idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0], metadata={"type": "code"}))
        self.idx.insert(VectorEntry(id="e2", vector=[0.9, 0.1, 0.0], metadata={"type": "text"}))
        self.idx.insert(VectorEntry(id="e3", vector=[0.8, 0.2, 0.0], metadata={"type": "code"}))

    def test_filter_by_metadata(self):
        results = self.idx.search(
            [1.0, 0.0, 0.0], k=5,
            filter_fn=lambda e: e.metadata.get("type") == "code",
        )
        self.assertEqual(len(results), 2)
        for _, _, entry in results:
            self.assertEqual(entry.metadata["type"], "code")

    def test_no_filter_returns_all(self):
        results = self.idx.search([1.0, 0.0, 0.0], k=5)
        self.assertEqual(len(results), 3)


class TestMetrics(unittest.TestCase):
    """Tests for different similarity metrics."""

    def test_dot_product_metric(self):
        idx = VectorIndex(dim=3, metric="dot")
        idx.insert(VectorEntry(id="e1", vector=[2.0, 0.0, 0.0]))
        results = idx.search([3.0, 0.0, 0.0], k=1)
        # dot product = 6.0
        self.assertAlmostEqual(results[0][1], 6.0)

    def test_cosine_metric_default(self):
        idx = VectorIndex(dim=3)
        idx.insert(VectorEntry(id="e1", vector=[2.0, 0.0, 0.0]))
        results = idx.search([3.0, 0.0, 0.0], k=1)
        # cosine = 1.0 (same direction)
        self.assertAlmostEqual(results[0][1], 1.0)


class TestStats(unittest.TestCase):
    """Tests for index statistics."""

    def test_empty_stats(self):
        idx = VectorIndex(dim=768)
        stats = idx.stats()
        self.assertEqual(stats["count"], 0)
        self.assertFalse(stats["has_entry_point"])

    def test_populated_stats(self):
        idx = VectorIndex(dim=3)
        idx.insert(VectorEntry(id="e1", vector=[1.0, 0.0, 0.0]))
        idx.insert(VectorEntry(id="e2", vector=[0.0, 1.0, 0.0]))
        stats = idx.stats()
        self.assertEqual(stats["count"], 2)
        self.assertTrue(stats["has_entry_point"])
        self.assertEqual(stats["dim"], 3)


class TestVectorEntry(unittest.TestCase):
    """Tests for VectorEntry dataclass."""

    def test_to_dict_and_from_dict(self):
        entry = VectorEntry(
            id="test", vector=[1.0, 2.0],
            metadata={"key": "value"}, created_at=12345.0, access_count=3,
        )
        d = entry.to_dict()
        entry2 = VectorEntry.from_dict(d)
        self.assertEqual(entry2.id, "test")
        self.assertEqual(entry2.vector, [1.0, 2.0])
        self.assertEqual(entry2.metadata, {"key": "value"})
        self.assertEqual(entry2.access_count, 3)

    def test_default_values(self):
        entry = VectorEntry(id="test", vector=[1.0])
        self.assertEqual(entry.metadata, {})
        self.assertEqual(entry.access_count, 0)
        self.assertEqual(entry.created_at, 0.0)


if __name__ == "__main__":
    unittest.main()
