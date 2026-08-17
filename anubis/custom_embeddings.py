"""Custom embedding model — replace nomic-embed-text with ANUBIS's own.

Currently ANUBIS depends on the external `nomic-embed-text` model for
semantic search. This module provides a path to replacing that
dependency with ANUBIS's own embedding model, trained on his own
knowledge library.

The approach:
1. Generate training pairs from the knowledge library
   (document → positive pair, document → negative pair)
2. Train a small embedding model using contrastive loss
3. Export the model in a format that SemanticIndex can load
4. Evaluate against nomic-embed-text on retrieval quality
5. Promote via the A/B drive once quality matches or exceeds

Since we use only the standard library, the actual training is done
via the Unsloth adapter (which uses HuggingFace under the hood).
This module generates the training data and provides the adapter
for loading custom embeddings.

The embedding format is simple JSON:
{
    "model_name": "anubis-embed-v1",
    "dimensions": 384,
    "vocabulary": {"word": index},
    "weights": [[...]],  # embedding matrix
    "metadata": {...}
}

This is NOT a production-grade embedding model — it's a starting
point that ANUBIS can improve over time. The first version uses
a simple bag-of-words approach with TF-IDF weighting, which is
fast, local, and requires no external dependencies.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


# Default embedding dimension for the custom model
# (smaller than nomic's 768 for faster local inference)
DEFAULT_DIM = 384


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer — lowercase, split on non-alphanumeric."""
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class EmbeddingTrainingPair:
    """A training pair for contrastive embedding learning."""
    text_a: str
    text_b: str
    label: float  # 1.0 = similar, 0.0 = dissimilar

    def to_dict(self) -> dict[str, Any]:
        return {"text_a": self.text_a, "text_b": self.text_b, "label": self.label}


