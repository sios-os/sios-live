"""Knowledge grounding for ANUBIS.

Wires the knowledge library and claim index into the model adapter
so ANUBIS grounds his answers in governed K3 content instead of
relying solely on base model weights.

When ANUBIS receives a user message, the grounding module:
  1. Retrieves the most relevant documents from the knowledge library
  2. Searches the claim index for supporting atomic claims
  3. Reranks results using local BM25 + optional cloud teacher
  4. Formats both into a structured context block
  5. Returns a grounding string to inject into the system prompt

This implements the retrieval-augmented generation (RAG) pattern
with two-stage retrieval (vector + reranker) using only the Python
standard library.
"""

from __future__ import annotations

from typing import Any

from anubis.knowledge import KnowledgeBase, KnowledgeDocument
from anubis.verification import ClaimIndex
from anubis.reranker import LocalReranker, RerankResult


class KnowledgeGrounding:
    """Retrieve and format knowledge context for ANUBIS prompts.

    Uses semantic search (embeddings) when available, falling back to
    keyword-based retrieval. Results are reranked with a local BM25
    reranker for improved relevance.
    """

    def __init__(
        self,
        kb: KnowledgeBase,
        index: ClaimIndex | None = None,
        semantic: Any = None,
        reranker: Any = None,
    ) -> None:
        self.kb = kb
        self.index = index or ClaimIndex()
        if self.index.size == 0:
            self.index.build_from_library(kb)
        self._semantic = semantic
        self._reranker = reranker or LocalReranker()

    def _retrieve_docs(
        self, query: str, specialty_id: str, limit: int
    ) -> list[KnowledgeDocument]:
        """Retrieve documents using semantic search if available, else keyword.

        After initial retrieval, results are reranked using the local
        BM25 reranker for improved keyword relevance.
        """
        if self._semantic and self._semantic.is_ready():
            # Over-fetch for reranking (get 3x more, then rerank to top_k)
            fetch_k = limit * 3
            results = self._semantic.search(query, top_k=fetch_k, specialty_id=specialty_id or None)
            docs: list[KnowledgeDocument] = []
            for r in results:
                doc = self.kb.get_document(r.doc_id)
                if doc:
                    docs.append(doc)
            # If semantic returned too few, supplement with keyword search
            if len(docs) < limit:
                kw_docs = self.kb.retrieve(query, specialty_id=specialty_id, limit=limit)
                existing = {d.doc_id for d in docs}
                for d in kw_docs:
                    if d.doc_id not in existing and len(docs) < fetch_k:
                        docs.append(d)
            # Rerank using BM25
            docs = self._rerank_docs(query, docs, limit)
            return docs
        # No semantic — use keyword search, still rerank
        docs = self.kb.retrieve(query, specialty_id=specialty_id, limit=limit * 2)
        docs = self._rerank_docs(query, docs, limit)
        return docs

    def _rerank_docs(
        self, query: str, docs: list[KnowledgeDocument], limit: int
    ) -> list[KnowledgeDocument]:
        """Rerank documents using the local BM25 reranker."""
        if not docs or len(docs) <= 1:
            return docs[:limit]
        candidates = [
            {
                "id": d.doc_id,
                "content": f"{d.title}. {d.content[:500]}",
                "metadata": {"doc_id": d.doc_id},
            }
            for d in docs
        ]
        try:
            reranked = self._reranker.rerank(query, candidates, top_k=limit)
            # Map back to KnowledgeDocument, preserving reranked order
            doc_map = {d.doc_id: d for d in docs}
            result = []
            for r in reranked:
                doc = doc_map.get(r.id)
                if doc:
                    result.append(doc)
            # If reranker returned fewer than limit, fill with remaining
            if len(result) < limit:
                existing = {d.doc_id for d in result}
                for d in docs:
                    if d.doc_id not in existing and len(result) < limit:
                        result.append(d)
            return result[:limit]
        except Exception:
            # Reranker failure → return original order
            return docs[:limit]

    def ground(
        self,
        query: str,
        *,
        max_docs: int = 3,
        max_claims: int = 10,
        specialty_id: str = "",
    ) -> str:
        """Retrieve and format knowledge context for a user query.

        Returns a string to append to the system prompt, or empty
        string if no relevant knowledge was found.
        """
        docs = self._retrieve_docs(query, specialty_id, max_docs)
        claims = self.index.search(query, limit=max_claims)

        # Boost: if claims reference documents not in docs, add them
        claim_doc_ids = {c.get("doc_id", "") for c in claims if c.get("doc_id")}
        existing_doc_ids = {d.doc_id for d in docs}
        for doc in self.kb.library_documents():
            if doc.doc_id in claim_doc_ids and doc.doc_id not in existing_doc_ids and len(docs) < max_docs + 2:
                docs.append(doc)
                existing_doc_ids.add(doc.doc_id)

        if not docs and not claims:
            return ""

        parts: list[str] = ["=== GOVERNED KNOWLEDGE CONTEXT ==="]
        parts.append(
            "The following information is retrieved from your governed "
            "knowledge library (550 documents, 15,677 verified claims). "
            "Use it to ground your answer. Cite the source document when "
            "you use specific facts."
        )
        parts.append("")

        if docs:
            parts.append("--- Relevant Documents ---")
            for doc in docs:
                parts.append(f"[{doc.title}]")
                # Include a meaningful excerpt
                excerpt = doc.content[:600]
                if len(doc.content) > 600:
                    excerpt += "..."
                parts.append(excerpt)
                if doc.tags:
                    parts.append(f"Tags: {', '.join(doc.tags[:5])}")
                parts.append("")

        if claims:
            parts.append("--- Supporting Claims ---")
            for claim in claims:
                ct = claim.get("claim_type", "fact")
                conf = claim.get("confidence_adjusted", claim.get("confidence", 0.8))
                status = claim.get("verification_status", "unverified")
                text = claim.get("text", "")
                parts.append(f"  [{ct}|{status}|conf={conf:.2f}] {text}")
            parts.append("")

        parts.append("=== END KNOWLEDGE CONTEXT ===")
        return "\n".join(parts)

    def ground_with_citations(
        self,
        query: str,
        *,
        max_docs: int = 3,
        max_claims: int = 10,
        specialty_id: str = "",
    ) -> dict[str, Any]:
        """Like ground() but also returns structured citation data.

        Returns a dict with:
          - context: the formatted string for the system prompt
          - citations: list of document titles used
          - claims_used: list of claim texts
          - doc_ids: list of document IDs
        """
        docs = self._retrieve_docs(query, specialty_id, max_docs)
        claims = self.index.search(query, limit=max_claims)

        context = self.ground(
            query, max_docs=max_docs, max_claims=max_claims, specialty_id=specialty_id
        )

        return {
            "context": context,
            "citations": [d.title for d in docs],
            "doc_ids": [d.doc_id for d in docs],
            "claims_used": [c.get("text", "") for c in claims],
            "claim_ids": [c.get("claim_id", "") for c in claims],
        }

    def stats(self) -> dict[str, Any]:
        """Return grounding system stats."""
        s = {
            "library_size": self.kb.library_size(),
            "claims_indexed": self.index.size,
            "index_stats": self.index.stats(),
            "semantic_enabled": self._semantic is not None and self._semantic.is_ready(),
        }
        if self._semantic:
            s["semantic_stats"] = self._semantic.stats()
        return s
