"""Reranker module for improved retrieval accuracy.

Standard vector databases use Bi-Encoders (fast but shallow semantic
matching). This reranker acts as a second-stage filter: the vector
index pulls the top-N candidates, then the reranker scores each
candidate against the query for exact structural relevance.

Two reranking strategies:
1. Cloud teacher reranker — uses Gemini/Groq to score relevance
   (highest quality, requires network, privacy-gated)
2. Local lexical reranker — uses BM25-like scoring with standard
   library only (always available, no network needed)

The reranker is designed to be used by the memory and grounding
modules after initial vector retrieval. It does not replace the
vector index — it refines its results.

Privacy: the cloud reranker checks for sensitive data before sending
any query or candidate text to cloud providers. If sensitive data is
detected, it falls back to the local lexical reranker.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from .cloud_model import _check_sensitive_data


@dataclass
class RerankResult:
    """A single reranked result."""
    id: str
    score: float
    original_rank: int
    reranked_rank: int
    content: str = ""
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer for lexical scoring."""
    return re.findall(r"\w+", text.lower())


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    doc_freqs: dict[str, int],
    total_docs: int,
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute BM25 score for a single document."""
    if not doc_tokens or not query_tokens:
        return 0.0
    doc_len = len(doc_tokens)
    doc_term_freqs: dict[str, int] = {}
    for token in doc_tokens:
        doc_term_freqs[token] = doc_term_freqs.get(token, 0) + 1

    score = 0.0
    for token in query_tokens:
        if token not in doc_term_freqs:
            continue
        tf = doc_term_freqs[token]
        df = doc_freqs.get(token, 0)
        if df == 0:
            continue
        idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
    return score


class LocalReranker:
    """Lexical reranker using BM25-like scoring.

    Always available, no network needed. Uses only the Python
    standard library. Good for keyword-heavy queries where semantic
    embeddings may miss exact term matches.
    """

    def __init__(self) -> None:
        self._doc_freqs: dict[str, int] = {}
        self._total_docs: int = 0
        self._avg_doc_len: float = 0.0

    def _update_stats(self, candidates: list[dict[str, Any]]) -> None:
        """Update document frequency statistics from candidates."""
        self._doc_freqs = {}
        self._total_docs = len(candidates)
        total_len = 0
        for cand in candidates:
            content = cand.get("content", "")
            tokens = _tokenize(content)
            total_len += len(tokens)
            seen = set(tokens)
            for token in seen:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1
        self._avg_doc_len = total_len / self._total_docs if self._total_docs else 0.0

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank candidates using BM25 scoring.

        Args:
            query: The search query
            candidates: List of dicts with "id" and "content" keys
            top_k: Number of results to return

        Returns:
            List of RerankResult sorted by reranked score
        """
        if not candidates:
            return []

        self._update_stats(candidates)
        query_tokens = _tokenize(query)

        scored: list[tuple[int, float, dict[str, Any]]] = []
        for i, cand in enumerate(candidates):
            content = cand.get("content", "")
            doc_tokens = _tokenize(content)
            score = _bm25_score(
                query_tokens, doc_tokens,
                self._doc_freqs, self._total_docs, self._avg_doc_len,
            )
            scored.append((i, score, cand))

        # Sort by score descending
        scored.sort(key=lambda x: -x[1])

        results = []
        for new_rank, (orig_rank, score, cand) in enumerate(scored[:top_k]):
            results.append(RerankResult(
                id=cand.get("id", str(orig_rank)),
                score=score,
                original_rank=orig_rank,
                reranked_rank=new_rank,
                content=cand.get("content", ""),
                metadata=cand.get("metadata", {}),
            ))
        return results


