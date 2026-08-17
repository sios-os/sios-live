"""Atomic claim extraction from knowledge documents.

Implements KBP step 8: Evidence extraction — create atomic claims
from promoted library documents so ANUBIS can reason over
structured facts rather than only free text.

Extraction strategy
-------------------
The K3 documents in the SIOS knowledge library are structured
Markdown.  Each document is organised into headed sections with
bullet points, numbered lists, and definition-style statements.
This module parses that structure and emits atomic, self-contained
claims that can be independently verified.

A claim is a single factual statement that:
  * can be understood without surrounding context
  * can in principle be verified or refuted
  * is attributed to a source document

Claims are stored on the KnowledgeDocument.claims list as dicts
with the keys: claim_id, text, doc_id, section, claim_type,
confidence.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterator

from anubis.knowledge import KnowledgeBase, KnowledgeDocument


# ---------------------------------------------------------------------------
# claim model
# ---------------------------------------------------------------------------

@dataclass
class ExtractedClaim:
    """A single atomic claim extracted from a document."""

    claim_id: str
    text: str
    doc_id: str
    section: str = ""
    claim_type: str = "fact"          # fact, definition, process, measurement, list
    confidence: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "doc_id": self.doc_id,
            "section": self.section,
            "claim_type": self.claim_type,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# extraction engine
# ---------------------------------------------------------------------------

class ClaimExtractor:
    """Extract atomic claims from structured Markdown documents."""

    # Minimum claim length (characters) to avoid trivial fragments.
    MIN_CLAIM_LEN = 25
    # Maximum claim length — split longer bullets into sentences.
    MAX_CLAIM_LEN = 400

    # Patterns that indicate a bullet is NOT a factual claim.
    _SKIP_PATTERNS = re.compile(
        r"^(?:see |note: |example: |e\.g\. |i\.e\. |cf\. |todo|tbd|placeholder)",
        re.IGNORECASE,
    )

    # Section headers that tend to contain definitions.
    _DEFINITION_SECTIONS = {
        "definition", "overview", "fundamentals", "introduction",
        "what is", "core concepts", "key concepts", "principles",
    }

    # Section headers that tend to contain process steps.
    _PROCESS_SECTIONS = {
        "process", "procedure", "workflow", "steps", "algorithm",
        "method", "protocol", "pipeline", "cycle", "phases",
        "installation", "treatment", "management", "operation",
    }

    # Section headers that tend to contain measurements / specs.
    _MEASUREMENT_SECTIONS = {
        "specifications", "specs", "parameters", "ratings",
        "capacities", "limits", "thresholds", "values",
        "normal ranges", "reference ranges", "standards",
    }

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def extract_from_document(self, doc: KnowledgeDocument) -> list[ExtractedClaim]:
        """Extract all atomic claims from a single document."""
        claims: list[ExtractedClaim] = []
        sections = self._parse_sections(doc.content)

        for section_title, section_body in sections:
            claims.extend(self._extract_from_section(doc, section_title, section_body))

        # Deduplicate by claim text
        seen: set[str] = set()
        unique: list[ExtractedClaim] = []
        for c in claims:
            key = c.text.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def extract_from_library(
        self, kb: KnowledgeBase, specialty_id: str = "",
    ) -> dict[str, list[ExtractedClaim]]:
        """Extract claims from all (or one specialty's) library documents.

        Returns a mapping of doc_id -> list of claims.
        """
        result: dict[str, list[ExtractedClaim]] = {}
        for doc in kb.library_documents():
            if specialty_id and doc.specialty_id != specialty_id:
                continue
            claims = self.extract_from_document(doc)
            if claims:
                result[doc.doc_id] = claims
        return result

    def populate_library(
        self, kb: KnowledgeBase, specialty_id: str = "",
        save: bool = True,
    ) -> dict[str, int]:
        """Extract claims and write them onto the documents in-place.

        Returns a mapping of doc_id -> number of claims stored.
        """
        extracted = self.extract_from_library(kb, specialty_id=specialty_id)
        counts: dict[str, int] = {}
        for doc_id, claims in extracted.items():
            doc = kb.get_document(doc_id)
            if doc is None:
                continue
            doc.claims = [c.to_dict() for c in claims]
            counts[doc_id] = len(claims)
        if save and counts:
            kb._save()
        return counts

    # ------------------------------------------------------------------
    # parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_sections(content: str) -> list[tuple[str, str]]:
        """Split Markdown content into (title, body) pairs by header level."""
        lines = content.split("\n")
        sections: list[tuple[str, str]] = []
        current_title = ""
        current_body: list[str] = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                if current_title or current_body:
                    sections.append((current_title, "\n".join(current_body)))
                current_title = header_match.group(2).strip()
                current_body = []
            else:
                current_body.append(line)

        if current_title or current_body:
            sections.append((current_title, "\n".join(current_body)))

        return sections

    def _extract_from_section(
        self, doc: KnowledgeDocument, title: str, body: str,
    ) -> list[ExtractedClaim]:
        """Extract claims from a single section."""
        claims: list[ExtractedClaim] = []
        section_lower = title.lower().strip()

        # Determine the dominant claim type for this section
        if any(k in section_lower for k in self._DEFINITION_SECTIONS):
            default_type = "definition"
        elif any(k in section_lower for k in self._PROCESS_SECTIONS):
            default_type = "process"
        elif any(k in section_lower for k in self._MEASUREMENT_SECTIONS):
            default_type = "measurement"
        else:
            default_type = "fact"

        # 1. Extract from bullet points (-, *, •)
        for bullet in self._iter_bullets(body):
            for text in self._split_into_claims(bullet):
                if self._is_valid_claim(text):
                    claims.append(self._make_claim(doc, text, title, default_type))

        # 2. Extract from numbered lists (1., 2., etc.)
        for item in self._iter_numbered(body):
            for text in self._split_into_claims(item):
                if self._is_valid_claim(text):
                    claims.append(self._make_claim(doc, text, title, "process" if default_type == "process" else "fact"))

        # 3. Extract definition-style lines ("Term: definition")
        for line in body.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "-", "*", "•", "|", ">")):
                continue
            def_claim = self._try_definition(stripped)
            if def_claim and self._is_valid_claim(def_claim):
                claims.append(self._make_claim(doc, def_claim, title, "definition"))

        # 4. For definition sections, also grab the first paragraph
        if default_type == "definition":
            para = self._first_paragraph(body)
            if para and self._is_valid_claim(para):
                claims.append(self._make_claim(doc, para, title, "definition"))

        return claims

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_bullets(body: str) -> Iterator[str]:
        """Yield text from bullet-point lines."""
        for line in body.split("\n"):
            m = re.match(r"^\s*[-*•]\s+(.+)$", line)
            if m:
                yield m.group(1).strip()

    @staticmethod
    def _iter_numbered(body: str) -> Iterator[str]:
        """Yield text from numbered-list lines."""
        for line in body.split("\n"):
            m = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
            if m:
                yield m.group(1).strip()

    @staticmethod
    def _first_paragraph(body: str) -> str:
        """Return the first non-empty, non-header, non-list line."""
        for line in body.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("#", "-", "*", "•", "|", ">")):
                continue
            if re.match(r"^\d+[.)]\s", stripped):
                continue
            return stripped
        return ""

    @staticmethod
    def _try_definition(line: str) -> str | None:
        """If a line looks like 'Term: definition', return a claim string."""
        # Match "Term: definition" but not URLs or code
        if ":" not in line:
            return None
        # Avoid lines that are clearly not definitions
        if line.startswith("http") or line.startswith("```"):
            return None
        parts = line.split(":", 1)
        if len(parts) != 2:
            return None
        term = parts[0].strip()
        definition = parts[1].strip()
        # Term should be short (1-6 words) and definition should be meaningful
        if not term or not definition:
            return None
        term_words = term.split()
        if len(term_words) > 6:
            return None
        if len(definition) < 15:
            return None
        # Avoid if term contains sentence-ending punctuation
        if any(p in term for p in ".;!?"):
            return None
        return f"{term}: {definition}"

    def _split_into_claims(self, text: str) -> list[str]:
        """Split a bullet or list item into individual claim sentences."""
        # Remove markdown emphasis markers for cleaner claims
        clean = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        clean = re.sub(r"`([^`]+)`", r"\1", clean)

        # If the text is short enough, keep it as one claim
        if len(clean) <= self.MAX_CLAIM_LEN:
            return [clean] if clean else []

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", clean)
        claims: list[str] = []
        for s in sentences:
            s = s.strip()
            if len(s) >= self.MIN_CLAIM_LEN:
                claims.append(s)
        return claims

    def _is_valid_claim(self, text: str) -> bool:
        """Check whether a text fragment is a valid atomic claim."""
        text = text.strip()
        if len(text) < self.MIN_CLAIM_LEN:
            return False
        if len(text) > self.MAX_CLAIM_LEN * 2:
            return False
        if self._SKIP_PATTERNS.match(text):
            return False
        # Must contain at least one alphabetic character
        if not re.search(r"[a-zA-Z]", text):
            return False
        # Skip pure code blocks
        if text.startswith("```") or text.startswith("|"):
            return False
        # Skip if it's just a number or measurement without context
        if re.match(r"^\d+(\.\d+)?\s*(kg|mm|cm|m|ft|in|lb|g|mg|%|°|hz|w|v|a)$", text, re.IGNORECASE):
            return False
        return True

    def _make_claim(
        self, doc: KnowledgeDocument, text: str, section: str, claim_type: str,
    ) -> ExtractedClaim:
        """Create an ExtractedClaim with a stable ID."""
        claim_hash = hashlib.sha256(
            f"{doc.doc_id}:{text}".encode("utf-8")
        ).hexdigest()[:12]
        claim_id = f"claim_{claim_hash}"
        return ExtractedClaim(
            claim_id=claim_id,
            text=text,
            doc_id=doc.doc_id,
            section=section,
            claim_type=claim_type,
            confidence=self._confidence_for(claim_type),
        )

    @staticmethod
    def _confidence_for(claim_type: str) -> float:
        """Assign a default confidence based on claim type."""
        if claim_type == "definition":
            return 0.95
        if claim_type == "measurement":
            return 0.90
        if claim_type == "process":
            return 0.85
        return 0.80
