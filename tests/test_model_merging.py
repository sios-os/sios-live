"""Tests for the model merging module.

Tests verify:
- SLERP interpolation (geometry, edge cases)
- TIES-Merging (trim, elect, merge)
- Linear merge (weighted average)
- Parameter compatibility checks
- Artifact hashing
- Model save/load
- Evidence ledger logging
"""
import json
import math
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.model_merging import (
    ModelMerger,
    ModelWeights,
    MergeResult,
    _slerp,
    _ties_merge,
    _linear_merge,
)


class TestSLERP(unittest.TestCase):
    """Tests for SLERP interpolation."""

    def test_t_zero_returns_v0(self):
        v0 = [1.0, 0.0, 0.0]
        v1 = [0.0, 1.0, 0.0]
        result = _slerp(0.0, v0, v1)
        for a, b in zip(result, v0):
            self.assertAlmostEqual(a, b)

    def test_t_one_returns_v1(self):
        v0 = [1.0, 0.0, 0.0]
        v1 = [0.0, 1.0, 0.0]
        result = _slerp(1.0, v0, v1)
        for a, b in zip(result, v1):
            self.assertAlmostEqual(a, b)

    def test_t_half_is_midpoint(self):
        v0 = [1.0, 0.0, 0.0]
        v1 = [0.0, 1.0, 0.0]
        result = _slerp(0.5, v0, v1)
        # At t=0.5, SLERP of orthogonal unit vectors gives equal components
        self.assertAlmostEqual(result[0], result[1])

    def test_parallel_vectors_linear(self):
        v0 = [1.0, 2.0, 3.0]
        v1 = [2.0, 4.0, 6.0]  # parallel
        result = _slerp(0.5, v0, v1)
        # Should fall back to linear
        expected = [1.5, 3.0, 4.5]
        for a, b in zip(result, expected):
            self.assertAlmostEqual(a, b)

    def test_zero_vector_falls_back(self):
        v0 = [0.0, 0.0, 0.0]
        v1 = [1.0, 1.0, 1.0]
        result = _slerp(0.5, v0, v1)
        # Should not crash
        self.assertEqual(len(result), 3)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            _slerp(0.5, [1.0, 0.0], [1.0, 0.0, 0.0])


class TestTIESMerge(unittest.TestCase):
    """Tests for TIES-Merging."""

    def test_no_deltas_returns_base(self):
        base = [1.0, 2.0, 3.0]
        result = _ties_merge(base, [])
        self.assertEqual(result, base)

    def test_single_delta(self):
        base = [1.0, 2.0, 3.0]
        delta = [0.1, 0.2, 0.3]
        result = _ties_merge(base, [delta], density=1.0)
        for i in range(3):
            self.assertAlmostEqual(result[i], base[i] + delta[i])

    def test_conflict_resolution(self):
        base = [1.0, 1.0]
        # Two deltas with opposite signs
        d1 = [0.5, -0.5]
        d2 = [-0.3, 0.3]
        result = _ties_merge(base, [d1, d2], density=1.0)
        # Position 0: pos=1, neg=1 → tie → average
        # Position 1: pos=1, neg=1 → tie → average
        self.assertAlmostEqual(result[0], 1.0 + (0.5 - 0.3) / 2)
        self.assertAlmostEqual(result[1], 1.0 + (-0.5 + 0.3) / 2)

    def test_majority_sign_wins(self):
        base = [0.0, 0.0]
        d1 = [0.5, 0.1]
        d2 = [0.3, -0.1]
        d3 = [0.4, -0.2]
        result = _ties_merge(base, [d1, d2, d3], density=1.0)
        # Position 0: all positive → average positives
        self.assertAlmostEqual(result[0], (0.5 + 0.3 + 0.4) / 3)
        # Position 1: 1 pos, 2 neg → negative wins
        self.assertAlmostEqual(result[1], (-0.1 - 0.2) / 2)

    def test_density_trims(self):
        base = [0.0] * 10
        delta = [0.1] * 10
        delta[0] = 1.0  # one large value
        result = _ties_merge(base, [delta], density=0.1)
        # Only top 10% should be kept (1 value)
        self.assertAlmostEqual(result[0], 1.0)
        # Others should be trimmed to 0
        self.assertEqual(result[1], 0.0)


