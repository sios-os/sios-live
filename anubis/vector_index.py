"""In-process vector index for fast semantic recall.

Replaces the file-scan approach with an indexed search. Uses a
simplified HNSW (Hierarchical Navigable Small World) graph structure
implemented with only the Python standard library, per the
constitutional kernel's permission-integrity rule.

The index supports:
- Insert vectors with metadata
- Search by similarity (cosine or dot product)
- Remove vectors by ID
- Persist to disk (JSON format)
- Rebuild after purges (prevents fragmentation)
- Batch insert for bulk loading

Performance:
- O(log N) search on HNSW (vs O(N) file scan)
- In-memory graph, disk-persisted
- Suitable for up to ~100k vectors on a single machine
- For larger scale, integrate Qdrant/Milvus (future)

The index is used by the memory module for semantic recall. When the
memory system purges old entries, it calls rebuild() to re-optimize
the graph structure.
"""
from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VectorEntry:
    """A vector with associated metadata."""
    id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vector": self.vector,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VectorEntry":
        return cls(
            id=data["id"],
            vector=data["vector"],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", 0.0),
            access_count=data.get("access_count", 0),
        )


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _dot_product(a: list[float], b: list[float]) -> float:
    """Compute dot product between two vectors."""
    return sum(x * y for x, y in zip(a, b))


