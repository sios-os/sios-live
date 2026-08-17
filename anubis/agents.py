"""SIOS Agent Framework.

Implements the agent hierarchy from the KBP plan:
  - ANUBIS: receives the mission, selects directors, reconciles findings
  - Domain director: maintains the field map, routes tasks
  - Specialty agent: applies specialty ontology to a bounded problem
  - Temporary micro-agent: performs one narrow decomposition, then expires
  - Independent verifier: checks evidence without seeing other agents' drafts

Agents are not separate models — they are structured prompt contexts
that focus the same local model on different aspects of a problem.
This lets a single 7B model act as multiple specialists by decomposing
the work and applying different instructions to each sub-task.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

from anubis.registry import Registry, KnowledgeBase, Specialty, DomainDirector
from anubis.model import ModelAdapter
from anubis.grounding import KnowledgeGrounding
from anubis.verification import ClaimIndex


class AgentRole(IntEnum):
    ANUBIS = 0
    DIRECTOR = 1
    SPECIALIST = 2
    SUBSPECIALIST = 3
    VERIFIER = 4
    MICRO = 5


@dataclass
class AgentContext:
    """The bounded context an agent operates within."""
    agent_id: str
    role: AgentRole
    specialty_id: str = ""
    director_id: str = ""
    task: str = ""
    instructions: str = ""
    capabilities: list[str] = field(default_factory=list)
    time_limit: float = 30.0
    compute_limit_mb: int = 256
    created_at: float = 0.0
    expires_at: float = 0.0
    # Results
    output: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role.name,
            "specialty_id": self.specialty_id,
            "director_id": self.director_id,
            "task": self.task,
            "instructions": self.instructions,
            "capabilities": self.capabilities,
            "time_limit": self.time_limit,
            "compute_limit_mb": self.compute_limit_mb,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "output": self.output,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "completed": self.completed,
        }


class AgentFramework:
    """Manages agent creation, delegation, and result reconciliation.

    The framework creates structured prompts for each agent role and
    uses the local model to fill them. Directors route tasks to
    specialists; specialists produce bounded outputs; verifiers
    check outputs independently.
    """

    def __init__(
        self, registry: Registry, knowledge: KnowledgeBase,
        model: ModelAdapter, root: str | Path,
        grounding: KnowledgeGrounding | None = None,
    ) -> None:
        self.registry = registry
        self.knowledge = knowledge
        self.model = model
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._agents: dict[str, AgentContext] = {}
        self._counter = 0
        # Knowledge grounding for claim-based fact-checking
        self.grounding = grounding or KnowledgeGrounding(knowledge)
        self.claim_index = self.grounding.index

    def _next_id(self, prefix: str = "agent") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter:04d}"

    # ------------------------------------------------------------------ prompts

    def _director_prompt(self, director: DomainDirector, task: str) -> str:
        """Build a prompt for a domain director."""
        spec_names = []
        for sid in director.specialty_ids:
            spec = self.registry.get_specialty(sid)
            if spec:
                spec_names.append(spec.canonical_name)
        return (
            f"You are the {director.name} director in the SIOS knowledge system.\n"
            f"Your domain covers: {', '.join(spec_names[:10])}\n"
            f"Your charter: {director.charter}\n\n"
            f"Task: {task}\n\n"
            f"Identify which specialty within your domain is most relevant. "
            f"Respond with:\n"
            f"SPECIALTY: <specialty_name>\n"
            f"APPROACH: <brief description of how to handle this task>\n"
            f"DECOMPOSITION: <list of sub-tasks if the task is complex>\n"
        )

    def _specialist_prompt(self, specialty: Specialty, task: str, context: str = "") -> str:
        """Build a prompt for a specialty agent."""
        knowledge_ctx = self.knowledge.retrieve_context(task, specialty_id=specialty.specialty_id)
        # Also retrieve atomic claims for this specialty and task
        claims = self.claim_index.search(task, limit=8)
        parts = [
            f"You are a {specialty.canonical_name} specialist.",
            f"Scope: {specialty.scope_statement}",
        ]
        if specialty.regulated_domain:
            parts.append("WARNING: This is a regulated domain. Provide evidence and decision support only. Do not present conclusions as professional determinations.")
        if knowledge_ctx:
            parts.append(knowledge_ctx)
        if claims:
            parts.append("--- Verified Claims from Knowledge Library ---")
            for c in claims:
                ct = c.get("claim_type", "fact")
                status = c.get("verification_status", "unverified")
                conf = c.get("confidence_adjusted", c.get("confidence", 0.8))
                text = c.get("text", "")
                parts.append(f"  [{ct}|{status}|conf={conf:.2f}] {text}")
            parts.append("")
        if context:
            parts.append(f"Context from director: {context}")
        parts.append(f"\nTask: {task}")
        parts.append(
            "\nProvide a thorough answer with citations to sources where possible. "
            "If you are uncertain, state your uncertainty. Do not fabricate evidence. "
            "Reference specific claims from the knowledge library when they support your answer."
        )
        return "\n".join(parts)

    def _verifier_prompt(self, task: str, output_to_verify: str, checks: list[str]) -> str:
        """Build a prompt for an independent verifier.

        The verifier does NOT see who produced the output — only the
        output itself and the task it was meant to address.
        Includes relevant claims from the knowledge library for fact-checking.
        """
        checks_str = "\n".join(f"  - {c}" for c in checks)
        # Retrieve claims relevant to the task for fact-checking
        claims = self.claim_index.search(task, limit=10)
        claims_block = ""
        if claims:
            claims_block = "\n\n--- Knowledge Library Claims for Fact-Checking ---\n"
            for c in claims:
                ct = c.get("claim_type", "fact")
                status = c.get("verification_status", "unverified")
                text = c.get("text", "")
                claims_block += f"  [{ct}|{status}] {text}\n"
            claims_block += "\nUse these claims to check the output for factual accuracy.\n"
        return (
            f"You are an independent verifier in the SIOS knowledge system.\n"
            f"You must verify the following output without knowing who produced it.\n\n"
            f"Original task: {task}\n"
            f"Output to verify:\n{output_to_verify}\n\n"
            f"Checks to perform:\n{checks_str}\n"
            f"{claims_block}\n"
            f"Respond with:\n"
            f"VERDICT: <pass|fail|needs_revision>\n"
            f"ISSUES: <list of any problems found>\n"
            f"CONFIDENCE: <0.0 to 1.0>\n"
        )

    # ------------------------------------------------------------------ delegation

    def route_task(self, task: str) -> dict[str, Any]:
        """Route a task through the agent hierarchy.

        1. ANUBIS selects the most relevant director
        2. The director identifies the specialty and approach
        3. The specialist produces the output
        4. An independent verifier checks the output
        5. ANUBIS reconciles and returns the result
        """
        results: dict[str, Any] = {
            "task": task,
            "timestamp": time.time(),
            "steps": [],
        }

        # Step 1: Select director by keyword matching
        best_director = self._select_director(task)
        if best_director is None:
            results["error"] = "no relevant director found"
            return results

        results["director"] = best_director.name
        results["steps"].append(f"Routed to {best_director.name}")

        # Step 2: Director identifies specialty and approach
        director_ctx = AgentContext(
            agent_id=self._next_id("director"),
            role=AgentRole.DIRECTOR,
            director_id=best_director.director_id,
            task=task,
            instructions=self._director_prompt(best_director, task),
            created_at=time.time(),
        )
        director_ctx.output = self.model.generate(director_ctx.instructions)
        director_ctx.completed = True
        self._agents[director_ctx.agent_id] = director_ctx
        results["director_output"] = director_ctx.output
        results["steps"].append("Director identified specialty and approach")

        # Parse director output to find specialty
        specialty = self._parse_specialty_from_director(director_ctx.output, best_director)
        if specialty is None:
            # Fall back to first specialty in director
            specs = self.registry.specialties_by_director(best_director.director_id)
            if specs:
                specialty = specs[0]
        if specialty is None:
            results["error"] = "no specialty found"
            return results

        results["specialty"] = specialty.canonical_name
        results["steps"].append(f"Specialty: {specialty.canonical_name}")

        # Step 3: Specialist produces output
        specialist_ctx = AgentContext(
            agent_id=self._next_id("specialist"),
            role=AgentRole.SPECIALIST,
            specialty_id=specialty.specialty_id,
            director_id=best_director.director_id,
            task=task,
            instructions=self._specialist_prompt(specialty, task, director_ctx.output),
            created_at=time.time(),
        )
        specialist_ctx.output = self.model.generate(specialist_ctx.instructions)
        specialist_ctx.completed = True
        self._agents[specialist_ctx.agent_id] = specialist_ctx
        results["specialist_output"] = specialist_ctx.output
        results["steps"].append("Specialist produced output")

        # Step 4: Independent verifier checks output
        verifier_checks = [
            "Is the output factually correct within the stated scope?",
            "Does the output address the original task?",
            "Are there any unsupported claims?",
            "Is uncertainty appropriately stated?",
        ]
        verifier_ctx = AgentContext(
            agent_id=self._next_id("verifier"),
            role=AgentRole.VERIFIER,
            task=task,
            instructions=self._verifier_prompt(task, specialist_ctx.output, verifier_checks),
            created_at=time.time(),
        )
        verifier_ctx.output = self.model.generate(verifier_ctx.instructions)
        verifier_ctx.completed = True
        self._agents[verifier_ctx.agent_id] = verifier_ctx
        results["verifier_output"] = verifier_ctx.output
        results["steps"].append("Verifier checked output")

        # Step 5: Reconcile
        verdict = self._parse_verifier_verdict(verifier_ctx.output)
        results["verdict"] = verdict
        results["confidence"] = self._parse_verifier_confidence(verifier_ctx.output)
        results["steps"].append(f"Final verdict: {verdict}")

        return results

    def _select_director(self, task: str) -> DomainDirector | None:
        """Select the most relevant director for a task by keyword matching."""
        task_terms = set(task.lower().split())
        best = None
        best_score = 0
        for director in self.registry.directors():
            # Match against director name and description
            dir_terms = set(director.name.lower().split())
            dir_terms.update(set(director.description.lower().split()))
            # Match against specialty names
            for sid in director.specialty_ids:
                spec = self.registry.get_specialty(sid)
                if spec:
                    dir_terms.update(set(spec.canonical_name.lower().split()))
            score = len(task_terms & dir_terms)
            if score > best_score:
                best_score = score
                best = director
        return best

    def _parse_specialty_from_director(
        self, director_output: str, director: DomainDirector,
    ) -> Specialty | None:
        """Parse the SPECIALTY: line from director output."""
        for line in director_output.split("\n"):
            if line.strip().upper().startswith("SPECIALTY:"):
                name = line.split(":", 1)[1].strip()
                # Find matching specialty in this director
                for sid in director.specialty_ids:
                    spec = self.registry.get_specialty(sid)
                    if spec and (
                        name.lower() in spec.canonical_name.lower()
                        or spec.canonical_name.lower() in name.lower()
                    ):
                        return spec
        return None

    def _parse_verifier_verdict(self, output: str) -> str:
        """Parse the VERDICT: line from verifier output."""
        for line in output.split("\n"):
            if line.strip().upper().startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip().lower()
                if "pass" in verdict:
                    return "pass"
                elif "fail" in verdict:
                    return "fail"
                elif "revision" in verdict:
                    return "needs_revision"
        return "unknown"

    def _parse_verifier_confidence(self, output: str) -> float:
        """Parse the CONFIDENCE: line from verifier output."""
        for line in output.split("\n"):
            if line.strip().upper().startswith("CONFIDENCE:"):
                try:
                    val = float(line.split(":", 1)[1].strip())
                    return max(0.0, min(1.0, val))
                except ValueError:
                    pass
        return 0.0

    # ------------------------------------------------------------------ queries

    def agents(self) -> list[AgentContext]:
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> AgentContext | None:
        return self._agents.get(agent_id)

    def stats(self) -> dict[str, Any]:
        role_counts = {}
        for agent in self._agents.values():
            role_counts[agent.role.name] = role_counts.get(agent.role.name, 0) + 1
        return {
            "total_agents": len(self._agents),
            "role_distribution": role_counts,
            "completed": sum(1 for a in self._agents.values() if a.completed),
        }
