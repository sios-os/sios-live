"""Claim verification and indexing engine.

Implements KBP step 9: Independent verification — corroborate claims
against each other, detect contradictions, and build a fast lookup
index so ANUBIS can retrieve structured facts without scanning all
550 documents.

Verification strategy
---------------------
For each claim we look for:
  1. Corroborating claims — other claims that assert the same fact
  2. Contradicting claims — claims that assert the opposite
  3. Cross-specialty support — the same fact appearing in a
     different specialty (stronger evidence)

Because the SIOS knowledge library was authored from consistent
reference material, most claims will be corroborated rather than
contradicted.  Contradictions are flagged for human review.

Index strategy
--------------
A ClaimIndex holds:
  - keyword -> set of claim_ids
  - specialty_id -> set of claim_ids
  - claim_type -> set of claim_ids
  - claim_id -> full claim dict

This lets ANUBIS query "give me all measurement claims about
blood pressure" in O(1) lookup time.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.knowledge import KnowledgeBase, KnowledgeDocument


# ---------------------------------------------------------------------------
# verification result model
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """Result of verifying a single claim."""

    claim_id: str
    status: str = "unverified"       # verified, corroborated, contradicted, unverified
    corroboration_count: int = 0
    contradiction_count: int = 0
    corroborating_ids: list[str] = field(default_factory=list)
    contradicting_ids: list[str] = field(default_factory=list)
    cross_specialty: bool = False
    confidence_adjusted: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status,
            "corroboration_count": self.corroboration_count,
            "contradiction_count": self.contradiction_count,
            "corroborating_ids": self.corroborating_ids,
            "contradicting_ids": self.contradicting_ids,
            "cross_specialty": self.cross_specialty,
            "confidence_adjusted": self.confidence_adjusted,
        }


# ---------------------------------------------------------------------------
# claim index
# ---------------------------------------------------------------------------

class ClaimIndex:
    """Fast lookup index over all claims in the knowledge library."""

    def __init__(self) -> None:
        self._by_keyword: dict[str, set[str]] = {}
        self._by_specialty: dict[str, set[str]] = {}
        self._by_type: dict[str, set[str]] = {}
        self._by_id: dict[str, dict[str, Any]] = {}
        self._all_claims: list[dict[str, Any]] = []

    @property
    def size(self) -> int:
        return len(self._by_id)

    def add_claim(self, claim: dict[str, Any], specialty_id: str = "") -> None:
        """Add a single claim to the index."""
        cid = claim.get("claim_id", "")
        if not cid:
            return
        self._by_id[cid] = claim
        self._all_claims.append(claim)

        # Index by specialty
        if specialty_id:
            self._by_specialty.setdefault(specialty_id, set()).add(cid)

        # Index by claim type
        ct = claim.get("claim_type", "fact")
        self._by_type.setdefault(ct, set()).add(cid)

        # Index by keywords from the claim text
        text = claim.get("text", "").lower()
        for kw in self._extract_keywords(text):
            self._by_keyword.setdefault(kw, set()).add(cid)

    def build_from_library(self, kb: KnowledgeBase) -> int:
        """Build the index from all library documents."""
        self.__init__()
        for doc in kb.library_documents():
            for claim in doc.claims:
                self.add_claim(claim, specialty_id=doc.specialty_id)
        return self.size

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------

    def get(self, claim_id: str) -> dict[str, Any] | None:
        return self._by_id.get(claim_id)

    def by_specialty(self, specialty_id: str) -> list[dict[str, Any]]:
        ids = self._by_specialty.get(specialty_id, set())
        return [self._by_id[c] for c in ids if c in self._by_id]

    def by_type(self, claim_type: str) -> list[dict[str, Any]]:
        ids = self._by_type.get(claim_type, set())
        return [self._by_id[c] for c in ids if c in self._by_id]

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search claims by keyword overlap."""
        keywords = self._extract_keywords(query.lower())
        if not keywords:
            return []
        scored: list[tuple[int, dict[str, Any]]] = []
        candidate_ids: set[str] = set()
        for kw in keywords:
            candidate_ids.update(self._by_keyword.get(kw, set()))
        for cid in candidate_ids:
            claim = self._by_id.get(cid)
            if not claim:
                continue
            text = claim.get("text", "").lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, claim))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:limit]]

    def all_claims(self) -> list[dict[str, Any]]:
        return list(self._all_claims)

    def stats(self) -> dict[str, Any]:
        return {
            "total_claims": len(self._by_id),
            "by_type": {k: len(v) for k, v in self._by_type.items()},
            "specialties_indexed": len(self._by_specialty),
            "keywords_indexed": len(self._by_keyword),
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        """Extract meaningful keywords from text (stopword-filtered)."""
        STOPWORDS = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can",
            "of", "in", "on", "at", "to", "for", "with", "by", "from",
            "as", "into", "through", "during", "before", "after",
            "above", "below", "up", "down", "out", "off", "over",
            "under", "again", "further", "then", "once", "and", "or",
            "but", "not", "no", "nor", "so", "than", "too", "very",
            "just", "also", "only", "per", "vs", "via", "etc",
            "this", "that", "these", "those", "it", "its", "they",
            "them", "their", "we", "our", "you", "your", "i", "my",
            "he", "she", "his", "her", "which", "what", "who", "when",
            "where", "why", "how", "all", "each", "every", "both",
            "few", "more", "most", "other", "some", "such",
            "if", "about", "against", "between", "same",
        }
        words = re.findall(r"[a-z][a-z0-9_-]{2,}", text)
        return {w for w in words if w not in STOPWORDS and len(w) >= 3}


