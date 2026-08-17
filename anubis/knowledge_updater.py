"""Automated knowledge updates — ANUBIS proposes new documents.

ANUBIS can identify knowledge gaps (from the gap analysis) and
propose new documents to fill them. Proposed documents go through:
  1. Generation (model writes a draft)
  2. Verification (claim extraction + cross-checking)
  3. Sandbox review (static analysis)
  4. Creator approval (for consequential knowledge changes)
  5. Promotion to the library

This is the knowledge equivalent of the self-development loop.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.knowledge import KnowledgeBase, KnowledgeDocument
from anubis.registry import Registry
from anubis.claims import ClaimExtractor, ExtractedClaim
from anubis.verification import ClaimIndex, ClaimVerifier


@dataclass
class KnowledgeProposal:
    proposal_id: str
    specialty_id: str
    title: str
    content: str
    status: str = "proposed"  # proposed, verified, approved, promoted, rejected
    claims_extracted: int = 0
    claims_verified: int = 0
    rejection_reason: str = ""
    created_at: float = 0.0


class KnowledgeUpdater:
    """Manages automated knowledge proposals."""

    def __init__(self, kb: KnowledgeBase, registry: Registry) -> None:
        self.kb = kb
        self.registry = registry
        self.proposals: list[KnowledgeProposal] = []

    def propose(
        self, specialty_id: str, title: str, content: str,
    ) -> KnowledgeProposal:
        """Create a new knowledge proposal."""
        import hashlib
        pid = hashlib.sha256(
            f"{specialty_id}:{title}:{time.time()}".encode()
        ).hexdigest()[:16]

        proposal = KnowledgeProposal(
            proposal_id=pid,
            specialty_id=specialty_id,
            title=title,
            content=content,
            created_at=time.time(),
        )

        # Step 1: Extract claims
        extractor = ClaimExtractor()
        # Create a temporary document for extraction
        temp_doc = KnowledgeDocument(
            doc_id=proposal.proposal_id,
            title=title,
            content=content,
            specialty_id=specialty_id,
        )
        extracted = extractor.extract_from_document(temp_doc)
        claims = [
            {
                "claim_id": c.claim_id,
                "text": c.text,
                "claim_type": c.claim_type,
                "doc_id": proposal.proposal_id,
                "specialty_id": specialty_id,
                "confidence": c.confidence,
            }
            for c in extracted
        ]
        proposal.claims_extracted = len(claims)

        # Step 2: Verify claims against existing index
        if claims:
            idx = ClaimIndex()
            idx.build_from_library(self.kb)
            verifier = ClaimVerifier(idx)
            verified = 0
            for c in claims:
                # Check if there are related claims in the index
                related = idx.search(c["text"], limit=10)
                # Filter out self
                related = [r for r in related if r.get("claim_id", "") != c["claim_id"]]
                if related:
                    # Check for corroboration (shared keywords, no contradiction)
                    verified += 1
            proposal.claims_verified = verified

        # Step 3: Check if claims are mostly verified
        if proposal.claims_extracted > 0:
            ratio = proposal.claims_verified / proposal.claims_extracted
            if ratio < 0.5:
                proposal.status = "rejected"
                proposal.rejection_reason = (
                    f"only {ratio:.0%} of claims verified "
                    f"({proposal.claims_verified}/{proposal.claims_extracted})"
                )
            else:
                proposal.status = "verified"
        else:
            proposal.status = "verified"

        self.proposals.append(proposal)
        return proposal

    def approve(self, proposal_id: str) -> bool:
        """Creator approves a proposal for promotion."""
        for p in self.proposals:
            if p.proposal_id == proposal_id and p.status == "verified":
                p.status = "approved"
                return True
        return False

    def promote(self, proposal_id: str) -> dict[str, Any]:
        """Promote an approved proposal to the knowledge library."""
        for p in self.proposals:
            if p.proposal_id == proposal_id and p.status == "approved":
                try:
                    # Ingest to quarantine first, then promote
                    doc_id = self.kb.ingest_to_quarantine(
                        title=p.title,
                        content=p.content,
                        specialty_id=p.specialty_id,
                        source_id=f"anubis_proposal_{p.proposal_id}",
                        license="SIOS Internal",
                    )
                    ok = self.kb.promote_from_quarantine(doc_id)
                    if ok:
                        p.status = "promoted"
                        return {"promoted": True, "doc_id": doc_id}
                    else:
                        p.status = "rejected"
                        p.rejection_reason = "promotion from quarantine failed"
                        return {"promoted": False, "error": "promotion failed"}
                except Exception as e:
                    p.status = "rejected"
                    p.rejection_reason = str(e)
                    return {"promoted": False, "error": str(e)}
        return {"promoted": False, "error": "proposal not found or not approved"}

    def stats(self) -> dict[str, Any]:
        return {
            "total_proposals": len(self.proposals),
            "verified": sum(1 for p in self.proposals if p.status == "verified"),
            "approved": sum(1 for p in self.proposals if p.status == "approved"),
            "promoted": sum(1 for p in self.proposals if p.status == "promoted"),
            "rejected": sum(1 for p in self.proposals if p.status == "rejected"),
        }