@dataclass
class EmbeddingModel:
    """A simple embedding model stored as JSON.

    Uses TF-IDF style weighting over a vocabulary to produce
    fixed-dimensional embeddings. This is a baseline that can
    be replaced with a neural model later.
    """
    model_name: str = "anubis-embed-v1"
    dimensions: int = DEFAULT_DIM
    vocabulary: dict[str, int] = field(default_factory=dict)
    idf_weights: dict[str, float] = field(default_factory=dict)
    document_count: int = 0
    trained_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def embed(self, text: str) -> list[float]:
        """Embed a text string into a fixed-dimensional vector.

        Uses TF-IDF weighting with random projection to the
        target dimensionality.
        """
        tokens = _tokenize(text)
        if not tokens:
            return [0.0] * self.dimensions

        # Term frequency
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        # TF-IDF weighted bag of words
        # Use hash-based projection to fixed dimensions
        vec = [0.0] * self.dimensions
        for token, count in tf.items():
            idf = self.idf_weights.get(token, 1.0)
            weight = (1.0 + math.log(count)) * idf
            # Hash-based projection
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            for i in range(min(4, self.dimensions)):
                idx = (h >> (i * 8)) & 0xFF
                dim = idx % self.dimensions
                sign = 1.0 if ((h >> (i * 8 + 7)) & 1) == 0 else -1.0
                vec[dim] += weight * sign

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "vocabulary": self.vocabulary,
            "idf_weights": self.idf_weights,
            "document_count": self.document_count,
            "trained_at": self.trained_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingModel":
        return cls(
            model_name=data.get("model_name", "anubis-embed-v1"),
            dimensions=data.get("dimensions", DEFAULT_DIM),
            vocabulary=data.get("vocabulary", {}),
            idf_weights=data.get("idf_weights", {}),
            document_count=data.get("document_count", 0),
            trained_at=data.get("trained_at", 0.0),
            metadata=data.get("metadata", {}),
        )

    def save(self, path: str | Path) -> dict[str, Any]:
        """Save the embedding model to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {"saved": True, "path": str(path), "vocab_size": len(self.vocabulary)}

    @classmethod
    def load(cls, path: str | Path) -> "EmbeddingModel":
        """Load an embedding model from disk."""
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


class EmbeddingTrainer:
    """Train a custom embedding model on ANUBIS's knowledge library.

    The training process:
    1. Scan all knowledge documents
    2. Build a vocabulary from the corpus
    3. Compute IDF weights for each term
    4. Generate positive/negative training pairs
    5. Save the model for use by SemanticIndex
    """

    def __init__(
        self,
        dimensions: int = DEFAULT_DIM,
        ledger: Ledger | None = None,
        min_doc_freq: int = 2,
        max_vocab_size: int = 50000,
    ) -> None:
        self.dimensions = dimensions
        self.ledger = ledger
        self.min_doc_freq = min_doc_freq
        self.max_vocab_size = max_vocab_size

    def _build_vocabulary(
        self, documents: list[str]
    ) -> tuple[dict[str, int], dict[str, float]]:
        """Build vocabulary and compute IDF weights.

        Args:
            documents: List of document texts

        Returns:
            Tuple of (vocabulary, idf_weights)
        """
        # Count document frequency for each term
        doc_freq: dict[str, int] = {}
        for doc in documents:
            tokens = set(_tokenize(doc))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # Filter by minimum document frequency
        vocab_terms = [
            term for term, freq in doc_freq.items()
            if freq >= self.min_doc_freq
        ]

        # Limit vocabulary size (keep most frequent)
        vocab_terms.sort(key=lambda t: doc_freq[t], reverse=True)
        vocab_terms = vocab_terms[:self.max_vocab_size]

        # Build vocabulary index
        vocabulary = {term: i for i, term in enumerate(vocab_terms)}

        # Compute IDF: log(N / df)
        n_docs = len(documents)
        idf_weights = {
            term: math.log(n_docs / doc_freq[term]) + 1.0
            for term in vocab_terms
        }

        return vocabulary, idf_weights

    def generate_training_pairs(
        self,
        documents: list[str],
        titles: list[str] | None = None,
        *,
        num_pairs: int = 100,
    ) -> list[EmbeddingTrainingPair]:
        """Generate contrastive training pairs from documents.

        Positive pairs: documents with similar titles or overlapping terms.
        Negative pairs: random documents with no term overlap.
        """
        pairs: list[EmbeddingTrainingPair] = []
        if len(documents) < 2:
            return pairs

        titles = titles or [""] * len(documents)

        # Generate positive pairs (similar documents)
        for i in range(min(num_pairs // 2, len(documents) - 1)):
            # Find a similar document
            tokens_i = set(_tokenize(documents[i]))
            best_j = -1
            best_overlap = 0
            for j in range(len(documents)):
                if j == i:
                    continue
                tokens_j = set(_tokenize(documents[j]))
                overlap = len(tokens_i & tokens_j)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_j = j

            if best_j >= 0 and best_overlap > 0:
                pairs.append(EmbeddingTrainingPair(
                    text_a=documents[i][:200],
                    text_b=documents[best_j][:200],
                    label=1.0,
                ))

        # Generate negative pairs (dissimilar documents)
        for i in range(min(num_pairs // 2, len(documents) - 1)):
            # Find a dissimilar document
            tokens_i = set(_tokenize(documents[i]))
            worst_j = -1
            worst_overlap = float("inf")
            for j in range(len(documents)):
                if j == i:
                    continue
                tokens_j = set(_tokenize(documents[j]))
                overlap = len(tokens_i & tokens_j)
                if overlap < worst_overlap:
                    worst_overlap = overlap
                    worst_j = j

            if worst_j >= 0:
                pairs.append(EmbeddingTrainingPair(
                    text_a=documents[i][:200],
                    text_b=documents[worst_j][:200],
                    label=0.0,
                ))

        return pairs

    def train(
        self,
        documents: list[str],
        model_name: str = "anubis-embed-v1",
    ) -> EmbeddingModel:
        """Train a custom embedding model on a corpus.

        Args:
            documents: List of document texts
            model_name: Name for the trained model

        Returns:
            Trained EmbeddingModel
        """
        t0 = time.monotonic()

        vocabulary, idf_weights = self._build_vocabulary(documents)

        model = EmbeddingModel(
            model_name=model_name,
            dimensions=self.dimensions,
            vocabulary=vocabulary,
            idf_weights=idf_weights,
            document_count=len(documents),
            trained_at=time.time(),
            metadata={
                "training_method": "tfidf_hash_projection",
                "vocab_size": len(vocabulary),
                "training_duration_s": round(time.monotonic() - t0, 3),
            },
        )

        if self.ledger:
            self.ledger.append({
                "event": "embedding_model_trained",
                "model_name": model_name,
                "vocab_size": len(vocabulary),
                "dimensions": self.dimensions,
                "document_count": len(documents),
            })

        return model

    def evaluate_retrieval(
        self,
        model: EmbeddingModel,
        documents: list[str],
        queries: list[str],
        *,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Evaluate retrieval quality of the embedding model.

        Computes embeddings for all documents and queries, then
        measures how often the correct document appears in top_k.
        """
        # Embed all documents
        doc_embeddings = [model.embed(doc) for doc in documents]

        # For each query, find top_k documents
        hits = 0
        total = len(queries)
        for i, query in enumerate(queries):
            query_emb = model.embed(query)
            # Cosine similarity (vectors are already normalized)
            scores = []
            for j, doc_emb in enumerate(doc_embeddings):
                score = sum(a * b for a, b in zip(query_emb, doc_emb))
                scores.append((score, j))
            scores.sort(reverse=True)
            top_indices = [idx for _, idx in scores[:top_k]]
            # Check if the matching document (by index) is in top_k
            # For this simple eval, we assume query i matches document i
            if i in top_indices:
                hits += 1

        return {
            "queries": total,
            "hits": hits,
            "hit_rate": round(hits / total, 3) if total > 0 else 0.0,
            "top_k": top_k,
        }


class CustomEmbeddingAdapter:
    """Adapter to use a custom embedding model in place of nomic-embed-text.

    Provides the same interface as the Ollama embedding function
    used by SemanticIndex, but uses the local custom model instead.
    """

    def __init__(self, model: EmbeddingModel) -> None:
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Embed text using the custom model."""
        return self.model.embed(text)

    @property
    def dimensions(self) -> int:
        return self.model.dimensions

    @property
    def model_name(self) -> str:
        return self.model.model_name

    def status(self) -> dict[str, Any]:
        """Return adapter status."""
        return {
            "model_name": self.model.model_name,
            "dimensions": self.model.dimensions,
            "vocab_size": len(self.model.vocabulary),
            "document_count": self.model.document_count,
            "trained_at": self.model.trained_at,
            "replaces": "nomic-embed-text",
        }
