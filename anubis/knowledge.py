"""SIOS Knowledge Base.

Implements the four separated stores from the KBP plan:
  - Active context: short-lived reasoning workspace (in-memory)
  - Durable memory: identity and lived continuity (anubis/memory.py)
  - Knowledge library: versioned reference material (this module)
  - Experimental quarantine: untrusted learning material (this module)

The knowledge library stores documents with full provenance:
  - Source identity, publisher, date, license, version
  - Trust tier and verification status
  - Atomic claims linked to supporting evidence
  - Retrieval by keyword, specialty, or semantic similarity

ANUBIS retrieves relevant passages before attempting a task, instead
of relying solely on model weights.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from anubis.registry import Registry, SourceTier, SourceClass, KnowledgeDepth


@dataclass
class KnowledgeDocument:
    """A document in the knowledge library."""
    doc_id: str
    title: str
    content: str
    source_id: str = ""
    specialty_id: str = ""
    trust_tier: int = SourceTier.T5
    license: str = ""
    version: str = ""
    date_added: float = 0.0
    content_hash: str = ""
    tags: list[str] = field(default_factory=list)
    # Atomic claims extracted from this document
    claims: list[dict[str, Any]] = field(default_factory=list)
    # Verification status
    verified: bool = False
    verification_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "source_id": self.source_id,
            "specialty_id": self.specialty_id,
            "trust_tier": self.trust_tier,
            "license": self.license,
            "version": self.version,
            "date_added": self.date_added,
            "content_hash": self.content_hash,
            "tags": self.tags,
            "claims": self.claims,
            "verified": self.verified,
            "verification_notes": self.verification_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeDocument":
        return cls(
            doc_id=data.get("doc_id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            source_id=data.get("source_id", ""),
            specialty_id=data.get("specialty_id", ""),
            trust_tier=data.get("trust_tier", SourceTier.T5),
            license=data.get("license", ""),
            version=data.get("version", ""),
            date_added=data.get("date_added", 0.0),
            content_hash=data.get("content_hash", ""),
            tags=data.get("tags", []),
            claims=data.get("claims", []),
            verified=data.get("verified", False),
            verification_notes=data.get("verification_notes", ""),
        )


@dataclass
class Claim:
    """An atomic claim linked to supporting evidence."""
    claim_id: str
    text: str
    doc_id: str
    supporting_evidence: list[str] = field(default_factory=list)
    opposing_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    jurisdiction: str = ""
    effective_date: str = ""
    expiry_date: str = ""


class KnowledgeBase:
    """The knowledge library and quarantine store.

    Documents enter through quarantine and are promoted to the library
    only after verification. ANUBIS retrieves from the library, not
    from quarantine.
    """

    def __init__(self, root: str | Path, registry: Registry) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._library_dir = self.root / "library"
        self._quarantine_dir = self.root / "quarantine"
        self._library_dir.mkdir(exist_ok=True)
        self._quarantine_dir.mkdir(exist_ok=True)
        self._index_path = self.root / "index.json"
        self._registry = registry
        self._library: dict[str, KnowledgeDocument] = {}
        self._quarantine: dict[str, KnowledgeDocument] = {}
        self._load()

    def _load(self) -> None:
        """Load the document index."""
        if self._index_path.exists():
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            for d in data.get("library", []):
                doc = KnowledgeDocument.from_dict(d)
                self._library[doc.doc_id] = doc
            for d in data.get("quarantine", []):
                doc = KnowledgeDocument.from_dict(d)
                self._quarantine[doc.doc_id] = doc

    def _save(self) -> None:
        """Save the document index."""
        self._index_path.write_text(
            json.dumps({
                "library": [d.to_dict() for d in self._library.values()],
                "quarantine": [d.to_dict() for d in self._quarantine.values()],
            }, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _make_doc_id(title: str) -> str:
        """Create a document ID from a title."""
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return f"doc_{slug}_{int(time.time()) % 100000}"

    # ------------------------------------------------------------------ ingest

    def ingest_to_quarantine(
        self, title: str, content: str, source_id: str = "",
        specialty_id: str = "", license: str = "", tags: list[str] | None = None,
    ) -> str:
        """Add a document to quarantine. Returns the doc_id."""
        doc_id = self._make_doc_id(title)
        doc = KnowledgeDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            source_id=source_id,
            specialty_id=specialty_id,
            trust_tier=SourceTier.Q,
            license=license,
            version="1.0",
            date_added=time.time(),
            content_hash=self._hash_content(content),
            tags=tags or [],
            verified=False,
        )
        self._quarantine[doc_id] = doc
        self._save()
        return doc_id

    def promote_from_quarantine(
        self, doc_id: str, trust_tier: int = SourceTier.T3,
        verification_notes: str = "",
    ) -> bool:
        """Promote a document from quarantine to the trusted library."""
        doc = self._quarantine.pop(doc_id, None)
        if doc is None:
            return False
        doc.trust_tier = trust_tier
        doc.verified = True
        doc.verification_notes = verification_notes
        self._library[doc_id] = doc
        self._save()
        return True

    def reject_from_quarantine(self, doc_id: str, reason: str = "") -> bool:
        """Reject and remove a quarantined document."""
        if doc_id in self._quarantine:
            del self._quarantine[doc_id]
            self._save()
            return True
        return False

    # ------------------------------------------------------------------ retrieve

    def retrieve(
        self, query: str, specialty_id: str = "", limit: int = 5,
        min_tier: int = SourceTier.T5,
    ) -> list[KnowledgeDocument]:
        """Retrieve relevant documents from the trusted library.

        Uses simple keyword matching. A future version could use
        embeddings for semantic search.
        """
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return []

        scored: list[tuple[float, KnowledgeDocument]] = []
        for doc in self._library.values():
            if doc.trust_tier > min_tier:
                continue
            if specialty_id and doc.specialty_id != specialty_id:
                continue
            # Score by keyword overlap
            doc_terms = set(re.findall(r"\w+", doc.title.lower()))
            doc_terms.update(set(re.findall(r"\w+", doc.content.lower())))
            doc_terms.update(set(t.lower() for t in doc.tags))
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                # Weight by trust tier (lower tier = higher trust = higher score)
                trust_weight = 1.0 / (doc.trust_tier + 1)
                score = overlap * trust_weight
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:limit]]

    def retrieve_context(self, query: str, specialty_id: str = "", limit: int = 3) -> str:
        """Retrieve and format context for injection into ANUBIS prompts."""
        docs = self.retrieve(query, specialty_id=specialty_id, limit=limit)
        if not docs:
            return ""
        parts = ["=== KNOWLEDGE LIBRARY ==="]
        for doc in docs:
            tier_name = SourceTier(doc.trust_tier).name if doc.trust_tier < 9 else "QUARANTINE"
            parts.append(f"[{tier_name}] {doc.title}")
            # Include first 500 chars of content
            excerpt = doc.content[:500]
            if len(doc.content) > 500:
                excerpt += "..."
            parts.append(excerpt)
            if doc.license:
                parts.append(f"License: {doc.license}")
            parts.append("")
        return "\n".join(parts)

    # ------------------------------------------------------------------ queries

    def library_documents(self) -> list[KnowledgeDocument]:
        return list(self._library.values())

    def quarantine_documents(self) -> list[KnowledgeDocument]:
        return list(self._quarantine.values())

    def get_document(self, doc_id: str) -> KnowledgeDocument | None:
        return self._library.get(doc_id) or self._quarantine.get(doc_id)

    def library_size(self) -> int:
        return len(self._library)

    def quarantine_size(self) -> int:
        return len(self._quarantine)

    def stats(self) -> dict[str, Any]:
        tier_counts = {}
        for doc in self._library.values():
            tier_counts[doc.trust_tier] = tier_counts.get(doc.trust_tier, 0) + 1
        return {
            "library_size": len(self._library),
            "quarantine_size": len(self._quarantine),
            "total_claims": sum(len(d.claims) for d in self._library.values()),
            "tier_distribution": tier_counts,
            "verified_docs": sum(1 for d in self._library.values() if d.verified),
        }


# ------------------------------------------------------------------ population pipeline

class PopulationPipeline:
    """The controlled population pipeline from the KBP plan.

    Steps:
      1. Register — create specialty identity
      2. Map — build field ontology
      3. Design curriculum — declare learning objectives
      4. Discover sources — search approved catalogs
      5. License review — resolve ownership and permissions
      6. Quarantine acquisition — download to isolated area
      7. Parse and normalize — extract structure
      8. Evidence extraction — create atomic claims
      9. Independent verification — corroborate claims
      10. Index and package — build versioned pack
      11. Evaluate — run benchmarks
      12. Promote — move to trusted library
      13. Observe outcomes — compare with later results
      14. Maintain — watch for updates and expiry
    """

    def __init__(self, registry: Registry, knowledge: KnowledgeBase) -> None:
        self.registry = registry
        self.knowledge = knowledge

    def populate_specialty(
        self, specialty_id: str, documents: list[dict[str, Any]],
        creator_approved: bool = False,
    ) -> dict[str, Any]:
        """Populate a specialty with documents through the pipeline.

        Documents enter quarantine, and if creator_approved, are promoted
        to the trusted library immediately. Otherwise they stay in
        quarantine for review.

        Returns a summary of the population result.
        """
        spec = self.registry.get_specialty(specialty_id)
        if spec is None:
            return {"error": f"unknown specialty: {specialty_id}"}

        promoted = 0
        quarantined = 0
        for doc_data in documents:
            title = doc_data.get("title", "")
            content = doc_data.get("content", "")
            source_id = doc_data.get("source_id", "")
            license_text = doc_data.get("license", "")
            tags = doc_data.get("tags", [])
            trust_tier = doc_data.get("trust_tier", SourceTier.T3)

            # Step 6: Quarantine acquisition
            doc_id = self.knowledge.ingest_to_quarantine(
                title=title, content=content, source_id=source_id,
                specialty_id=specialty_id, license=license_text, tags=tags,
            )

            if creator_approved:
                # Steps 9-12: Verify and promote
                notes = doc_data.get("verification_notes", "Creator-approved population")
                if self.knowledge.promote_from_quarantine(doc_id, trust_tier, notes):
                    promoted += 1
            else:
                quarantined += 1

        # Update specialty depth if documents were promoted
        if promoted > 0 and spec.knowledge_depth < KnowledgeDepth.K1:
            self.registry.update_specialty_depth(specialty_id, KnowledgeDepth.K1)

        return {
            "specialty_id": specialty_id,
            "documents_submitted": len(documents),
            "promoted": promoted,
            "quarantined": quarantined,
            "new_depth": self.registry.get_specialty(specialty_id).knowledge_depth if spec else 0,
        }

    def pipeline_status(self, specialty_id: str) -> dict[str, Any]:
        """Get the population status of a specialty."""
        spec = self.registry.get_specialty(specialty_id)
        if spec is None:
            return {"error": f"unknown specialty: {specialty_id}"}
        # Count documents in library and quarantine for this specialty
        lib_docs = [d for d in self.knowledge.library_documents() if d.specialty_id == specialty_id]
        quar_docs = [d for d in self.knowledge.quarantine_documents() if d.specialty_id == specialty_id]
        return {
            "specialty_id": specialty_id,
            "canonical_name": spec.canonical_name,
            "knowledge_depth": spec.knowledge_depth,
            "depth_name": KnowledgeDepth(spec.knowledge_depth).name,
            "evaluation_status": spec.evaluation_status,
            "library_docs": len(lib_docs),
            "quarantine_docs": len(quar_docs),
            "last_verified": spec.last_verified_at,
        }
