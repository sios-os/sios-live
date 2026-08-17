"""Semantic search using Ollama embeddings.

This module provides embedding-based retrieval over the knowledge library,
complementing the keyword-based KnowledgeGrounding with semantic similarity.

Uses nomic-embed-text (768-dim) via Ollama's /api/embeddings endpoint.
All inference is local — no cloud.

Uses VectorIndex for O(log N) search instead of linear scan.
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from anubis.vector_index import VectorIndex, VectorEntry

EMBEDDING_MODEL = os.environ.get("ANUBIS_EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434")
EMBED_DIM = 768
CACHE_FILE = "knowledge/embeddings_cache.json"
CUSTOM_EMBED_PATH = os.environ.get(
    "ANUBIS_CUSTOM_EMBED", "memory/custom_embed_model.json"
)
# When True, use the custom embedding model as the PRIMARY source.
# Ollama (nomic-embed-text) becomes the fallback.
# This is the Phase 2 default — ANUBIS prefers his own embeddings.
PREFER_CUSTOM_EMBED = os.environ.get(
    "ANUBIS_PREFER_CUSTOM_EMBED", "1"
) == "1"

_custom_embed_cache = None


def _load_custom_embed():
    """Load custom embedding model if available (cached)."""
    global _custom_embed_cache
    if _custom_embed_cache is not None:
        return _custom_embed_cache
    path = Path(CUSTOM_EMBED_PATH)
    if not path.exists():
        return None
    try:
        from anubis.custom_embeddings import EmbeddingModel
        _custom_embed_cache = EmbeddingModel.load(path)
        return _custom_embed_cache
    except Exception:
        return None


def _embed_ollama(text: str) -> list[float]:
    """Get embedding from Ollama (legacy fallback)."""
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=json.dumps({"model": EMBEDDING_MODEL, "prompt": text[:2000]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    return data.get("embedding", [])


def _embed(text: str) -> list[float]:
    """Get embedding — custom model primary, Ollama fallback.

    Phase 2 behavior:
    1. If a custom embedding model is trained, use it (self-hosted)
    2. If custom model unavailable, try Ollama (nomic-embed-text)
    3. If both unavailable, return empty vector

    This makes ANUBIS self-reliant for embeddings. Once the custom
    model is trained via embeddings_train, Ollama is no longer needed.
    """
    # Try custom embedding model first (self-hosted)
    if PREFER_CUSTOM_EMBED:
        custom = _load_custom_embed()
        if custom is not None:
            emb = custom.embed(text)
            if emb:
                return emb

    # Fall back to Ollama
    try:
        emb = _embed_ollama(text)
        if emb:
            return emb
    except Exception:
        pass

    return []

    # Fallback to custom embedding model
    custom = _load_custom_embed()
    if custom is not None:
        return custom.embed(text)

    return []


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class SemanticResult:
    doc_id: str
    title: str
    specialty_id: str
    score: float
    snippet: str = ""


class SemanticIndex:
    """Embedding-based index over knowledge documents.

    Uses VectorIndex internally for fast similarity search.
    Falls back to linear scan if the vector index is not built.
    """

    def __init__(self, cache_path: str | Path | None = None) -> None:
        self.cache_path = Path(cache_path) if cache_path else Path(CACHE_FILE)
        self._embeddings: dict[str, list[float]] = {}
        self._doc_meta: dict[str, dict[str, Any]] = {}
        self._loaded = False
        self._vindex: VectorIndex | None = None
        self._vindex_dirty = False

    def _load_cache(self) -> None:
        if self._loaded:
            return
        if self.cache_path.exists():
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._embeddings = data.get("embeddings", {})
            self._doc_meta = data.get("meta", {})
        self._loaded = True
        # Build vector index from loaded embeddings
        self._rebuild_vindex()

    def _rebuild_vindex(self) -> None:
        """Build the internal VectorIndex from cached embeddings."""
        if not self._embeddings:
            self._vindex = None
            return
        idx = VectorIndex(dim=EMBED_DIM, metric="cosine")
        entries = []
        for doc_id, emb in self._embeddings.items():
            meta = self._doc_meta.get(doc_id, {})
            entries.append(VectorEntry(
                id=doc_id,
                vector=emb,
                metadata=meta,
            ))
        idx.insert_batch(entries)
        self._vindex = idx
        self._vindex_dirty = False

    def _save_cache(self) -> None:
        data = {"embeddings": self._embeddings, "meta": self._doc_meta}
        self.cache_path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def build(self, kb, batch_size: int = 50, force: bool = False) -> dict[str, int]:
        """Build embeddings for all documents in the knowledge base."""
        self._load_cache()
        docs = kb.library_documents()
        built = 0
        skipped = 0
        for i, doc in enumerate(docs):
            if not force and doc.doc_id in self._embeddings:
                skipped += 1
                continue
            # Embed the title + first 500 chars of content
            text = f"{doc.title}. {doc.content[:500]}"
            try:
                emb = _embed(text)
                if emb:
                    self._embeddings[doc.doc_id] = emb
                    self._doc_meta[doc.doc_id] = {
                        "title": doc.title,
                        "specialty_id": doc.specialty_id,
                        "snippet": doc.content[:200],
                    }
                    built += 1
                    self._vindex_dirty = True
                if built % batch_size == 0 and built > 0:
                    self._save_cache()
                    print(f"  Embedded {built} documents...")
            except Exception as e:
                print(f"  ERROR embedding {doc.doc_id}: {e}")
        self._save_cache()
        # Rebuild vector index if we added new entries
        if self._vindex_dirty:
            self._rebuild_vindex()
        return {"built": built, "skipped": skipped, "total": len(docs)}

    def search(
        self, query: str, top_k: int = 5, specialty_id: str | None = None
    ) -> list[SemanticResult]:
        """Search for documents semantically similar to the query.

        Uses VectorIndex for O(log N) search when available.
        Falls back to linear scan otherwise.
        """
        self._load_cache()
        if not self._embeddings:
            return []
        try:
            query_emb = _embed(query)
        except Exception:
            return []
        if not query_emb:
            return []

        # Use vector index if available
        if self._vindex is not None and len(self._vindex) > 0:
            filter_fn = None
            if specialty_id:
                def filter_fn(entry):
                    return entry.metadata.get("specialty_id") == specialty_id
            # Over-fetch for filtering
            search_k = top_k * 3 if specialty_id else top_k
            vresults = self._vindex.search(query_emb, k=search_k, filter_fn=filter_fn)
            results: list[SemanticResult] = []
            for doc_id, score, entry in vresults[:top_k]:
                meta = entry.metadata
                results.append(SemanticResult(
                    doc_id=doc_id,
                    title=meta.get("title", ""),
                    specialty_id=meta.get("specialty_id", ""),
                    score=score,
                    snippet=meta.get("snippet", ""),
                ))
            return results

        # Fallback: linear scan
        scores: list[tuple[str, float]] = []
        for doc_id, emb in self._embeddings.items():
            meta = self._doc_meta.get(doc_id, {})
            if specialty_id and meta.get("specialty_id") != specialty_id:
                continue
            sim = _cosine_sim(query_emb, emb)
            scores.append((doc_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, score in scores[:top_k]:
            meta = self._doc_meta.get(doc_id, {})
            results.append(SemanticResult(
                doc_id=doc_id,
                title=meta.get("title", ""),
                specialty_id=meta.get("specialty_id", ""),
                score=score,
                snippet=meta.get("snippet", ""),
            ))
        return results

    def stats(self) -> dict[str, Any]:
        self._load_cache()
        return {
            "indexed_docs": len(self._embeddings),
            "embedding_dim": EMBED_DIM,
            "model": EMBEDDING_MODEL,
            "cache_file": str(self.cache_path),
            "vector_index_active": self._vindex is not None,
        }

    def is_ready(self) -> bool:
        self._load_cache()
        return len(self._embeddings) > 0

    def rebuild_index(self) -> dict[str, Any]:
        """Rebuild the internal vector index from cached embeddings."""
        self._load_cache()
        self._rebuild_vindex()
        if self._vindex:
            return self._vindex.stats()
        return {"count": 0}
