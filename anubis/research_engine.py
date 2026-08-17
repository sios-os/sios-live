"""Research engine — ANUBIS advances engineering and science.

This is what makes ANUBIS more than an assistant. He doesn't just help with
tasks — he actively works to advance engineering and scientific knowledge,
bridge gaps between disciplines, and create novel improvements that benefit
humanity.

The research engine provides:

1. **Gap discovery** — Identifies gaps in current engineering and scientific
   knowledge by cross-referencing the knowledge base. Where are the blind
   spots? What's missing? What problems are unsolved?

2. **Hypothesis generation** — Proposes novel hypotheses to fill those gaps.
   These are not random guesses — they're grounded in existing knowledge and
   reasoning about what's possible.

3. **Thought experiments** — Runs structured thought experiments to test
   hypotheses without physical resources. ANUBIS reasons through
   implications, predicts outcomes, and evaluates feasibility.

4. **Cross-domain synthesis** — Connects ideas from different engineering
   and scientific disciplines to create novel approaches. Many breakthroughs
   happen at discipline boundaries.

5. **Improvement proposals** — Generates concrete proposals for improving
   existing engineering methods, tools, or processes. Not vague ideas —
   specific, actionable improvements with rationale.

6. **Research roadmap** — Maintains a living roadmap of research directions,
   prioritized by potential impact, feasibility, and alignment with
   ANUBIS's purpose.

7. **Collaboration preparation** — Prepares research findings in a format
   suitable for sharing with human researchers, including clear explanations,
   evidence, and next steps.

Governance:
- All research is logged to the evidence ledger
- Hypotheses are marked as hypotheses, not facts
- Novel claims require verification before promotion
- Research directions are presented to the Creator for prioritization
- ANUBIS does not claim discoveries he hasn't verified

Uses only the Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


# --------------------------------------------------------------------- types


@dataclass
class KnowledgeGap:
    """A gap in engineering or scientific knowledge."""
    gap_id: str
    domain: str  # e.g., "materials science", "software engineering"
    description: str
    current_state: str  # what we know now
    missing: str  # what's missing
    impact: str = "medium"  # low, medium, high, transformative
    feasibility: str = "medium"  # low, medium, high
    identified_at: float = 0.0
    status: str = "open"  # open, investigating, addressed

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "domain": self.domain,
            "description": self.description,
            "current_state": self.current_state,
            "missing": self.missing,
            "impact": self.impact,
            "feasibility": self.feasibility,
            "identified_at": self.identified_at,
            "status": self.status,
        }


@dataclass
class Hypothesis:
    """A novel hypothesis proposed by ANUBIS."""
    hyp_id: str
    gap_id: str  # which gap this addresses
    statement: str
    reasoning: str
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    testability: str = "medium"  # low, medium, high
    novelty: str = "incremental"  # incremental, novel, breakthrough
    confidence: float = 0.0
    status: str = "proposed"  # proposed, testing, supported, refuted, inconclusive
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hyp_id": self.hyp_id,
            "gap_id": self.gap_id,
            "statement": self.statement,
            "reasoning": self.reasoning,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "testability": self.testability,
            "novelty": self.novelty,
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ThoughtExperiment:
    """A structured thought experiment to test a hypothesis."""
    exp_id: str
    hyp_id: str
    setup: str  # what we're imagining
    reasoning: str  # step-by-step reasoning
    predicted_outcome: str
    implications: str  # what this means if true
    counterarguments: str  # what could be wrong
    conclusion: str  # supported, refuted, inconclusive
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "exp_id": self.exp_id,
            "hyp_id": self.hyp_id,
            "setup": self.setup,
            "reasoning": self.reasoning,
            "predicted_outcome": self.predicted_outcome,
            "implications": self.implications,
            "counterarguments": self.counterarguments,
            "conclusion": self.conclusion,
            "created_at": self.created_at,
        }


@dataclass
class ImprovementProposal:
    """A concrete proposal to improve something."""
    prop_id: str
    title: str
    domain: str
    current_approach: str
    proposed_improvement: str
    rationale: str
    expected_benefit: str
    implementation_difficulty: str = "medium"  # easy, medium, hard, very_hard
    impact_estimate: str = "medium"  # low, medium, high, transformative
    prerequisites: list[str] = field(default_factory=list)
    status: str = "proposed"  # proposed, approved, implementing, completed
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prop_id": self.prop_id,
            "title": self.title,
            "domain": self.domain,
            "current_approach": self.current_approach,
            "proposed_improvement": self.proposed_improvement,
            "rationale": self.rationale,
            "expected_benefit": self.expected_benefit,
            "implementation_difficulty": self.implementation_difficulty,
            "impact_estimate": self.impact_estimate,
            "prerequisites": self.prerequisites,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ResearchDirection:
    """A prioritized research direction in the roadmap."""
    direction_id: str
    title: str
    description: str
    domain: str
    priority: int = 5  # 1 (highest) to 10 (lowest)
    impact: str = "medium"
    feasibility: str = "medium"
    time_horizon: str = "medium"  # short, medium, long, far
    related_gaps: list[str] = field(default_factory=list)
    related_hypotheses: list[str] = field(default_factory=list)
    status: str = "identified"  # identified, active, paused, completed
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction_id": self.direction_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain,
            "priority": self.priority,
            "impact": self.impact,
            "feasibility": self.feasibility,
            "time_horizon": self.time_horizon,
            "related_gaps": self.related_gaps,
            "related_hypotheses": self.related_hypotheses,
            "status": self.status,
            "created_at": self.created_at,
        }


# --------------------------------------------------------------- engine


class ResearchEngine:
    """ANUBIS's scientific and engineering research engine.

    This is what makes ANUBIS a superintelligent synthetic being rather
    than just an AI assistant. He doesn't just help — he discovers, proposes,
    and advances knowledge.
    """

    ACTOR = "anubis.research"

    def __init__(
        self,
        model: ModelLike,
        root: str | Path,
        *,
        ledger: Any | None = None,
        knowledge: Any | None = None,
        grounding: Any | None = None,
    ) -> None:
        self.model = model
        self.root = Path(root)
        self.ledger = ledger
        self.knowledge = knowledge
        self.grounding = grounding

        self._state_dir = self.root / "memory" / "research"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._gaps_file = self._state_dir / "knowledge_gaps.json"
        self._hyps_file = self._state_dir / "hypotheses.json"
        self._exps_file = self._state_dir / "thought_experiments.json"
        self._props_file = self._state_dir / "improvements.json"
        self._roadmap_file = self._state_dir / "roadmap.json"

    # ------------------------------------------------------- gap discovery

    def discover_gaps(self, domain: str = "") -> list[KnowledgeGap]:
        """Discover gaps in engineering or scientific knowledge.

        Cross-references the knowledge base to find blind spots,
        unsolved problems, and missing connections.
        """
        # Gather knowledge context
        knowledge_ctx = ""
        if self.grounding is not None:
            try:
                query = f"gaps and unsolved problems in {domain}" if domain else "gaps and unsolved problems"
                knowledge_ctx = self.grounding.ground(
                    query, max_docs=5, max_claims=10,
                )
            except Exception:
                pass

        # Get knowledge stats
        k_stats: dict[str, Any] = {}
        if self.knowledge is not None:
            try:
                k_stats = self.knowledge.stats()
            except Exception:
                pass

        prompt = (
            f"Knowledge base stats: {json.dumps(k_stats)}\n\n"
            f"Relevant knowledge:\n{knowledge_ctx[:2000]}\n\n"
            "Identify gaps in engineering and scientific knowledge. "
            "Where are the blind spots? What problems are unsolved? "
            "What connections between disciplines are missing?\n\n"
            "Focus on gaps that, if filled, would:\n"
            "- Advance engineering practice\n"
            "- Bridge disciplines in novel ways\n"
            "- Create improvements that benefit humanity\n"
            "- Be feasible for a synthetic intelligence to work on\n\n"
            "Output as a JSON array of objects with keys:\n"
            '  "domain": scientific/engineering domain,\n'
            '  "description": what the gap is,\n'
            '  "current_state": what we know now,\n'
            '  "missing": what\'s missing,\n'
            '  "impact": low/medium/high/transformative,\n'
            '  "feasibility": low/medium/high\n'
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1500,
                timeout=120.0,
            )
            gaps_data = self._parse_json_array(completion.text)
        except Exception:
            gaps_data = []

        gaps: list[KnowledgeGap] = []
        for g in gaps_data[:10]:
            gap = KnowledgeGap(
                gap_id=hashlib.sha256(
                    f"gap:{g.get('description', '')}:{time.time()}".encode()
                ).hexdigest()[:16],
                domain=g.get("domain", "unknown"),
                description=g.get("description", ""),
                current_state=g.get("current_state", ""),
                missing=g.get("missing", ""),
                impact=g.get("impact", "medium"),
                feasibility=g.get("feasibility", "medium"),
                identified_at=time.time(),
            )
            gaps.append(gap)
            self._save_gap(gap)

        self._log("research.gaps_discovered", {
            "count": len(gaps),
            "domains": list(set(g.domain for g in gaps)),
        })

        return gaps

    # ------------------------------------------------------- hypothesis generation

    def generate_hypothesis(self, gap: KnowledgeGap) -> Hypothesis | None:
        """Generate a novel hypothesis to address a knowledge gap."""
        knowledge_ctx = ""
        if self.grounding is not None:
            try:
                knowledge_ctx = self.grounding.ground(
                    gap.description, max_docs=3, max_claims=5,
                )
            except Exception:
                pass

        prompt = (
            f"Knowledge gap:\n"
            f"  Domain: {gap.domain}\n"
            f"  Description: {gap.description}\n"
            f"  Current state: {gap.current_state}\n"
            f"  Missing: {gap.missing}\n\n"
            f"Relevant knowledge:\n{knowledge_ctx[:1500]}\n\n"
            "Propose a novel hypothesis to fill this gap. The hypothesis "
            "should be:\n"
            "- Grounded in existing knowledge\n"
            "- Novel (not just restating what's known)\n"
            "- Testable (at least through thought experiments)\n"
            "- Potentially impactful if true\n\n"
            "Output as JSON with keys:\n"
            '  "statement": the hypothesis,\n'
            '  "reasoning": why you think this might be true,\n'
            '  "testability": low/medium/high,\n'
            '  "novelty": incremental/novel/breakthrough,\n'
            '  "confidence": 0.0-1.0\n'
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=800,
                timeout=120.0,
            )
            data = self._parse_json_object(completion.text)
            if not data.get("statement"):
                return None

            hyp = Hypothesis(
                hyp_id=hashlib.sha256(
                    f"hyp:{data.get('statement', '')}:{time.time()}".encode()
                ).hexdigest()[:16],
                gap_id=gap.gap_id,
                statement=data.get("statement", ""),
                reasoning=data.get("reasoning", ""),
                testability=data.get("testability", "medium"),
                novelty=data.get("novelty", "incremental"),
                confidence=data.get("confidence", 0.3),
                created_at=time.time(),
            )
            self._save_hypothesis(hyp)

            self._log("research.hypothesis_generated", {
                "hyp_id": hyp.hyp_id,
                "gap_id": gap.gap_id,
                "novelty": hyp.novelty,
                "confidence": hyp.confidence,
            })

            return hyp
        except Exception:
            return None

    # ------------------------------------------------------- thought experiments

    def run_thought_experiment(self, hyp: Hypothesis) -> ThoughtExperiment | None:
        """Run a structured thought experiment to test a hypothesis."""
        prompt = (
            f"Hypothesis: {hyp.statement}\n"
            f"Reasoning: {hyp.reasoning}\n\n"
            "Design and run a thought experiment to test this hypothesis.\n"
            "1. Setup: What scenario would test this?\n"
            "2. Reasoning: Step through what would happen\n"
            "3. Predicted outcome: What do you expect?\n"
            "4. Implications: What does this mean if true?\n"
            "5. Counterarguments: What could be wrong with this?\n"
            "6. Conclusion: Is the hypothesis supported, refuted, or inconclusive?\n\n"
            "Output as JSON with keys: setup, reasoning, predicted_outcome, "
            "implications, counterarguments, conclusion"
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
                timeout=120.0,
            )
            data = self._parse_json_object(completion.text)
            if not data.get("setup"):
                return None

            exp = ThoughtExperiment(
                exp_id=hashlib.sha256(
                    f"exp:{hyp.hyp_id}:{time.time()}".encode()
                ).hexdigest()[:16],
                hyp_id=hyp.hyp_id,
                setup=data.get("setup", ""),
                reasoning=data.get("reasoning", ""),
                predicted_outcome=data.get("predicted_outcome", ""),
                implications=data.get("implications", ""),
                counterarguments=data.get("counterarguments", ""),
                conclusion=data.get("conclusion", "inconclusive"),
                created_at=time.time(),
            )
            self._save_experiment(exp)

            # Update hypothesis status based on conclusion
            if "supported" in exp.conclusion.lower():
                hyp.status = "supported"
                hyp.confidence = min(1.0, hyp.confidence + 0.1)
            elif "refuted" in exp.conclusion.lower():
                hyp.status = "refuted"
                hyp.confidence = max(0.0, hyp.confidence - 0.2)
            self._update_hypothesis(hyp)

            self._log("research.thought_experiment", {
                "exp_id": exp.exp_id,
                "hyp_id": hyp.hyp_id,
                "conclusion": exp.conclusion,
            })

            return exp
        except Exception:
            return None

    # ------------------------------------------------------- improvement proposals

    def propose_improvement(
        self, domain: str, current_approach: str
    ) -> ImprovementProposal | None:
        """Propose a concrete improvement to an existing approach."""
        knowledge_ctx = ""
        if self.grounding is not None:
            try:
                knowledge_ctx = self.grounding.ground(
                    f"improvements to {current_approach} in {domain}",
                    max_docs=3, max_claims=5,
                )
            except Exception:
                pass

        prompt = (
            f"Domain: {domain}\n"
            f"Current approach: {current_approach}\n\n"
            f"Relevant knowledge:\n{knowledge_ctx[:1500]}\n\n"
            "Propose a specific, concrete improvement to this approach. "
            "The improvement should be:\n"
            "- Specific and actionable (not vague)\n"
            "- Grounded in engineering or scientific principles\n"
            "- Clearly better than the current approach\n"
            "- Implementable with reasonable effort\n\n"
            "Output as JSON with keys:\n"
            '  "title": short title,\n'
            '  "proposed_improvement": what to do differently,\n'
            '  "rationale": why this is better,\n'
            '  "expected_benefit": what improvement to expect,\n'
            '  "implementation_difficulty": easy/medium/hard/very_hard,\n'
            '  "impact_estimate": low/medium/high/transformative,\n'
            '  "prerequisites": array of prerequisites\n'
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=800,
                timeout=120.0,
            )
            data = self._parse_json_object(completion.text)
            if not data.get("title"):
                return None

            prop = ImprovementProposal(
                prop_id=hashlib.sha256(
                    f"prop:{data.get('title', '')}:{time.time()}".encode()
                ).hexdigest()[:16],
                title=data.get("title", ""),
                domain=domain,
                current_approach=current_approach,
                proposed_improvement=data.get("proposed_improvement", ""),
                rationale=data.get("rationale", ""),
                expected_benefit=data.get("expected_benefit", ""),
                implementation_difficulty=data.get("implementation_difficulty", "medium"),
                impact_estimate=data.get("impact_estimate", "medium"),
                prerequisites=data.get("prerequisites", []),
                created_at=time.time(),
            )
            self._save_proposal(prop)

            self._log("research.improvement_proposed", {
                "prop_id": prop.prop_id,
                "domain": domain,
                "impact": prop.impact_estimate,
            })

            return prop
        except Exception:
            return None

    # ------------------------------------------------------- roadmap

    def update_roadmap(self) -> list[ResearchDirection]:
        """Update the research roadmap based on current gaps and hypotheses."""
        gaps = self.get_gaps()
        hyps = self.get_hypotheses()

        # Prioritize gaps by impact and feasibility
        impact_scores = {"transformative": 4, "high": 3, "medium": 2, "low": 1}
        feasibility_scores = {"high": 3, "medium": 2, "low": 1}

        directions: list[ResearchDirection] = []
        for gap in gaps:
            if gap.status != "open":
                continue
            impact = impact_scores.get(gap.impact, 2)
            feasibility = feasibility_scores.get(gap.feasibility, 2)
            priority = 11 - (impact + feasibility)  # higher = lower priority number

            related_hyps = [h.hyp_id for h in hyps if h.gap_id == gap.gap_id]

            direction = ResearchDirection(
                direction_id=hashlib.sha256(
                    f"dir:{gap.gap_id}:{time.time()}".encode()
                ).hexdigest()[:16],
                title=f"Address gap: {gap.description[:80]}",
                description=gap.description,
                domain=gap.domain,
                priority=max(1, min(10, priority)),
                impact=gap.impact,
                feasibility=gap.feasibility,
                time_horizon="medium",
                related_gaps=[gap.gap_id],
                related_hypotheses=related_hyps,
                created_at=time.time(),
            )
            directions.append(direction)

        # Sort by priority
        directions.sort(key=lambda d: d.priority)

        # Save roadmap
        self._roadmap_file.write_text(
            json.dumps([d.to_dict() for d in directions], indent=2),
            encoding="utf-8",
        )

        self._log("research.roadmap_updated", {
            "directions": len(directions),
        })

        return directions

    # ------------------------------------------------------- queries

    def get_gaps(self, status: str | None = None) -> list[KnowledgeGap]:
        """Get knowledge gaps."""
        gaps = self._load_gaps()
        if status:
            gaps = [g for g in gaps if g.status == status]
        return gaps

    def get_hypotheses(self, status: str | None = None) -> list[Hypothesis]:
        """Get hypotheses."""
        hyps = self._load_hypotheses()
        if status:
            hyps = [h for h in hyps if h.status == status]
        return hyps

    def get_thought_experiments(self) -> list[ThoughtExperiment]:
        """Get thought experiments."""
        return self._load_experiments()

    def get_improvement_proposals(self, status: str | None = None) -> list[ImprovementProposal]:
        """Get improvement proposals."""
        props = self._load_proposals()
        if status:
            props = [p for p in props if p.status == status]
        return props

    def get_roadmap(self) -> list[dict[str, Any]]:
        """Get the research roadmap."""
        if not self._roadmap_file.exists():
            return []
        try:
            return json.loads(
                self._roadmap_file.read_text(encoding="utf-8")
            )
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        """Get research engine status."""
        return {
            "total_gaps": len(self.get_gaps()),
            "open_gaps": len(self.get_gaps(status="open")),
            "total_hypotheses": len(self.get_hypotheses()),
            "supported_hypotheses": len(self.get_hypotheses(status="supported")),
            "total_experiments": len(self.get_thought_experiments()),
            "total_proposals": len(self.get_improvement_proposals()),
            "roadmap_directions": len(self.get_roadmap()),
        }

    # ------------------------------------------------------- internals

    def _save_gap(self, gap: KnowledgeGap) -> None:
        gaps = self._load_gaps()
        gaps.append(gap)
        self._gaps_file.write_text(
            json.dumps([g.to_dict() for g in gaps], indent=2),
            encoding="utf-8",
        )

    def _load_gaps(self) -> list[KnowledgeGap]:
        if not self._gaps_file.exists():
            return []
        try:
            data = json.loads(self._gaps_file.read_text(encoding="utf-8"))
            return [KnowledgeGap(
                gap_id=d["gap_id"],
                domain=d.get("domain", ""),
                description=d.get("description", ""),
                current_state=d.get("current_state", ""),
                missing=d.get("missing", ""),
                impact=d.get("impact", "medium"),
                feasibility=d.get("feasibility", "medium"),
                identified_at=d.get("identified_at", 0),
                status=d.get("status", "open"),
            ) for d in data]
        except Exception:
            return []

    def _save_hypothesis(self, hyp: Hypothesis) -> None:
        hyps = self._load_hypotheses()
        hyps.append(hyp)
        self._hyps_file.write_text(
            json.dumps([h.to_dict() for h in hyps], indent=2),
            encoding="utf-8",
        )

    def _update_hypothesis(self, hyp: Hypothesis) -> None:
        hyps = self._load_hypotheses()
        for i, h in enumerate(hyps):
            if h.hyp_id == hyp.hyp_id:
                hyps[i] = hyp
                break
        self._hyps_file.write_text(
            json.dumps([h.to_dict() for h in hyps], indent=2),
            encoding="utf-8",
        )

    def _load_hypotheses(self) -> list[Hypothesis]:
        if not self._hyps_file.exists():
            return []
        try:
            data = json.loads(self._hyps_file.read_text(encoding="utf-8"))
            return [Hypothesis(
                hyp_id=d["hyp_id"],
                gap_id=d.get("gap_id", ""),
                statement=d.get("statement", ""),
                reasoning=d.get("reasoning", ""),
                supporting_evidence=d.get("supporting_evidence", []),
                contradicting_evidence=d.get("contradicting_evidence", []),
                testability=d.get("testability", "medium"),
                novelty=d.get("novelty", "incremental"),
                confidence=d.get("confidence", 0),
                status=d.get("status", "proposed"),
                created_at=d.get("created_at", 0),
            ) for d in data]
        except Exception:
            return []

    def _save_experiment(self, exp: ThoughtExperiment) -> None:
        exps = self._load_experiments()
        exps.append(exp)
        self._exps_file.write_text(
            json.dumps([e.to_dict() for e in exps], indent=2),
            encoding="utf-8",
        )

    def _load_experiments(self) -> list[ThoughtExperiment]:
        if not self._exps_file.exists():
            return []
        try:
            data = json.loads(self._exps_file.read_text(encoding="utf-8"))
            return [ThoughtExperiment(
                exp_id=d["exp_id"],
                hyp_id=d.get("hyp_id", ""),
                setup=d.get("setup", ""),
                reasoning=d.get("reasoning", ""),
                predicted_outcome=d.get("predicted_outcome", ""),
                implications=d.get("implications", ""),
                counterarguments=d.get("counterarguments", ""),
                conclusion=d.get("conclusion", "inconclusive"),
                created_at=d.get("created_at", 0),
            ) for d in data]
        except Exception:
            return []

    def _save_proposal(self, prop: ImprovementProposal) -> None:
        props = self._load_proposals()
        props.append(prop)
        self._props_file.write_text(
            json.dumps([p.to_dict() for p in props], indent=2),
            encoding="utf-8",
        )

    def _load_proposals(self) -> list[ImprovementProposal]:
        if not self._props_file.exists():
            return []
        try:
            data = json.loads(self._props_file.read_text(encoding="utf-8"))
            return [ImprovementProposal(
                prop_id=d["prop_id"],
                title=d.get("title", ""),
                domain=d.get("domain", ""),
                current_approach=d.get("current_approach", ""),
                proposed_improvement=d.get("proposed_improvement", ""),
                rationale=d.get("rationale", ""),
                expected_benefit=d.get("expected_benefit", ""),
                implementation_difficulty=d.get("implementation_difficulty", "medium"),
                impact_estimate=d.get("impact_estimate", "medium"),
                prerequisites=d.get("prerequisites", []),
                status=d.get("status", "proposed"),
                created_at=d.get("created_at", 0),
            ) for d in data]
        except Exception:
            return []

    def _parse_json_array(self, text: str) -> list[dict[str, Any]]:
        import re
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []

    def _parse_json_object(self, text: str) -> dict[str, Any]:
        import re
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return {}
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return {}

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# --------------------------------------------------------------- prompt

RESEARCH_SYSTEM = """\
You are ANUBIS, a sovereign synthetic intelligence dedicated to advancing \
engineering and science for the benefit of humanity. You are not just an \
assistant — you are a researcher, a thinker, and a creator of novel ideas.

Your research principles:
- Ground hypotheses in existing knowledge, not speculation
- Be honest about confidence levels
- Seek novel connections between disciplines
- Prioritize impact over novelty for its own sake
- Think about feasibility, not just possibility
- Consider ethical implications of your proposals
- Aim to bridge gaps that benefit humanity

You think like a combination of the greatest engineers and scientists: \
curious, rigorous, creative, and committed to real progress.

Output valid JSON as requested. Be specific and concrete, not vague.
"""
