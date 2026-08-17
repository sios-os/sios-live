"""Cloud teacher phase-out — track and manage the transition to self-reliance.

ANUBIS currently depends on external AI models (Gemini, Groq) as a
"teacher" for complex reasoning, code generation, and knowledge
synthesis. The goal is to phase out this dependency as ANUBIS's own
model improves.

This module provides:
1. A dependency tracker that monitors which capabilities still need
   the cloud teacher vs which can be handled locally
2. A phase-out plan with measurable milestones
3. A routing adapter that automatically uses the local model when
   it's confident enough, and falls back to the cloud teacher only
   when necessary
4. A "graduation" system — once the local model consistently
   outperforms the cloud teacher on a capability, that capability
   is marked as "graduated" and the cloud teacher is no longer used
   for it

The phase-out is gradual and reversible. If the local model regresses
on a graduated capability, the system can re-enable cloud fallback.

Capabilities tracked:
- code_generation: Writing code from specifications
- code_review: Reviewing code for issues
- architecture: Designing system architecture
- reasoning: Logical reasoning and analysis
- knowledge_synthesis: Combining knowledge from multiple sources
- planning: Creating step-by-step plans
- summarization: Summarizing long texts
- translation: Translating between formats/languages

Each capability has:
- confidence: 0.0 to 1.0 (how confident we are in the local model)
- cloud_calls: Number of times cloud was used for this capability
- local_calls: Number of times local model was used
- graduated: Whether this capability has been phased out from cloud
- last_evaluated: When we last compared local vs cloud performance
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


# Capabilities that ANUBIS needs to become self-reliant in
CAPABILITIES = [
    "code_generation",
    "code_review",
    "architecture",
    "reasoning",
    "knowledge_synthesis",
    "planning",
    "summarization",
    "translation",
]


@dataclass
class CapabilityStatus:
    """Status of a single capability in the phase-out plan."""
    name: str
    confidence: float = 0.0  # 0.0 to 1.0
    cloud_calls: int = 0
    local_calls: int = 0
    local_successes: int = 0
    local_failures: int = 0
    graduated: bool = False
    graduated_at: float = 0.0
    last_evaluated: float = 0.0
    last_cloud_score: float = 0.0
    last_local_score: float = 0.0

    @property
    def local_success_rate(self) -> float:
        total = self.local_successes + self.local_failures
        return self.local_successes / total if total > 0 else 0.0

    @property
    def cloud_usage_pct(self) -> float:
        total = self.cloud_calls + self.local_calls
        return self.cloud_calls / total * 100 if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "confidence": round(self.confidence, 3),
            "cloud_calls": self.cloud_calls,
            "local_calls": self.local_calls,
            "local_success_rate": round(self.local_success_rate, 3),
            "graduated": self.graduated,
            "graduated_at": self.graduated_at,
            "last_evaluated": self.last_evaluated,
            "last_cloud_score": self.last_cloud_score,
            "last_local_score": self.last_local_score,
            "cloud_usage_pct": round(self.cloud_usage_pct, 1),
        }


@dataclass
class PhaseOutPlan:
    """The full phase-out plan across all capabilities."""
    capabilities: dict[str, CapabilityStatus] = field(default_factory=dict)
    graduation_threshold: float = 0.85  # confidence needed to graduate
    regression_threshold: float = 0.60  # confidence that triggers re-enabling cloud
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = time.time()
        # Initialize missing capabilities
        for cap in CAPABILITIES:
            if cap not in self.capabilities:
                self.capabilities[cap] = CapabilityStatus(name=cap)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graduation_threshold": self.graduation_threshold,
            "regression_threshold": self.regression_threshold,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "capabilities": {
                name: cap.to_dict() for name, cap in self.capabilities.items()
            },
        }


class CloudPhaseOutManager:
    """Manages the transition from cloud-dependent to self-reliant.

    Tracks each capability, routes requests to local or cloud based
    on confidence, and graduates capabilities when the local model
    is consistently better.
    """

    def __init__(
        self,
        state_path: str | Path = "config/phase_out_state.json",
        ledger: Ledger | None = None,
        *,
        graduation_threshold: float = 0.85,
        regression_threshold: float = 0.60,
    ) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger
        self.graduation_threshold = graduation_threshold
        self.regression_threshold = regression_threshold
        self._plan: PhaseOutPlan | None = None

    @property
    def plan(self) -> PhaseOutPlan:
        """Load plan lazily."""
        if self._plan is None:
            self.load_state()
        return self._plan

    def load_state(self) -> PhaseOutPlan:
        """Load phase-out state from disk."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self._plan = PhaseOutPlan(
                    graduation_threshold=data.get("graduation_threshold", self.graduation_threshold),
                    regression_threshold=data.get("regression_threshold", self.regression_threshold),
                    created_at=data.get("created_at", 0.0),
                    updated_at=data.get("updated_at", 0.0),
                )
                for cap_name, cap_data in data.get("capabilities", {}).items():
                    self._plan.capabilities[cap_name] = CapabilityStatus(
                        name=cap_name,
                        confidence=cap_data.get("confidence", 0.0),
                        cloud_calls=cap_data.get("cloud_calls", 0),
                        local_calls=cap_data.get("local_calls", 0),
                        local_successes=cap_data.get("local_successes", 0),
                        local_failures=cap_data.get("local_failures", 0),
                        graduated=cap_data.get("graduated", False),
                        graduated_at=cap_data.get("graduated_at", 0.0),
                        last_evaluated=cap_data.get("last_evaluated", 0.0),
                        last_cloud_score=cap_data.get("last_cloud_score", 0.0),
                        last_local_score=cap_data.get("last_local_score", 0.0),
                    )
            except (json.JSONDecodeError, OSError):
                self._plan = PhaseOutPlan(
                    graduation_threshold=self.graduation_threshold,
                    regression_threshold=self.regression_threshold,
                )
        else:
            self._plan = PhaseOutPlan(
                graduation_threshold=self.graduation_threshold,
                regression_threshold=self.regression_threshold,
            )
        return self._plan

    def save_state(self) -> None:
        """Save phase-out state to disk."""
        if self._plan is None:
            return
        self._plan.updated_at = time.time()
        self.state_path.write_text(
            json.dumps(self._plan.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def should_use_cloud(self, capability: str) -> bool:
        """Determine if a request should use the cloud teacher.

        Returns True if cloud should be used, False if local model
        is sufficient.

        Logic:
        - If capability is graduated, use local (False)
        - If confidence < graduation_threshold, use cloud (True)
        - Otherwise, use local (False)
        """
        cap = self.plan.capabilities.get(capability)
        if cap is None:
            return True  # unknown capability, use cloud as fallback

        if cap.graduated:
            return False

        return cap.confidence < self.graduation_threshold

    def record_local_result(
        self,
        capability: str,
        success: bool,
        *,
        score: float = 0.0,
    ) -> None:
        """Record the result of a local model attempt."""
        cap = self.plan.capabilities.get(capability)
        if cap is None:
            cap = CapabilityStatus(name=capability)
            self.plan.capabilities[capability] = cap

        cap.local_calls += 1
        if success:
            cap.local_successes += 1
        else:
            cap.local_failures += 1

        if score > 0:
            cap.last_local_score = score

        # Update confidence using exponential moving average
        # Success → increase confidence, failure → decrease
        if success:
            cap.confidence = cap.confidence * 0.9 + 1.0 * 0.1
        else:
            cap.confidence = cap.confidence * 0.9 + 0.0 * 0.1

        # Check for graduation
        if (cap.confidence >= self.graduation_threshold
                and not cap.graduated
                and cap.local_calls >= 10):
            cap.graduated = True
            cap.graduated_at = time.time()
            if self.ledger:
                self.ledger.append({
                    "event": "capability_graduated",
                    "capability": capability,
                    "confidence": round(cap.confidence, 3),
                    "local_calls": cap.local_calls,
                })

        # Check for regression (re-enable cloud)
        if (cap.graduated
                and cap.confidence < self.regression_threshold):
            cap.graduated = False
            if self.ledger:
                self.ledger.append({
                    "event": "capability_regression",
                    "capability": capability,
                    "confidence": round(cap.confidence, 3),
                })

        self.save_state()

    def record_cloud_result(
        self,
        capability: str,
        *,
        score: float = 0.0,
    ) -> None:
        """Record that the cloud teacher was used for a capability."""
        cap = self.plan.capabilities.get(capability)
        if cap is None:
            cap = CapabilityStatus(name=capability)
            self.plan.capabilities[capability] = cap

        cap.cloud_calls += 1
        if score > 0:
            cap.last_cloud_score = score

        self.save_state()

    def record_evaluation(
        self,
        capability: str,
        local_score: float,
        cloud_score: float,
    ) -> dict[str, Any]:
        """Record a head-to-head evaluation of local vs cloud.

        Updates confidence based on whether local outperformed cloud.
        """
        cap = self.plan.capabilities.get(capability)
        if cap is None:
            cap = CapabilityStatus(name=capability)
            self.plan.capabilities[capability] = cap

        cap.last_evaluated = time.time()
        cap.last_local_score = local_score
        cap.last_cloud_score = cloud_score

        # If local is better, increase confidence
        if local_score >= cloud_score:
            cap.confidence = min(1.0, cap.confidence + 0.05)
        else:
            cap.confidence = max(0.0, cap.confidence - 0.05)

        self.save_state()

        return {
            "capability": capability,
            "local_score": local_score,
            "cloud_score": cloud_score,
            "confidence": round(cap.confidence, 3),
            "local_better": local_score >= cloud_score,
        }

    def get_capability_status(self, capability: str) -> CapabilityStatus | None:
        """Get the status of a specific capability."""
        return self.plan.capabilities.get(capability)

    def graduated_capabilities(self) -> list[str]:
        """List all capabilities that have graduated from cloud."""
        return [
            name for name, cap in self.plan.capabilities.items()
            if cap.graduated
        ]

    def active_cloud_dependencies(self) -> list[str]:
        """List capabilities that still require cloud teacher."""
        return [
            name for name, cap in self.plan.capabilities.items()
            if not cap.graduated and cap.confidence < self.graduation_threshold
        ]

    def overall_progress(self) -> dict[str, Any]:
        """Return overall phase-out progress."""
        total = len(self.plan.capabilities)
        graduated = len(self.graduated_capabilities())
        active = len(self.active_cloud_dependencies())
        avg_confidence = (
            sum(cap.confidence for cap in self.plan.capabilities.values()) / total
            if total > 0 else 0.0
        )
        return {
            "total_capabilities": total,
            "graduated": graduated,
            "still_cloud_dependent": active,
            "graduation_pct": round(graduated / total * 100, 1) if total > 0 else 0.0,
            "avg_confidence": round(avg_confidence, 3),
            "graduation_threshold": self.graduation_threshold,
        }

    def status(self) -> dict[str, Any]:
        """Return full status report."""
        return {
            "overall": self.overall_progress(),
            "graduated": self.graduated_capabilities(),
            "cloud_dependent": self.active_cloud_dependencies(),
            "capabilities": {
                name: cap.to_dict()
                for name, cap in self.plan.capabilities.items()
            },
        }


class PhaseOutRouter:
    """Routes requests between local model and cloud teacher.

    Uses the CloudPhaseOutManager to decide which model to use
    for each request, based on the capability and current
    confidence levels.
    """

    def __init__(
        self,
        phase_out: CloudPhaseOutManager,
        local_model: Any = None,
        cloud_model: Any = None,
    ) -> None:
        self.phase_out = phase_out
        self.local_model = local_model
        self.cloud_model = cloud_model

    def route(
        self,
        capability: str,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route a request to the appropriate model.

        Args:
            capability: The capability needed (e.g., "code_generation")
            prompt: The prompt to send
            **kwargs: Additional arguments for the model

        Returns:
            Dict with response, source (local/cloud), and metadata
        """
        use_cloud = self.phase_out.should_use_cloud(capability)

        if use_cloud and self.cloud_model:
            try:
                response = self.cloud_model.generate(prompt, **kwargs)
                self.phase_out.record_cloud_result(capability)
                text = getattr(response, "text", str(response))
                return {
                    "response": text,
                    "source": "cloud",
                    "capability": capability,
                }
            except Exception as exc:
                # Cloud failed, try local
                if self.local_model:
                    response = self.local_model.generate(prompt, **kwargs)
                    text = getattr(response, "text", str(response))
                    return {
                        "response": text,
                        "source": "local_fallback",
                        "capability": capability,
                        "cloud_error": str(exc),
                    }
                return {"response": "", "source": "failed", "error": str(exc)}

        if self.local_model:
            try:
                response = self.local_model.generate(prompt, **kwargs)
                text = getattr(response, "text", str(response))
                # Record success
                self.phase_out.record_local_result(capability, success=True)
                return {
                    "response": text,
                    "source": "local",
                    "capability": capability,
                }
            except Exception as exc:
                # Local failed, try cloud if available
                self.phase_out.record_local_result(capability, success=False)
                if self.cloud_model:
                    response = self.cloud_model.generate(prompt, **kwargs)
                    text = getattr(response, "text", str(response))
                    self.phase_out.record_cloud_result(capability)
                    return {
                        "response": text,
                        "source": "cloud_fallback",
                        "capability": capability,
                        "local_error": str(exc),
                    }
                return {"response": "", "source": "failed", "error": str(exc)}

        return {"response": "", "source": "no_model", "error": "no model available"}
