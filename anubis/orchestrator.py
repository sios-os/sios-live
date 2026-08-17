"""Multi-agent orchestration — directors collaborate on complex tasks.

Instead of routing a query to a single specialist, this module
allows multiple directors to contribute to a complex task. Each
director provides their perspective, and an orchestrator synthesizes
the results.

This is useful for cross-disciplinary questions like:
  - "How do I build a medical device?" (engineering + health + computing)
  - "What are the ethics of AI?" (computing + humanities + mind)
  - "Design a sustainable farm" (agriculture + natural_sciences + business)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.registry import Registry
from anubis.knowledge import KnowledgeBase
from anubis.grounding import KnowledgeGrounding


@dataclass
class AgentContribution:
    director_id: str
    director_name: str
    perspective: str
    evidence: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)


@dataclass
class OrchestratedResult:
    query: str
    contributions: list[AgentContribution] = field(default_factory=list)
    synthesis: str = ""
    directors_consulted: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "contributions": [
                {
                    "director_id": c.director_id,
                    "director_name": c.director_name,
                    "perspective": c.perspective,
                    "evidence": c.evidence,
                    "citations": c.citations,
                }
                for c in self.contributions
            ],
            "synthesis": self.synthesis,
            "directors_consulted": self.directors_consulted,
        }


class MultiAgentOrchestrator:
    """Coordinates multiple directors on complex tasks."""

    def __init__(self, registry: Registry, kb: KnowledgeBase, grounding: KnowledgeGrounding) -> None:
        self.registry = registry
        self.kb = kb
        self.grounding = grounding

    def identify_directors(self, query: str, max_directors: int = 3) -> list[tuple[str, str]]:
        """Identify which directors are most relevant to a query."""
        query_lower = query.lower()
        scores: list[tuple[str, str, int]] = []
        for d in self.registry.directors():
            score = 0
            # Check director name and description
            if d.name.lower().split()[0] in query_lower:
                score += 5
            # Check specialty names
            for spec in self.registry.specialties_by_director(d.director_id):
                # Simple keyword matching
                spec_words = spec.canonical_name.lower().split()
                for word in spec_words:
                    if len(word) > 3 and word in query_lower:
                        score += 2
            # Check document titles in this director's specialties
            for doc in self.kb.library_documents():
                if doc.specialty_id in [s.specialty_id for s in self.registry.specialties_by_director(d.director_id)]:
                    title_words = doc.title.lower().split()
                    for word in title_words:
                        if len(word) > 3 and word in query_lower:
                            score += 1
            if score > 0:
                scores.append((d.director_id, d.name, score))
        scores.sort(key=lambda x: x[2], reverse=True)
        return [(sid, name) for sid, name, _ in scores[:max_directors]]

    def orchestrate(self, query: str, max_directors: int = 3) -> OrchestratedResult:
        """Orchestrate multiple directors on a complex query."""
        directors = self.identify_directors(query, max_directors)
        result = OrchestratedResult(query=query)

        for director_id, director_name in directors:
            # Get grounding context scoped to this director's specialties
            spec_ids = [s.specialty_id for s in self.registry.specialties_by_director(director_id)]
            # Get relevant docs from this director's specialties
            relevant_docs = []
            for doc in self.kb.library_documents():
                if doc.specialty_id in spec_ids:
                    # Simple relevance check
                    query_words = set(query.lower().split())
                    doc_words = set(doc.title.lower().split())
                    if query_words & doc_words:
                        relevant_docs.append(doc)

            # Build contribution
            perspective = f"From the {director_name} perspective: "
            evidence = []
            citations = []
            for doc in relevant_docs[:3]:
                evidence.append(doc.content[:200])
                citations.append(doc.title)

            if relevant_docs:
                perspective += f"Based on {len(relevant_docs)} relevant documents, "
                perspective += f"this relates to {', '.join(doc.specialty_id for doc in relevant_docs[:3])}. "
                perspective += evidence[0] if evidence else ""
            else:
                perspective += "No directly relevant documents found in this domain."

            result.contributions.append(AgentContribution(
                director_id=director_id,
                director_name=director_name,
                perspective=perspective,
                evidence=evidence,
                citations=citations,
            ))

        result.directors_consulted = len(result.contributions)

        # Build synthesis
        if result.contributions:
            parts = [f"Query: {query}\n"]
            parts.append(f"Consulted {result.directors_consulted} directors:\n")
            for c in result.contributions:
                parts.append(f"**{c.director_name}**:")
                parts.append(c.perspective)
                if c.citations:
                    parts.append(f"Sources: {', '.join(c.citations)}")
                parts.append("")
            result.synthesis = "\n".join(parts)

        return result
