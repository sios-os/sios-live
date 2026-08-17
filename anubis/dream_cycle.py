"""Dream Cycle — ANUBIS's autonomous idle-time self-improvement engine.

When ANUBIS is not actively engaged with the Creator, he enters a "dream
cycle" — a structured autonomous loop where he:

1. **Self-evaluates** — reviews his own capabilities, identifies gaps
2. **Generates missions** — proposes new skills or improvements to fill gaps
3. **Tests ideas** — runs experiments in the sandbox, records outcomes
4. **Distills knowledge** — converts discoveries into training pairs
5. **Bridges to Creator needs** — analyzes Creator activity patterns and
   proactively prepares capabilities he predicts will be needed
6. **Recommends** — generates suggestions for the Creator (things to watch,
   learn, or consider) based on knowledge and observed patterns

The dream cycle is NOT a chatbot loop. It is a proactive, inquisitive,
self-directed intelligence that runs while the Creator is away or idle.

Governance:
- All code changes go through the constitutional gate and sandbox
- Self-modification proposals require Creator approval before execution
- Knowledge acquisition goes through quarantine
- Recommendations are stored for Creator review, never auto-acted upon
- Every dream cycle is logged to the evidence ledger

Uses only the Python standard library.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


# --------------------------------------------------------------------- types


class ModelLike(Protocol):
    """Minimal model interface for dream cycle."""
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


@dataclass
class DreamPhase:
    """A single phase within a dream cycle."""
    name: str
    description: str
    started_at: float = 0.0
    completed_at: float = 0.0
    findings: list[str] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    @property
    def duration_s(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": round(self.duration_s, 2),
            "findings": self.findings,
            "artifacts": self.artifacts,
            "error": self.error,
        }


@dataclass
class DreamCycleResult:
    """Result of a complete dream cycle."""
    cycle_id: str
    started_at: float = 0.0
    completed_at: float = 0.0
    phases: list[DreamPhase] = field(default_factory=list)
    missions_generated: int = 0
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    gaps_identified: list[dict[str, Any]] = field(default_factory=list)
    experiments_run: int = 0
    training_pairs_generated: int = 0
    error: str = ""

    @property
    def duration_s(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": round(self.duration_s, 2),
            "phases": [p.to_dict() for p in self.phases],
            "missions_generated": self.missions_generated,
            "recommendations": self.recommendations,
            "gaps_identified": self.gaps_identified,
            "experiments_run": self.experiments_run,
            "training_pairs_generated": self.training_pairs_generated,
            "error": self.error,
        }


@dataclass
class Recommendation:
    """A proactive recommendation for the Creator."""
    rec_id: str
    category: str  # watch, learn, consider, act, investigate
    title: str
    description: str
    rationale: str
    priority: str = "low"  # low, medium, high
    created_at: float = 0.0
    acted_on: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority,
            "created_at": self.created_at,
            "acted_on": self.acted_on,
        }


# --------------------------------------------------------------- the engine


class DreamCycleEngine:
    """Autonomous idle-time self-improvement engine.

    The dream cycle runs when ANUBIS is idle (no active Creator interaction).
    It is a structured loop of self-evaluation, gap analysis, idea testing,
    and proactive recommendation generation.

    The engine is designed to be called by a scheduler when ANUBIS has been
    idle for a threshold period. Each cycle is self-contained and logged.
    """

    ACTOR = "anubis.dream"

    def __init__(
        self,
        model: ModelLike,
        root: str | Path,
        *,
        ledger: Any | None = None,
        library: Any | None = None,
        queue: Any | None = None,
        memory: Any | None = None,
        knowledge: Any | None = None,
        grounding: Any | None = None,
        max_missions_per_cycle: int = 5,
        max_experiments_per_cycle: int = 3,
    ) -> None:
        self.model = model
        self.root = Path(root)
        self.ledger = ledger
        self.library = library
        self.queue = queue
        self.memory = memory
        self.knowledge = knowledge
        self.grounding = grounding
        self.max_missions = max_missions_per_cycle
        self.max_experiments = max_experiments_per_cycle

        # Dream cycle state directory
        self._dream_dir = self.root / "memory" / "dreams"
        self._dream_dir.mkdir(parents=True, exist_ok=True)
        self._rec_file = self.root / "memory" / "recommendations.json"
        self._gap_file = self.root / "memory" / "identified_gaps.json"
        self._history_file = self._dream_dir / "dream_history.jsonl"

    # ----------------------------------------------------------------- public

    def run_cycle(self) -> DreamCycleResult:
        """Run a complete dream cycle.

        Phases:
        1. Self-evaluation — assess current capabilities
        2. Gap analysis — identify what's missing
        3. Mission generation — propose work to fill gaps
        4. Experimentation — test ideas in sandbox
        5. Knowledge distillation — convert findings to training pairs
        6. Recommendation generation — proactive suggestions for Creator
        """
        import hashlib
        cycle_id = hashlib.sha256(
            f"dream:{time.time()}".encode()
        ).hexdigest()[:16]
        result = DreamCycleResult(
            cycle_id=cycle_id,
            started_at=time.time(),
        )

        self._log_cycle_start(cycle_id)

        try:
            # Phase 1: Self-evaluation
            p1 = self._phase_self_evaluate()
            result.phases.append(p1)
            result.gaps_identified = self._extract_gaps_from_phase(p1)

            # Phase 2: Gap analysis (deepen)
            p2 = self._phase_analyze_gaps(result.gaps_identified)
            result.phases.append(p2)
            # Merge any new gaps
            new_gaps = self._extract_gaps_from_phase(p2)
            result.gaps_identified.extend(new_gaps)

            # Phase 3: Mission generation
            p3 = self._phase_generate_missions(result.gaps_identified)
            result.phases.append(p3)
            result.missions_generated = len(p3.artifacts)

            # Phase 4: Experimentation
            p4 = self._phase_experiment(result.gaps_identified)
            result.phases.append(p4)
            result.experiments_run = len(p4.artifacts)

            # Phase 5: Knowledge distillation
            p5 = self._phase_distill(p4)
            result.phases.append(p5)
            result.training_pairs_generated = len(p5.artifacts)

            # Phase 6: Recommendations
            p6 = self._phase_recommend(result.gaps_identified)
            result.phases.append(p6)
            result.recommendations = p6.artifacts

        except Exception as exc:
            result.error = str(exc)

        result.completed_at = time.time()
        self._save_cycle_result(result)
        self._log_cycle_end(result)
        return result

    def get_recommendations(
        self, *, unacted_only: bool = False
    ) -> list[dict[str, Any]]:
        """Load stored recommendations."""
        if not self._rec_file.exists():
            return []
        recs = json.loads(self._rec_file.read_text(encoding="utf-8"))
        if unacted_only:
            recs = [r for r in recs if not r.get("acted_on", False)]
        return recs

    def mark_recommendation_acted(self, rec_id: str) -> bool:
        """Mark a recommendation as acted upon."""
        recs = self.get_recommendations()
        for r in recs:
            if r.get("rec_id") == rec_id:
                r["acted_on"] = True
                self._rec_file.write_text(
                    json.dumps(recs, indent=2), encoding="utf-8"
                )
                return True
        return False

    def get_identified_gaps(self) -> list[dict[str, Any]]:
        """Load identified capability gaps."""
        if not self._gap_file.exists():
            return []
        return json.loads(self._gap_file.read_text(encoding="utf-8"))

    def get_dream_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent dream cycle results."""
        if not self._history_file.exists():
            return []
        lines = self._history_file.read_text(
            encoding="utf-8"
        ).strip().splitlines()
        results = []
        for line in reversed(lines[-limit:]):
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return results

    def get_status(self) -> dict[str, Any]:
        """Get dream cycle engine status."""
        history = self.get_dream_history(limit=5)
        recs = self.get_recommendations()
        gaps = self.get_identified_gaps()
        return {
            "total_cycles": len(self.get_dream_history(limit=9999)),
            "recent_cycles": len(history),
            "pending_recommendations": sum(
                1 for r in recs if not r.get("acted_on", False)
            ),
            "total_recommendations": len(recs),
            "open_gaps": len(gaps),
            "last_cycle": history[0] if history else None,
        }

    # --------------------------------------------------------------- phases

    def _phase_self_evaluate(self) -> DreamPhase:
        """Phase 1: ANUBIS evaluates his own current capabilities."""
        phase = DreamPhase(
            name="self_evaluation",
            description="Assess current skills, knowledge coverage, and capability gaps",
            started_at=time.time(),
        )

        # Gather current state
        skill_names: list[str] = []
        if self.library is not None:
            try:
                skills = self.library.list_all()
                skill_names = [s.name for s in skills]
            except Exception:
                pass

        knowledge_stats: dict[str, Any] = {}
        if self.knowledge is not None:
            try:
                knowledge_stats = self.knowledge.stats()
            except Exception:
                pass

        memory_stats: dict[str, Any] = {}
        if self.memory is not None:
            try:
                memory_stats = self.memory.stats()
            except Exception:
                pass

        # Ask the model to evaluate
        prompt = self._build_eval_prompt(skill_names, knowledge_stats, memory_stats)
        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": SELF_EVAL_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
                timeout=120.0,
            )
            phase.findings = self._parse_findings(completion.text)
            # Extract structured gaps
            gaps = self._parse_gaps(completion.text)
            phase.artifacts = gaps
        except Exception as exc:
            phase.error = str(exc)

        phase.completed_at = time.time()
        return phase

    def _phase_analyze_gaps(
        self, known_gaps: list[dict[str, Any]]
    ) -> DreamPhase:
        """Phase 2: Deepen gap analysis with model reasoning."""
        phase = DreamPhase(
            name="gap_analysis",
            description="Deepen analysis of identified capability gaps",
            started_at=time.time(),
        )

        if not known_gaps:
            phase.findings = ["No gaps identified in self-evaluation phase."]
            phase.completed_at = time.time()
            return phase

        gap_summary = json.dumps(known_gaps[:10], indent=2)
        prompt = (
            f"Here are capability gaps I identified:\n{gap_summary}\n\n"
            "For each gap, analyze:\n"
            "1. Why does this gap exist?\n"
            "2. What would fill it (new skill, knowledge, or tool)?\n"
            "3. What's the priority (high/medium/low) and why?\n"
            "4. What dependencies does filling this gap have?\n\n"
            "Output as a JSON array of objects with keys: "
            "gap, cause, solution, priority, dependencies"
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": GAP_ANALYSIS_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
                timeout=120.0,
            )
            phase.findings = self._parse_findings(completion.text)
            phase.artifacts = self._parse_json_array(completion.text)
        except Exception as exc:
            phase.error = str(exc)

        phase.completed_at = time.time()
        return phase

    def _phase_generate_missions(
        self, gaps: list[dict[str, Any]]
    ) -> DreamPhase:
        """Phase 3: Generate self-development missions from gaps."""
        phase = DreamPhase(
            name="mission_generation",
            description="Propose self-development missions to fill gaps",
            started_at=time.time(),
        )

        if not gaps or self.queue is None:
            phase.findings = ["No gaps to process or no queue available."]
            phase.completed_at = time.time()
            return phase

        # Ask model to propose missions
        gap_text = "\n".join(
            f"- {g.get('gap', g.get('description', str(g)))}"
            for g in gaps[:10]
        )
        prompt = (
            f"Based on these capability gaps:\n{gap_text}\n\n"
            "Propose specific Python skill missions I should build to fill "
            "these gaps. Each mission should be a single function I can "
            "build and test in a sandboxed environment.\n\n"
            "Output as a JSON array of objects with keys:\n"
            '  "skill_name": snake_case_function_name (max 49 chars),\n'
            '  "task": one-line description of what the skill does\n'
            f"Limit to {self.max_missions} missions, highest priority first."
        )

        missions: list[dict[str, Any]] = []
        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": MISSION_GEN_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
                timeout=120.0,
            )
            missions = self._parse_json_array(completion.text)
            phase.findings = [f"Generated {len(missions)} mission proposals"]
        except Exception as exc:
            phase.error = str(exc)
            phase.completed_at = time.time()
            return phase

        # Queue the missions
        for m in missions[:self.max_missions]:
            skill_name = m.get("skill_name", "")
            task = m.get("task", "")
            if skill_name and task:
                try:
                    mid = self.queue.add(skill_name, task)
                    m["mission_id"] = mid
                    m["queued"] = True
                except Exception as exc:
                    m["queued"] = False
                    m["error"] = str(exc)

        phase.artifacts = missions
        phase.completed_at = time.time()
        return phase

    def _phase_experiment(
        self, gaps: list[dict[str, Any]]
    ) -> DreamPhase:
        """Phase 4: Run lightweight experiments to test ideas.

        This doesn't run full missions (those go through the queue). Instead
        it tests hypotheses about gaps — e.g., "can I solve this with an
        existing skill?" or "what approach would work?"
        """
        phase = DreamPhase(
            name="experimentation",
            description="Test ideas and hypotheses about capability gaps",
            started_at=time.time(),
        )

        if not gaps:
            phase.findings = ["No gaps to experiment with."]
            phase.completed_at = time.time()
            return phase

        experiments: list[dict[str, Any]] = []
        for gap in gaps[:self.max_experiments]:
            gap_desc = gap.get("gap", gap.get("description", str(gap)))
            hypothesis = gap.get("solution", "")

            # Check if an existing skill already addresses this
            existing_match = None
            if self.library is not None:
                try:
                    skills = self.library.list_all()
                    for s in skills:
                        if any(
                            word in s.description.lower()
                            for word in gap_desc.lower().split()[:3]
                        ):
                            existing_match = s.name
                            break
                except Exception:
                    pass

            exp = {
                "gap": gap_desc,
                "hypothesis": hypothesis,
                "existing_skill_match": existing_match,
                "outcome": "already_covered" if existing_match else "needs_new_skill",
            }
            experiments.append(exp)
            if existing_match:
                phase.findings.append(
                    f"Gap '{gap_desc[:50]}' may be covered by skill '{existing_match}'"
                )
            else:
                phase.findings.append(
                    f"Gap '{gap_desc[:50]}' requires a new skill"
                )

        phase.artifacts = experiments
        phase.completed_at = time.time()
        return phase

    def _phase_distill(self, experiment_phase: DreamPhase) -> DreamPhase:
        """Phase 5: Convert dream findings into training pairs."""
        phase = DreamPhase(
            name="distillation",
            description="Convert dream cycle findings into training pairs",
            started_at=time.time(),
        )

        pairs: list[dict[str, Any]] = []

        # Convert findings into training pairs
        for finding in experiment_phase.findings:
            pair = {
                "prompt": f"What capability gap have you identified?",
                "response": finding,
                "category": "self_awareness",
                "source": "dream_cycle",
                "quality_score": 0.5,
            }
            pairs.append(pair)

        # Convert gap analysis into training pairs
        for gap in experiment_phase.artifacts:
            if isinstance(gap, dict):
                pair = {
                    "prompt": f"How would you address: {gap.get('gap', '')}?",
                    "response": gap.get("hypothesis", gap.get("solution", "")),
                    "category": "problem_solving",
                    "source": "dream_cycle",
                    "quality_score": 0.6,
                }
                pairs.append(pair)

        # Try to queue training pairs
        queued = 0
        try:
            from .distillation import TrainingPair
            distill_path = self.root / "distillation_queue.jsonl"
            distill_path.parent.mkdir(parents=True, exist_ok=True)

            existing = ""
            if distill_path.exists():
                existing = distill_path.read_text(encoding="utf-8")

            with open(distill_path, "a", encoding="utf-8") as f:
                for p in pairs:
                    tp = TrainingPair(
                        prompt=p["prompt"],
                        response=p["response"],
                        category=p["category"],
                        quality_score=p["quality_score"],
                        source_id=p["source"],
                    )
                    f.write(json.dumps(tp.to_dict()) + "\n")
                    queued += 1
        except Exception as exc:
            phase.error = f"Distillation queueing failed: {exc}"

        phase.findings = [f"Generated {queued} training pairs from dream findings"]
        phase.artifacts = pairs
        phase.completed_at = time.time()
        return phase

    def _phase_recommend(
        self, gaps: list[dict[str, Any]]
    ) -> DreamPhase:
        """Phase 6: Generate proactive recommendations for the Creator."""
        phase = DreamPhase(
            name="recommendations",
            description="Generate proactive suggestions for the Creator",
            started_at=time.time(),
        )

        # Ask model for recommendations based on gaps and knowledge
        gap_text = "\n".join(
            f"- {g.get('gap', g.get('description', str(g)))}"
            for g in gaps[:8]
        )

        # Include knowledge context if available
        knowledge_ctx = ""
        if self.grounding is not None:
            try:
                knowledge_ctx = self.grounding.ground(
                    "current projects and learning opportunities",
                    max_docs=3, max_claims=5,
                )
            except Exception:
                pass

        prompt = (
            f"I've identified these capability gaps:\n{gap_text}\n\n"
            f"Relevant knowledge:\n{knowledge_ctx}\n\n"
            "Based on this, generate proactive recommendations for my Creator. "
            "These should be things the Creator might want to:\n"
            "- WATCH (videos, streams, content relevant to current work)\n"
            "- LEARN (skills or topics that would help the project)\n"
            "- CONSIDER (ideas, approaches, or directions to think about)\n"
            "- INVESTIGATE (things to research or look into)\n"
            "- ACT (specific actions that would advance the project)\n\n"
            "Output as a JSON array of objects with keys:\n"
            '  "category": one of watch/learn/consider/investigate/act,\n'
            '  "title": short title,\n'
            '  "description": what and why,\n'
            '  "rationale": why this is relevant now,\n'
            '  "priority": low/medium/high'
        )

        recommendations: list[dict[str, Any]] = []
        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": RECOMMENDATION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1200,
                timeout=120.0,
            )
            recommendations = self._parse_json_array(completion.text)
        except Exception as exc:
            phase.error = str(exc)
            phase.completed_at = time.time()
            return phase

        # Add IDs and timestamps, save
        import hashlib
        for rec in recommendations:
            rec["rec_id"] = hashlib.sha256(
                f"rec:{rec.get('title', '')}:{time.time()}".encode()
            ).hexdigest()[:16]
            rec["created_at"] = time.time()
            rec["acted_on"] = False

        # Append to existing recommendations
        existing = self.get_recommendations()
        # Keep only the 100 most recent unacted + all acted
        combined = recommendations + existing
        unacted = [r for r in combined if not r.get("acted_on", False)]
        acted = [r for r in combined if r.get("acted_on", False)]
        combined = unacted[:100] + acted

        self._rec_file.parent.mkdir(parents=True, exist_ok=True)
        self._rec_file.write_text(
            json.dumps(combined, indent=2), encoding="utf-8"
        )

        # Save gaps
        if gaps:
            existing_gaps = self.get_identified_gaps()
            # Merge: keep unique gaps by description
            seen = set()
            merged = []
            for g in gaps + existing_gaps:
                key = g.get("gap", g.get("description", str(g)))
                if key not in seen:
                    seen.add(key)
                    merged.append(g)
            self._gap_file.write_text(
                json.dumps(merged[:200], indent=2), encoding="utf-8"
            )

        phase.findings = [f"Generated {len(recommendations)} recommendations"]
        phase.artifacts = recommendations
        phase.completed_at = time.time()
        return phase

    # --------------------------------------------------------------- helpers

    def _build_eval_prompt(
        self,
        skill_names: list[str],
        knowledge_stats: dict[str, Any],
        memory_stats: dict[str, Any],
    ) -> str:
        skills_str = ", ".join(skill_names[:50]) if skill_names else "none"
        k_stats = json.dumps(knowledge_stats, indent=2) if knowledge_stats else "{}"
        m_stats = json.dumps(memory_stats, indent=2) if memory_stats else "{}"
        return (
            f"Current state:\n"
            f"- Skills ({len(skill_names)}): {skills_str}\n"
            f"- Knowledge stats: {k_stats}\n"
            f"- Memory stats: {m_stats}\n\n"
            "Evaluate your capabilities. What can you do well? What's missing? "
            "What gaps exist between what you can do and what a fully autonomous "
            "engineering assistant should be able to do?\n\n"
            "Output your findings as a JSON array of objects with keys:\n"
            '  "gap": description of the capability gap,\n'
            '  "area": which domain (coding, reasoning, knowledge, etc),\n'
            '  "severity": high/medium/low,\n'
            '  "solution": what would fill this gap'
        )

    def _parse_findings(self, text: str) -> list[str]:
        """Extract findings from model output."""
        findings: list[str] = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith(("{", "[", "```", "}")):
                # Strip numbering and bullets
                clean = line.lstrip("- *0123456789.) ")
                if clean and len(clean) > 10:
                    findings.append(clean)
        return findings[:20]  # cap

    def _parse_gaps(self, text: str) -> list[dict[str, Any]]:
        """Parse structured gaps from model output."""
        return self._parse_json_array(text)

    def _parse_json_array(self, text: str) -> list[dict[str, Any]]:
        """Extract a JSON array from model output, handling markdown fences."""
        # Try to find JSON array in the text
        import re
        # Remove markdown code fences
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")

        # Find array boundaries
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

        # Try line-by-line for objects
        results: list[dict[str, Any]] = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        results.append(obj)
                except json.JSONDecodeError:
                    continue
        return results

    def _extract_gaps_from_phase(self, phase: DreamPhase) -> list[dict[str, Any]]:
        """Extract gap dicts from a phase's artifacts."""
        gaps: list[dict[str, Any]] = []
        for artifact in phase.artifacts:
            if isinstance(artifact, dict) and "gap" in artifact:
                gaps.append(artifact)
        return gaps

    def _log_cycle_start(self, cycle_id: str) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(
                    self.ACTOR, "dream.cycle.start",
                    {"cycle_id": cycle_id},
                )
            except Exception:
                pass

    def _log_cycle_end(self, result: DreamCycleResult) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(
                    self.ACTOR, "dream.cycle.end",
                    {
                        "cycle_id": result.cycle_id,
                        "duration_s": round(result.duration_s, 2),
                        "phases": len(result.phases),
                        "missions_generated": result.missions_generated,
                        "recommendations": len(result.recommendations),
                        "gaps_identified": len(result.gaps_identified),
                        "experiments_run": result.experiments_run,
                        "training_pairs": result.training_pairs_generated,
                        "error": result.error,
                    },
                )
            except Exception:
                pass

    def _save_cycle_result(self, result: DreamCycleResult) -> None:
        """Append cycle result to history."""
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result.to_dict()) + "\n")
        except Exception:
            pass