class VectorIndex:
    """In-process vector index with HNSW-like search.

    Uses a simplified HNSW graph for approximate nearest neighbor
    search. The graph is built incrementally as vectors are inserted.

    Parameters:
        dim: Vector dimensionality
        max_connections: Max connections per node in the graph (M)
        ef_construction: Search depth during insertion
        ef_search: Search depth during query
        metric: "cosine" or "dot"
    """

    def __init__(
        self,
        dim: int = 768,
        *,
        max_connections: int = 16,
        ef_construction: int = 100,
        ef_search: int = 50,
        metric: str = "cosine",
    ) -> None:
        self.dim = dim
        self.max_connections = max_connections
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.metric = metric
        self._entries: dict[str, VectorEntry] = {}
        self._graph: dict[str, list[str]] = {}  # id -> neighbor ids
        self._entry_point: str | None = None
        self._max_level: int = 0
        self._levels: dict[str, int] = {}  # id -> level

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        return len(self._entries) == 0

    def _similarity(self, a: list[float], b: list[float]) -> float:
        """Compute similarity based on the configured metric."""
        if self.metric == "dot":
            return _dot_product(a, b)
        return _cosine_similarity(a, b)

    def _random_level(self) -> int:
        """Generate a random level for the HNSW graph."""
        level = 0
        while random.random() < 0.5 and level < 10:
            level += 1
        return level

    def insert(self, entry: VectorEntry) -> None:
        """Insert a vector entry into the index."""
        if len(entry.vector) != self.dim:
            raise ValueError(
                f"vector dimension mismatch: expected {self.dim}, got {len(entry.vector)}"
            )
        if not entry.created_at:
            entry.created_at = time.time()

        self._entries[entry.id] = entry
        self._graph[entry.id] = []
        level = self._random_level()
        self._levels[entry.id] = level

        if self._entry_point is None:
            self._entry_point = entry.id
            self._max_level = level
            return

        # Connect to nearest neighbors at each level
        # Simplified: just connect to the nearest entries
        neighbors = self._search_layer(
            entry.vector, self.ef_construction, set(), set([self._entry_point])
        )
        # Keep only the top max_connections
        neighbors.sort(key=lambda x: -x[1])
        self._graph[entry.id] = [n for n, _ in neighbors[:self.max_connections]]

        # Add reverse connections
        for nid, _ in neighbors[:self.max_connections]:
            if nid not in self._graph:
                self._graph[nid] = []
            if entry.id not in self._graph[nid]:
                self._graph[nid].append(entry.id)
                # Prune if too many connections
                if len(self._graph[nid]) > self.max_connections * 2:
                    self._graph[nid] = self._graph[nid][:self.max_connections]

        # Update entry point if this node has a higher level
        if level > self._max_level:
            self._max_level = level
            self._entry_point = entry.id

    def insert_batch(self, entries: list[VectorEntry]) -> int:
        """Insert multiple entries. Returns count inserted."""
        count = 0
        for entry in entries:
            try:
                self.insert(entry)
                count += 1
            except ValueError:
                continue
        return count

    def _search_layer(
        self,
        query: list[float],
        ef: int,
        visited: set[str],
        entry_points: set[str],
    ) -> list[tuple[str, float]]:
        """Search a single layer of the graph."""
        candidates: list[tuple[str, float]] = []
        for ep_id in entry_points:
            if ep_id in visited or ep_id not in self._entries:
                continue
            sim = self._similarity(query, self._entries[ep_id].vector)
            candidates.append((ep_id, sim))
            visited.add(ep_id)

        candidates.sort(key=lambda x: -x[1])
        results = list(candidates[:ef])

        # Expand from the best candidates
        i = 0
        while i < len(candidates) and i < ef:
            cid, _ = candidates[i]
            for nid in self._graph.get(cid, []):
                if nid in visited or nid not in self._entries:
                    continue
                visited.add(nid)
                sim = self._similarity(query, self._entries[nid].vector)
                candidates.append((nid, sim))
                candidates.sort(key=lambda x: -x[1])
                if len(candidates) > ef * 2:
                    candidates = candidates[:ef * 2]
            i += 1

        return results[:ef]

    def search(
        self,
        query: list[float],
        k: int = 5,
        *,
        filter_fn: Any | None = None,
    ) -> list[tuple[str, float, VectorEntry]]:
        """Search for the k most similar vectors.

        Returns list of (id, similarity_score, entry) tuples.
        Optional filter_fn(entry) -> bool can filter results.

        For small indexes (<= ef_search entries), uses brute-force
        scan which is both faster and more accurate. For larger
        indexes, uses the HNSW graph for approximate search.
        """
        if self.is_empty or self._entry_point is None:
            return []

        if len(query) != self.dim:
            raise ValueError(
                f"query dimension mismatch: expected {self.dim}, got {len(query)}"
            )

        # For small indexes, brute-force is faster and exact
        if len(self._entries) <= max(self.ef_search, k, 100):
            results: list[tuple[str, float]] = []
            for eid, entry in self._entries.items():
                sim = self._similarity(query, entry.vector)
                results.append((eid, sim))
            results.sort(key=lambda x: -x[1])
        else:
            # HNSW graph search for larger indexes
            visited: set[str] = set()
            results = self._search_layer(
                query, max(self.ef_search, k), visited, set([self._entry_point])
            )
            results.sort(key=lambda x: -x[1])

        # Apply filter and take top k
        output = []
        for rid, score in results:
            entry = self._entries.get(rid)
            if entry is None:
                continue
            if filter_fn and not filter_fn(entry):
                continue
            entry.access_count += 1
            output.append((rid, score, entry))
            if len(output) >= k:
                break

        return output

    def get(self, entry_id: str) -> VectorEntry | None:
        """Get an entry by ID."""
        return self._entries.get(entry_id)

    def remove(self, entry_id: str) -> bool:
        """Remove an entry by ID."""
        if entry_id not in self._entries:
            return False
        del self._entries[entry_id]
        # Remove from graph
        if entry_id in self._graph:
            del self._graph[entry_id]
        # Remove reverse connections
        for nid, neighbors in self._graph.items():
            if entry_id in neighbors:
                self._graph[nid] = [n for n in neighbors if n != entry_id]
        # Update entry point if needed
        if self._entry_point == entry_id:
            self._entry_point = next(iter(self._entries), None)
            self._max_level = self._levels.get(self._entry_point, 0) if self._entry_point else 0
        return True

    def rebuild(self) -> dict[str, Any]:
        """Rebuild the graph structure from scratch.

        This should be called after purges to prevent fragmentation
        and maintain search quality. Rebuilds all connections based
        on current vector positions.
        """
        if self.is_empty:
            return {"rebuilt": True, "count": 0, "duration_s": 0.0}

        t0 = time.monotonic()
        entries = list(self._entries.values())
        self._graph = {}
        self._levels = {}
        self._entry_point = None
        self._max_level = 0

        # Re-insert all entries
        for entry in entries:
            self._graph[entry.id] = []
            level = self._random_level()
            self._levels[entry.id] = level
            if self._entry_point is None:
                self._entry_point = entry.id
                self._max_level = level
                continue
            # Connect to nearest
            neighbors = self._search_layer(
                entry.vector, self.ef_construction, set(), set([self._entry_point])
            )
            neighbors.sort(key=lambda x: -x[1])
            self._graph[entry.id] = [n for n, _ in neighbors[:self.max_connections]]
            for nid, _ in neighbors[:self.max_connections]:
                if nid not in self._graph:
                    self._graph[nid] = []
                if entry.id not in self._graph[nid]:
                    self._graph[nid].append(entry.id)
                    if len(self._graph[nid]) > self.max_connections * 2:
                        self._graph[nid] = self._graph[nid][:self.max_connections]
            if level > self._max_level:
                self._max_level = level
                self._entry_point = entry.id

        elapsed = time.monotonic() - t0
        return {
            "rebuilt": True,
            "count": len(self._entries),
            "duration_s": round(elapsed, 3),
        }

    def stats(self) -> dict[str, Any]:
        """Return index statistics."""
        total_connections = sum(len(v) for v in self._graph.values())
        avg_connections = (
            total_connections / len(self._graph) if self._graph else 0.0
        )
        return {
            "count": len(self._entries),
            "dim": self.dim,
            "metric": self.metric,
            "max_connections": self.max_connections,
            "total_graph_edges": total_connections,
            "avg_connections": round(avg_connections, 2),
            "max_level": self._max_level,
            "has_entry_point": self._entry_point is not None,
        }

    def save(self, path: str | Path) -> None:
        """Persist the index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "dim": self.dim,
            "max_connections": self.max_connections,
            "ef_construction": self.ef_construction,
            "ef_search": self.ef_search,
            "metric": self.metric,
            "entries": [e.to_dict() for e in self._entries.values()],
            "graph": self._graph,
            "entry_point": self._entry_point,
            "max_level": self._max_level,
            "levels": self._levels,
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "VectorIndex":
        """Load an index from disk."""
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        idx = cls(
            dim=data.get("dim", 768),
            max_connections=data.get("max_connections", 16),
            ef_construction=data.get("ef_construction", 100),
            ef_search=data.get("ef_search", 50),
            metric=data.get("metric", "cosine"),
        )
        for entry_data in data.get("entries", []):
            entry = VectorEntry.from_dict(entry_data)
            idx._entries[entry.id] = entry
        idx._graph = data.get("graph", {})
        idx._entry_point = data.get("entry_point")
        idx._max_level = data.get("max_level", 0)
        idx._levels = data.get("levels", {})
        return idx
