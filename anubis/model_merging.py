"""Model merging — combine weights of multiple models without training.

Instead of forcing a small model to learn complex new concepts through
grueling backpropagation, this module mathematically blends the neural
weight layers of multiple models. This takes seconds on CPU and
introduces massive injections of new capabilities without a single
epoch of traditional training.

Implements three merging strategies:
1. SLERP (Spherical Linear Interpolation) — smooth interpolation
   between two models' weights, preserving the geometric structure
   of the weight space.
2. TIES-Merging — Trim, Elect sign, and Merge. Handles conflicts
   between multiple models by trimming small deltas, electing the
   dominant sign, and merging only non-conflicting deltas.
3. Linear merge — simple weighted average (baseline).

All operations use only the Python standard library (math, json).
Weight tensors are represented as flat lists of floats. Real model
files (safetensors) would be loaded by an adapter before merging.

Constitutional governance:
- Model merging is a ChangeClass.CONSEQUENTIAL action
- Main Engine merges require Court review and artifact hash binding
- All merges are logged to the evidence ledger
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class ModelWeights:
    """A simple model weight representation.

    Weights are stored as a dict mapping parameter names to flat
    float lists. This is a simplified representation — real model
    files would be loaded by an adapter that converts safetensors
    or GGUF to this format.
    """
    name: str
    params: dict[str, list[float]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def param_count(self) -> int:
        return sum(len(v) for v in self.params.values())

    @property
    def param_names(self) -> list[str]:
        return sorted(self.params.keys())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "params": self.params,
            "metadata": self.metadata,
        }


def _slerp(t: float, v0: list[float], v1: list[float]) -> list[float]:
    """Spherical linear interpolation between two vectors.

    SLERP preserves the geometric structure of the weight space,
    producing smoother transitions than linear interpolation.

    Args:
        t: Interpolation factor (0.0 = v0, 1.0 = v1)
        v0: First vector
        v1: Second vector

    Returns:
        Interpolated vector
    """
    if len(v0) != len(v1):
        raise ValueError(f"vector length mismatch: {len(v0)} vs {len(v1)}")

    # Compute dot product
    dot = sum(a * b for a, b in zip(v0, v1))

    # Compute norms
    norm0 = math.sqrt(sum(a * a for a in v0))
    norm1 = math.sqrt(sum(b * b for b in v1))

    if norm0 == 0 or norm1 == 0:
        # Fall back to linear if either is zero
        return [a * (1 - t) + b * t for a, b in zip(v0, v1)]

    # Normalized dot product
    omega = dot / (norm0 * norm1)
    # Clamp to valid acos range
    omega = max(-1.0, min(1.0, omega))

    # If vectors are nearly parallel, use linear interpolation
    if abs(omega) > 0.9995:
        return [a * (1 - t) + b * t for a, b in zip(v0, v1)]

    theta = math.acos(omega)
    sin_theta = math.sin(theta)

    # SLERP formula
    coef0 = math.sin((1 - t) * theta) / sin_theta
    coef1 = math.sin(t * theta) / sin_theta

    return [coef0 * a + coef1 * b for a, b in zip(v0, v1)]


def _ties_merge(
    base: list[float],
    deltas: list[list[float]],
    *,
    density: float = 0.5,
) -> list[float]:
    """TIES-Merging: Trim, Elect sign, Merge.

    Args:
        base: Base model weights
        deltas: List of delta vectors (model - base for each model)
        density: Fraction of deltas to keep (0.0 to 1.0)

    Returns:
        Merged weights
    """
    if not deltas:
        return list(base)

    n = len(base)
    # Step 1: Trim — keep only top-k magnitude deltas per model
    trim_count = int(n * density)
    trimmed_deltas: list[list[float]] = []
    for delta in deltas:
        # Compute magnitudes and find threshold
        mags = [abs(d) for d in delta]
        sorted_mags = sorted(mags, reverse=True)
        threshold = sorted_mags[trim_count - 1] if trim_count > 0 else 0.0

        trimmed = [d if abs(d) >= threshold else 0.0 for d in delta]
        trimmed_deltas.append(trimmed)

    # Step 2: Elect sign — majority vote on sign at each position
    result = list(base)
    for i in range(n):
        # Collect non-zero deltas at this position
        values = [td[i] for td in trimmed_deltas if td[i] != 0.0]
        if not values:
            continue

        # Count positive and negative
        pos = sum(1 for v in values if v > 0)
        neg = sum(1 for v in values if v < 0)

        # Step 3: Merge — average only non-conflicting deltas
        if pos > neg:
            # Keep positive
            kept = [v for v in values if v > 0]
            result[i] = base[i] + sum(kept) / len(kept)
        elif neg > pos:
            # Keep negative
            kept = [v for v in values if v < 0]
            result[i] = base[i] + sum(kept) / len(kept)
        else:
            # Tie — average all
            result[i] = base[i] + sum(values) / len(values)

    return result


def _linear_merge(
    models: list[list[float]],
    weights: list[float] | None = None,
) -> list[float]:
    """Linear (weighted average) merge of multiple models.

    Args:
        models: List of model weight vectors
        weights: Optional weights for each model (must sum to 1.0)

    Returns:
        Merged weights
    """
    if not models:
        return []
    if len(models) == 1:
        return list(models[0])

    if weights is None:
        weights = [1.0 / len(models)] * len(models)
    else:
        total = sum(weights)
        if total == 0:
            weights = [1.0 / len(models)] * len(models)
        else:
            weights = [w / total for w in weights]

    n = len(models[0])
    result = [0.0] * n
    for model, w in zip(models, weights):
        for i in range(n):
            result[i] += model[i] * w
    return result


@dataclass
class MergeResult:
    """Result of a model merge operation."""
    ok: bool
    strategy: str = ""
    merged_model: ModelWeights | None = None
    param_count: int = 0
    duration_s: float = 0.0
    artifact_hash: str = ""
    error: str = ""


class ModelMerger:
    """Merge multiple models' weights using various strategies.

    All merges are logged to the evidence ledger. Main Engine merges
    require Court review and artifact hash binding per the constitution.
    """

    def __init__(self, ledger: Ledger | None = None) -> None:
        self.ledger = ledger

    def _compute_hash(self, model: ModelWeights) -> str:
        """Compute SHA-256 hash of model weights."""
        h = hashlib.sha256()
        for name in sorted(model.params.keys()):
            h.update(name.encode("utf-8"))
            for v in model.params[name]:
                h.update(struct_pack_float(v))
        return h.hexdigest()

    def merge_slerp(
        self,
        model_a: ModelWeights,
        model_b: ModelWeights,
        *,
        t: float = 0.5,
    ) -> MergeResult:
        """Merge two models using SLERP.

        Args:
            model_a: First model (t=0.0)
            model_b: Second model (t=1.0)
            t: Interpolation factor (0.0 to 1.0)

        Returns:
            MergeResult with the merged model
        """
        t0 = time.monotonic()
        if model_a.param_names != model_b.param_names:
            return MergeResult(
                ok=False, strategy="slerp",
                error="parameter name mismatch between models",
            )

        merged_params: dict[str, list[float]] = {}
        for name in model_a.param_names:
            merged_params[name] = _slerp(t, model_a.params[name], model_b.params[name])

        merged = ModelWeights(
            name=f"slerp_{model_a.name}_{model_b.name}",
            params=merged_params,
            metadata={
                "strategy": "slerp",
                "t": t,
                "parents": [model_a.name, model_b.name],
            },
        )
        artifact_hash = self._compute_hash(merged)

        if self.ledger:
            self.ledger.append({
                "event": "model_merge",
                "strategy": "slerp",
                "parents": [model_a.name, model_b.name],
                "t": t,
                "artifact_hash": artifact_hash,
            })

        return MergeResult(
            ok=True,
            strategy="slerp",
            merged_model=merged,
            param_count=merged.param_count,
            duration_s=round(time.monotonic() - t0, 3),
            artifact_hash=artifact_hash,
        )

    def merge_ties(
        self,
        base: ModelWeights,
        models: list[ModelWeights],
        *,
        density: float = 0.5,
    ) -> MergeResult:
        """Merge multiple models into a base using TIES-Merging.

        Args:
            base: Base model
            models: List of models to merge into the base
            density: Fraction of deltas to keep (0.0 to 1.0)

        Returns:
            MergeResult with the merged model
        """
        t0 = time.monotonic()
        if not models:
            return MergeResult(ok=False, strategy="ties", error="no models to merge")

        # Verify parameter compatibility
        base_names = base.param_names
        for m in models:
            if m.param_names != base_names:
                return MergeResult(
                    ok=False, strategy="ties",
                    error=f"parameter mismatch: {m.name} vs base",
                )

        merged_params: dict[str, list[float]] = {}
        for name in base_names:
            base_vec = base.params[name]
            deltas = [
                [m.params[name][i] - base_vec[i] for i in range(len(base_vec))]
                for m in models
            ]
            merged_params[name] = _ties_merge(base_vec, deltas, density=density)

        merged = ModelWeights(
            name=f"ties_{base.name}_+{len(models)}",
            params=merged_params,
            metadata={
                "strategy": "ties",
                "density": density,
                "parents": [base.name] + [m.name for m in models],
            },
        )
        artifact_hash = self._compute_hash(merged)

        if self.ledger:
            self.ledger.append({
                "event": "model_merge",
                "strategy": "ties",
                "parents": [base.name] + [m.name for m in models],
                "density": density,
                "artifact_hash": artifact_hash,
            })

        return MergeResult(
            ok=True,
            strategy="ties",
            merged_model=merged,
            param_count=merged.param_count,
            duration_s=round(time.monotonic() - t0, 3),
            artifact_hash=artifact_hash,
        )

    def merge_linear(
        self,
        models: list[ModelWeights],
        weights: list[float] | None = None,
    ) -> MergeResult:
        """Merge multiple models using linear (weighted average) merge.

        Args:
            models: List of models to merge
            weights: Optional weights for each model

        Returns:
            MergeResult with the merged model
        """
        t0 = time.monotonic()
        if not models:
            return MergeResult(ok=False, strategy="linear", error="no models")

        # Verify compatibility
        ref_names = models[0].param_names
        for m in models[1:]:
            if m.param_names != ref_names:
                return MergeResult(
                    ok=False, strategy="linear",
                    error=f"parameter mismatch: {m.name}",
                )

        merged_params: dict[str, list[float]] = {}
        for name in ref_names:
            vecs = [m.params[name] for m in models]
            merged_params[name] = _linear_merge(vecs, weights)

        merged = ModelWeights(
            name=f"linear_{'_'.join(m.name for m in models)}",
            params=merged_params,
            metadata={
                "strategy": "linear",
                "weights": weights,
                "parents": [m.name for m in models],
            },
        )
        artifact_hash = self._compute_hash(merged)

        if self.ledger:
            self.ledger.append({
                "event": "model_merge",
                "strategy": "linear",
                "parents": [m.name for m in models],
                "artifact_hash": artifact_hash,
            })

        return MergeResult(
            ok=True,
            strategy="linear",
            merged_model=merged,
            param_count=merged.param_count,
            duration_s=round(time.monotonic() - t0, 3),
            artifact_hash=artifact_hash,
        )

    def save_model(
        self, model: ModelWeights, path: str | Path
    ) -> dict[str, Any]:
        """Save a merged model to disk (JSON format)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = model.to_dict()
        data["saved_at"] = time.time()
        path.write_text(
            json.dumps(data, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {"saved": True, "path": str(path), "params": model.param_count}


def struct_pack_float(v: float) -> bytes:
    """Pack a float into bytes for hashing."""
    import struct
    return struct.pack("d", v)