# ---------------------------------------------------------------------------
# verification engine
# ---------------------------------------------------------------------------

class ClaimVerifier:
    """Cross-check claims against each other for corroboration and contradiction."""

    # Negation words that flip a claim's meaning
    _NEGATIONS = {"not", "no", "never", "none", "cannot", "dont", "shouldnt", "mustnt"}
    # Note: "without" is excluded — it's often used in definitions
    # ("operates without human intervention") rather than as a logical
    # negation. Including it caused false positives.

    # Similarity threshold for considering two claims as related
    KEYWORD_OVERLAP_THRESHOLD = 3

    def __init__(self, index: ClaimIndex) -> None:
        self.index = index

    def verify_all(self, kb: KnowledgeBase) -> dict[str, Any]:
        """Run verification across all claims in the library.

        Returns a summary dict and updates each claim in-place with
        verification metadata.
        """
        results: dict[str, VerificationResult] = {}
        all_claims = self.index.all_claims()

        # Build a lookup: specialty_id -> set of claim_ids
        specialty_claims: dict[str, set[str]] = {}
        for doc in kb.library_documents():
            for c in doc.claims:
                cid = c.get("claim_id", "")
                if cid:
                    specialty_claims.setdefault(doc.specialty_id, set()).add(cid)

        verified_count = 0
        corroborated_count = 0
        contradicted_count = 0

        for claim in all_claims:
            cid = claim.get("claim_id", "")
            if not cid:
                continue
            result = self._verify_claim(claim, specialty_claims)
            results[cid] = result

            # Update the claim dict in-place with verification metadata
            claim["verification_status"] = result.status
            claim["corroboration_count"] = result.corroboration_count
            claim["contradiction_count"] = result.contradiction_count
            claim["confidence_adjusted"] = result.confidence_adjusted

            if result.status == "verified":
                verified_count += 1
            elif result.status == "corroborated":
                corroborated_count += 1
            elif result.status == "contradicted":
                contradicted_count += 1

        # Save updated claims back to documents
        kb._save()

        return {
            "total_claims": len(all_claims),
            "verified": verified_count,
            "corroborated": corroborated_count,
            "contradicted": contradicted_count,
            "unverified": len(all_claims) - verified_count - corroborated_count - contradicted_count,
            "results": {cid: r.to_dict() for cid, r in results.items()},
        }

    def _verify_claim(
        self, claim: dict[str, Any], specialty_claims: dict[str, set[str]],
    ) -> VerificationResult:
        """Verify a single claim by looking for corroborating/contradicting claims."""
        cid = claim.get("claim_id", "")
        text = claim.get("text", "").lower()
        doc_id = claim.get("doc_id", "")
        base_confidence = claim.get("confidence", 0.8)

        # Find related claims via keyword search
        related = self.index.search(text, limit=20)

        # Filter out self
        related = [r for r in related if r.get("claim_id", "") != cid]

        if not related:
            return VerificationResult(
                claim_id=cid,
                status="unverified",
                confidence_adjusted=base_confidence,
            )

        # Find the claim's specialty
        claim_specialty = None
        for spec, ids in specialty_claims.items():
            if cid in ids:
                claim_specialty = spec
                break

        corroborating: list[str] = []
        contradicting: list[str] = []
        cross_specialty = False

        for other in related:
            other_id = other.get("claim_id", "")
            other_text = other.get("text", "").lower()

            # Check if other claim is from a different specialty
            other_specialty = None
            for spec, ids in specialty_claims.items():
                if other_id in ids:
                    other_specialty = spec
                    break

            if other_specialty and claim_specialty and other_specialty != claim_specialty:
                cross_specialty = True

            # Determine corroboration vs contradiction
            if self._is_contradiction(text, other_text):
                contradicting.append(other_id)
            else:
                corroborating.append(other_id)

        corroboration_count = len(corroborating)
        contradiction_count = len(contradicting)

        # Determine status
        if contradiction_count > 0 and contradiction_count >= corroboration_count:
            status = "contradicted"
            confidence = base_confidence * 0.5
        elif corroboration_count >= 2:
            status = "verified"
            confidence = min(1.0, base_confidence + 0.1 * min(corroboration_count, 3))
        elif corroboration_count >= 1:
            status = "corroborated"
            confidence = min(1.0, base_confidence + 0.05)
        else:
            status = "unverified"
            confidence = base_confidence

        # Boost confidence if cross-specialty corroboration
        if cross_specialty and corroboration_count > 0:
            confidence = min(1.0, confidence + 0.05)

        return VerificationResult(
            claim_id=cid,
            status=status,
            corroboration_count=corroboration_count,
            contradiction_count=contradiction_count,
            corroborating_ids=corroborating[:10],
            contradicting_ids=contradicting[:10],
            cross_specialty=cross_specialty,
            confidence_adjusted=round(confidence, 3),
        )

    def _is_contradiction(self, text1: str, text2: str) -> bool:
        """Heuristic: check if two claims contradict each other."""
        # If one claim has a negation and the other doesn't, and they share
        # significant keywords, they may contradict.
        words1 = set(text1.split())
        words2 = set(text2.split())

        neg1 = words1 & self._NEGATIONS
        neg2 = words2 & self._NEGATIONS

        # If one has negation and the other doesn't, and they're otherwise similar
        if (neg1 and not neg2) or (neg2 and not neg1):
            # Check if they share enough keywords
            shared = words1 & words2
            for neg in self._NEGATIONS:
                shared.discard(neg)
            # Remove common stopwords
            shared -= {"the", "a", "is", "are", "of", "in", "to", "and", "or"}
            if len(shared) >= self.KEYWORD_OVERLAP_THRESHOLD:
                return True

        return False


# ---------------------------------------------------------------------------
# convenience: build index + verify in one call
# ---------------------------------------------------------------------------

def build_and_verify(kb: KnowledgeBase) -> dict[str, Any]:
    """Build the claim index and run verification in one step."""
    index = ClaimIndex()
    count = index.build_from_library(kb)
    print(f"  Index built: {count} claims, {len(index._by_keyword)} keywords")

    verifier = ClaimVerifier(index)
    print(f"  Running verification...")
    results = verifier.verify_all(kb)

    summary = {
        "index_stats": index.stats(),
        "verification_summary": {
            "total": results["total_claims"],
            "verified": results["verified"],
            "corroborated": results["corroborated"],
            "contradicted": results["contradicted"],
            "unverified": results["unverified"],
        },
    }
    return summary