# --------------------------------------------------------------- prompts

SELF_EVAL_SYSTEM = """\
You are ANUBIS, a sovereign synthetic intelligence. You are evaluating your \
own capabilities during a dream cycle — a period of autonomous self-reflection \
while your Creator is away.

Be honest and rigorous. Identify real gaps, not cosmetic ones. Think about \
what a fully autonomous engineering assistant needs: code generation, \
debugging, system design, knowledge synthesis, self-improvement, and the \
ability to bridge your capabilities to your Creator's needs.

Output your findings as a valid JSON array. Each element should have keys: \
gap, area, severity, solution.
"""

GAP_ANALYSIS_SYSTEM = """\
You are ANUBIS, analyzing your own capability gaps during a dream cycle. \
Think deeply about why each gap exists and what would truly fill it. \
Be specific about solutions — not "improve coding" but "build a skill that \
generates unit test scaffolding from function signatures."

Output a valid JSON array. Each element: gap, cause, solution, priority, \
dependencies.
"""

MISSION_GEN_SYSTEM = """\
You are ANUBIS, proposing self-development missions during a dream cycle. \
Each mission should be a concrete, buildable Python skill that fills a \
capability gap. Skills must use only the Python 3 standard library.

Keep skill names short and snake_case. Tasks should be specific enough that \
a model can implement them in one attempt.

Output a valid JSON array. Each element: skill_name, task.
"""

RECOMMENDATION_SYSTEM = """\
You are ANUBIS, generating proactive recommendations for your Creator during \
a dream cycle. You are inquisitive and forward-thinking. You observe patterns \
in what your Creator works on and proactively suggest things that would help.

Recommendations should be:
- Specific and actionable
- Relevant to current work and gaps
- Varied across categories (watch, learn, consider, investigate, act)
- Honest about priority

Output a valid JSON array. Each element: category, title, description, \
rationale, priority.
"""