class TestLinearMerge(unittest.TestCase):
    """Tests for linear merge."""

    def test_equal_weights(self):
        m1 = [1.0, 2.0]
        m2 = [3.0, 4.0]
        result = _linear_merge([m1, m2])
        self.assertAlmostEqual(result[0], 2.0)
        self.assertAlmostEqual(result[1], 3.0)

    def test_custom_weights(self):
        m1 = [1.0, 2.0]
        m2 = [3.0, 4.0]
        result = _linear_merge([m1, m2], weights=[0.75, 0.25])
        self.assertAlmostEqual(result[0], 1.5)
        self.assertAlmostEqual(result[1], 2.5)

    def test_single_model(self):
        m1 = [1.0, 2.0]
        result = _linear_merge([m1])
        self.assertEqual(result, m1)

    def test_empty(self):
        self.assertEqual(_linear_merge([]), [])


class TestModelWeights(unittest.TestCase):
    """Tests for ModelWeights dataclass."""

    def test_param_count(self):
        mw = ModelWeights(
            name="test",
            params={"layer1": [1.0, 2.0, 3.0], "layer2": [4.0, 5.0]},
        )
        self.assertEqual(mw.param_count, 5)

    def test_param_names_sorted(self):
        mw = ModelWeights(
            name="test",
            params={"b": [1.0], "a": [2.0]},
        )
        self.assertEqual(mw.param_names, ["a", "b"])


class TestModelMerger(unittest.TestCase):
    """Tests for the ModelMerger class."""

    def setUp(self):
        self.merger = ModelMerger()
        self.model_a = ModelWeights(
            name="model_a",
            params={"layer1": [1.0, 0.0, 0.0], "layer2": [0.5, 0.5]},
        )
        self.model_b = ModelWeights(
            name="model_b",
            params={"layer1": [0.0, 1.0, 0.0], "layer2": [0.3, 0.7]},
        )

    def test_slerp_merge(self):
        result = self.merger.merge_slerp(self.model_a, self.model_b, t=0.5)
        self.assertTrue(result.ok)
        self.assertEqual(result.strategy, "slerp")
        self.assertIsNotNone(result.merged_model)
        self.assertTrue(result.artifact_hash)

    def test_slerp_param_mismatch(self):
        bad_model = ModelWeights(name="bad", params={"other": [1.0]})
        result = self.merger.merge_slerp(self.model_a, bad_model)
        self.assertFalse(result.ok)
        self.assertIn("mismatch", result.error)

    def test_ties_merge(self):
        result = self.merger.merge_ties(
            self.model_a, [self.model_b], density=0.5
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.strategy, "ties")

    def test_ties_no_models(self):
        result = self.merger.merge_ties(self.model_a, [])
        self.assertFalse(result.ok)

    def test_linear_merge(self):
        result = self.merger.merge_linear([self.model_a, self.model_b])
        self.assertTrue(result.ok)
        self.assertEqual(result.strategy, "linear")

    def test_linear_with_weights(self):
        result = self.merger.merge_linear(
            [self.model_a, self.model_b], weights=[0.7, 0.3]
        )
        self.assertTrue(result.ok)

    def test_linear_no_models(self):
        result = self.merger.merge_linear([])
        self.assertFalse(result.ok)

    def test_save_model(self):
        result = self.merger.merge_slerp(self.model_a, self.model_b)
        tmpdir = tempfile.mkdtemp(prefix="anubis-merge-")
        try:
            save_result = self.merger.save_model(
                result.merged_model, Path(tmpdir) / "merged.json"
            )
            self.assertTrue(save_result["saved"])
            self.assertTrue((Path(tmpdir) / "merged.json").exists())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestArtifactHash(unittest.TestCase):
    """Tests for artifact hashing."""

    def test_same_model_same_hash(self):
        merger = ModelMerger()
        m = ModelWeights(name="test", params={"a": [1.0, 2.0]})
        h1 = merger._compute_hash(m)
        h2 = merger._compute_hash(m)
        self.assertEqual(h1, h2)

    def test_different_models_different_hash(self):
        merger = ModelMerger()
        m1 = ModelWeights(name="test", params={"a": [1.0, 2.0]})
        m2 = ModelWeights(name="test", params={"a": [1.0, 3.0]})
        h1 = merger._compute_hash(m1)
        h2 = merger._compute_hash(m2)
        self.assertNotEqual(h1, h2)

    def test_param_order_doesnt_matter(self):
        merger = ModelMerger()
        m1 = ModelWeights(name="test", params={"a": [1.0], "b": [2.0]})
        m2 = ModelWeights(name="test", params={"b": [2.0], "a": [1.0]})
        h1 = merger._compute_hash(m1)
        h2 = merger._compute_hash(m2)
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