class CloudReranker:
    """Cloud-teacher-based reranker for highest quality reranking.

    Uses Gemini/Groq to score each candidate's relevance to the
    query. Falls back to local reranker if:
    - Cloud is unavailable
    - Sensitive data is detected
    - The query is too simple to benefit from cloud scoring

    Privacy: checks all text for sensitive data before sending to
    cloud. Falls back to local reranker if sensitive data is found.
    """

    def __init__(self, cloud_adapter: Any | None = None) -> None:
        self.cloud = cloud_adapter
        self.local = LocalReranker()

    def _build_rerank_prompt(
        self, query: str, candidates: list[dict[str, Any]]
    ) -> str:
        """Build a prompt for the cloud teacher to score candidates."""
        prompt = f"Query: {query}\n\nScore each candidate's relevance to the query (0.0 to 1.0).\n\n"
        for i, cand in enumerate(candidates):
            content = cand.get("content", "")[:500]  # truncate for token limit
            prompt += f"Candidate {i}: {content}\n\n"
        prompt += "Respond with ONLY a JSON list of scores, e.g. [0.9, 0.3, 0.7]. No other text."
        return prompt

    def _parse_scores(self, response: str, count: int) -> list[float] | None:
        """Parse cloud teacher's response into scores."""
        import json
        # Try to extract JSON array from response
        try:
            # Find the JSON array in the response
            start = response.find("[")
            end = response.rfind("]")
            if start == -1 or end == -1:
                return None
            scores = json.loads(response[start:end + 1])
            if isinstance(scores, list) and len(scores) == count:
                return [float(s) for s in scores]
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return None

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank candidates using cloud teacher, with local fallback.

        Args:
            query: The search query
            candidates: List of dicts with "id" and "content" keys
            top_k: Number of results to return

        Returns:
            List of RerankResult sorted by reranked score
        """
        if not candidates:
            return []

        # If no cloud adapter, use local
        if self.cloud is None:
            return self.local.rerank(query, candidates, top_k=top_k)

        # Privacy check — fall back to local if sensitive
        all_text = query + " " + " ".join(c.get("content", "") for c in candidates)
        if _check_sensitive_data(all_text):
            return self.local.rerank(query, candidates, top_k=top_k)

        # Try cloud reranking
        try:
            prompt = self._build_rerank_prompt(query, candidates)
            completion = self.cloud.generate(
                prompt,
                system="You are a relevance scoring assistant. Score candidates precisely.",
                temperature=0.1,
                max_tokens=200,
            )
            scores = self._parse_scores(completion.text, len(candidates))
            if scores is None:
                return self.local.rerank(query, candidates, top_k=top_k)

            # Sort by cloud score
            scored = list(enumerate(scores))
            scored.sort(key=lambda x: -x[1])

            results = []
            for new_rank, (orig_rank, score) in enumerate(scored[:top_k]):
                cand = candidates[orig_rank]
                results.append(RerankResult(
                    id=cand.get("id", str(orig_rank)),
                    score=score,
                    original_rank=orig_rank,
                    reranked_rank=new_rank,
                    content=cand.get("content", ""),
                    metadata=cand.get("metadata", {}),
                ))
            return results

        except Exception:
            # Any cloud failure → local fallback
            return self.local.rerank(query, candidates, top_k=top_k)


class HybridReranker:
    """Hybrid reranker that combines local and cloud scoring.

    Uses both local (BM25) and cloud (teacher) scoring, then combines
    the scores with configurable weights. This gives the best of both:
    exact keyword matching from local + semantic understanding from cloud.

    Falls back to local-only if cloud is unavailable or sensitive.
    """

    def __init__(
        self,
        cloud_adapter: Any | None = None,
        local_weight: float = 0.3,
        cloud_weight: float = 0.7,
    ) -> None:
        self.cloud_reranker = CloudReranker(cloud_adapter)
        self.local_reranker = LocalReranker()
        self.local_weight = local_weight
        self.cloud_weight = cloud_weight

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Rerank using both local and cloud scores, combined."""
        if not candidates:
            return []

        # Get local scores
        local_results = self.local_reranker.rerank(query, candidates, top_k=len(candidates))
        local_scores = {r.id: r.score for r in local_results}

        # Normalize local scores to 0-1
        max_local = max(local_scores.values()) if local_scores else 1.0
        if max_local > 0:
            local_scores = {k: v / max_local for k, v in local_scores.items()}

        # Get cloud scores
        cloud_results = self.cloud_reranker.rerank(query, candidates, top_k=len(candidates))
        cloud_scores = {r.id: r.score for r in cloud_results}

        # Check if cloud was used (scores are 0-1) or fell back to local
        # If cloud was used, combine; otherwise just use local
        is_cloud_used = (
            self.cloud_reranker.cloud is not None
            and not _check_sensitive_data(
                query + " " + " ".join(c.get("content", "") for c in candidates)
            )
        )

        # Combine scores
        combined: list[tuple[str, float, int, dict[str, Any]]] = []
        for i, cand in enumerate(candidates):
            cid = cand.get("id", str(i))
            local_s = local_scores.get(cid, 0.0)
            if is_cloud_used:
                cloud_s = cloud_scores.get(cid, 0.0)
                combined_score = (
                    self.local_weight * local_s + self.cloud_weight * cloud_s
                )
            else:
                combined_score = local_s
            combined.append((cid, combined_score, i, cand))

        combined.sort(key=lambda x: -x[1])

        results = []
        for new_rank, (cid, score, orig_rank, cand) in enumerate(combined[:top_k]):
            results.append(RerankResult(
                id=cid,
                score=score,
                original_rank=orig_rank,
                reranked_rank=new_rank,
                content=cand.get("content", ""),
                metadata=cand.get("metadata", {}),
            ))
        return results


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int = 5,
    cloud_adapter: Any | None = None,
    strategy: str = "hybrid",
) -> list[RerankResult]:
    """Convenience function to rerank candidates.

    Args:
        query: The search query
        candidates: List of dicts with "id" and "content" keys
        top_k: Number of results to return
        cloud_adapter: Cloud model adapter (for cloud/hybrid strategy)
        strategy: "local", "cloud", or "hybrid"

    Returns:
        List of RerankResult sorted by reranked score
    """
    if strategy == "local":
        return LocalReranker().rerank(query, candidates, top_k=top_k)
    elif strategy == "cloud":
        return CloudReranker(cloud_adapter).rerank(query, candidates, top_k=top_k)
    else:  # hybrid
        return HybridReranker(cloud_adapter).rerank(query, candidates, top_k=top_k)
