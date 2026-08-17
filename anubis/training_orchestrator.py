"""Training orchestrator — the full self-improvement pipeline.

Connects all the pieces:
1. Distillation queue (anubis.distillation) → training data
2. Unsloth adapter (anubis.unsloth_adapter) → training script
3. Model evaluator (anubis.evaluation) → benchmark before/after
4. A/B drive manager (anubis.ab_drive) → safe deployment with rollback
5. Evidence ledger → audit trail

The orchestrator runs a full cycle:
  queue_status → export_dataset → generate_script → (run training)
  → evaluate_candidate → compare_with_current → stage_on_b_drive
  → canary_test → promote_or_rollback

The actual training execution (running the generated script) requires
GPU access and must be approved by the Creator. The orchestrator
prepares everything and presents the plan for approval.

Governance:
- Training jobs require Creator approval before execution
- Promotion requires the candidate to outperform the current model
- All steps are logged to the evidence ledger
- Rollback is automatic on canary failure
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ab_drive import ABDriveManager
from .distillation import KnowledgeDistiller
from .evaluation import ModelEvaluator, EvaluationResult
from .ledger import Ledger
from .unsloth_adapter import UnslothAdapter, TrainingConfig


@dataclass
class TrainingPlan:
    """A plan for a training run, prepared for Creator approval."""
    plan_id: str = ""
    created_at: float = 0.0
    queue_size: int = 0
    dataset_path: str = ""
    script_path: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    estimated_vram_mb: int = 0
    estimated_time_minutes: float = 0.0
    uses_unsloth: bool = False
    status: str = "pending_approval"  # pending_approval, approved, running, completed, rejected

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "queue_size": self.queue_size,
            "dataset_path": self.dataset_path,
            "script_path": self.script_path,
            "config": self.config,
            "estimated_vram_mb": self.estimated_vram_mb,
            "estimated_time_minutes": self.estimated_time_minutes,
            "uses_unsloth": self.uses_unsloth,
            "status": self.status,
        }


@dataclass
class TrainingCycleResult:
    """Result of a full training cycle."""
    plan_id: str = ""
    trained: bool = False
    evaluated: bool = False
    staged: bool = False
    promoted: bool = False
    rolled_back: bool = False
    candidate_score: float = 0.0
    current_score: float = 0.0
    recommendation: str = ""
    error: str = ""
    duration_s: float = 0.0


class TrainingOrchestrator:
    """Orchestrates the full self-improvement training cycle.

    This is the conductor that connects distillation, training,
    evaluation, and A/B deployment into a single governed pipeline.
    """

    def __init__(
        self,
        distiller: KnowledgeDistiller | None = None,
        unsloth: UnslothAdapter | None = None,
        evaluator: ModelEvaluator | None = None,
        ab_drive: ABDriveManager | None = None,
        ledger: Ledger | None = None,
        output_dir: str | Path = "training",
    ) -> None:
        self.distiller = distiller or KnowledgeDistiller()
        self.unsloth = unsloth or UnslothAdapter()
        self.evaluator = evaluator or ModelEvaluator()
        self.ab_drive = ab_drive or ABDriveManager()
        self.ledger = ledger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._plans: dict[str, TrainingPlan] = {}

    def prepare_training_plan(
        self,
        config: TrainingConfig | None = None,
        *,
        min_quality: float = 0.2,
        category: str | None = None,
    ) -> TrainingPlan:
        """Prepare a training plan for Creator approval.

        This does NOT execute training — it prepares the dataset,
        generates the training script, and estimates resource usage.

        Args:
            config: Training configuration (uses default if None)
            min_quality: Minimum quality score for training pairs
            category: Filter by category (None = all)

        Returns:
            TrainingPlan ready for Creator review
        """
        config = config or TrainingConfig()
        plan_id = f"plan_{int(time.time())}"

        # Check distillation queue
        queue_stats = self.distiller.stats()
        queue_size = queue_stats["queued_pairs"]

        if queue_size == 0:
            return TrainingPlan(
                plan_id=plan_id,
                created_at=time.time(),
                status="empty_queue",
            )

        # Export training dataset
        dataset_path = self.output_dir / f"{plan_id}_dataset.jsonl"
        export_result = self.distiller.export_training_data(
            dataset_path, category=category, min_quality=min_quality
        )

        # Generate training script
        script_path = self.output_dir / f"{plan_id}_train.py"
        script = self.unsloth.generate_training_script(config, str(dataset_path))
        self.unsloth.save_script(script, script_path)

        # Estimate performance
        estimate = self.unsloth.estimate_performance(
            config, dataset_size=export_result["exported"]
        )

        plan = TrainingPlan(
            plan_id=plan_id,
            created_at=time.time(),
            queue_size=queue_size,
            dataset_path=str(dataset_path),
            script_path=str(script_path),
            config=config.to_dict(),
            estimated_vram_mb=estimate.estimated_vram_with_unsloth_mb
            if self.unsloth.is_available()
            else estimate.estimated_vram_mb,
            estimated_time_minutes=estimate.estimated_time_with_unsloth_minutes
            if self.unsloth.is_available()
            else estimate.estimated_time_minutes,
            uses_unsloth=self.unsloth.is_available(),
            status="pending_approval",
        )

        self._plans[plan_id] = plan

        if self.ledger:
            self.ledger.append({
                "event": "training_plan_prepared",
                "plan_id": plan_id,
                "queue_size": queue_size,
                "dataset_exported": export_result["exported"],
                "uses_unsloth": plan.uses_unsloth,
            })

        return plan

    def approve_plan(self, plan_id: str) -> dict[str, Any]:
        """Mark a training plan as approved by the Creator.

        The actual training execution must be run separately — this
        just marks the plan as approved in the ledger.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return {"approved": False, "error": "plan not found"}

        plan.status = "approved"

        if self.ledger:
            self.ledger.append({
                "event": "training_plan_approved",
                "plan_id": plan_id,
            })

        return {"approved": True, "plan_id": plan_id}

    def reject_plan(self, plan_id: str, reason: str = "") -> dict[str, Any]:
        """Reject a training plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return {"rejected": False, "error": "plan not found"}

        plan.status = "rejected"

        if self.ledger:
            self.ledger.append({
                "event": "training_plan_rejected",
                "plan_id": plan_id,
                "reason": reason,
            })

        return {"rejected": True, "plan_id": plan_id}

    def evaluate_candidate(
        self,
        candidate_model: Any,
        current_model: Any,
        candidate_name: str = "candidate",
        current_name: str = "current",
    ) -> dict[str, Any]:
        """Evaluate a candidate model against the current model.

        Runs both models through the benchmark suite and produces
        a comparison report with a promotion recommendation.

        Args:
            candidate_model: The newly trained/merged model
            current_model: The currently active model
            candidate_name: Name for the candidate
            current_name: Name for the current model

        Returns:
            Dict with comparison and recommendation
        """
        # Evaluate current model
        current_result = self.evaluator.evaluate(
            current_model, model_name=current_name
        )

        # Evaluate candidate model
        candidate_result = self.evaluator.evaluate(
            candidate_model, model_name=candidate_name
        )

        # Compare
        comparison = self.evaluator.compare(current_result, candidate_result)

        # Save reports
        self.evaluator.save_report(
            current_result,
            self.output_dir / f"eval_{current_name}.json",
        )
        self.evaluator.save_report(
            candidate_result,
            self.output_dir / f"eval_{candidate_name}.json",
        )

        if self.ledger:
            self.ledger.append({
                "event": "candidate_evaluated",
                "candidate": candidate_name,
                "current": current_name,
                "recommendation": comparison["recommendation"],
                "candidate_score": candidate_result.avg_score,
                "current_score": current_result.avg_score,
            })

        return comparison

    def stage_candidate(
        self,
        version: str,
        comparison: dict[str, Any],
    ) -> dict[str, Any]:
        """Stage a candidate model on the A/B drive.

        Only stages if the comparison recommendation is "promote".
        The canary test runs automatically after staging.

        Args:
            version: Version string for the candidate
            comparison: Comparison dict from evaluate_candidate

        Returns:
            Dict with staging status
        """
        if comparison.get("recommendation") != "promote":
            return {
                "staged": False,
                "reason": f"comparison recommendation was '{comparison.get('recommendation')}'",
            }

        # Stage on A/B drive
        stage_result = self.ab_drive.stage_update(version)

        if self.ledger:
            self.ledger.append({
                "event": "candidate_staged",
                "version": version,
                "score": comparison.get("candidate", {}).get("avg_score"),
            })

        return stage_result

    def check_canary_and_promote(self) -> dict[str, Any]:
        """Check canary status and promote if passing.

        Returns:
            Dict with promotion or rollback status
        """
        canary = self.ab_drive.check_canary()

        if not canary.passed and canary.should_rollback:
            # Automatic rollback
            rollback_result = self.ab_drive.rollback(canary.reason)
            if self.ledger:
                self.ledger.append({
                    "event": "canary_failed_rollback",
                    "reason": canary.reason,
                })
            return {
                "promoted": False,
                "rolled_back": True,
                "reason": canary.reason,
                "rollback": rollback_result,
            }

        if canary.passed and not canary.reason.startswith("canary in progress"):
            # Canary completed successfully — promote
            promote_result = self.ab_drive.promote()
            if self.ledger and promote_result.get("promoted"):
                self.ledger.append({
                    "event": "candidate_promoted",
                    "version": promote_result.get("active_version"),
                })
            return {
                "promoted": promote_result.get("promoted", False),
                "canary_reason": canary.reason,
                "promotion": promote_result,
            }

        # Canary still in progress
        return {
            "promoted": False,
            "rolled_back": False,
            "canary_in_progress": True,
            "reason": canary.reason,
        }

    def run_cycle(
        self,
        candidate_model: Any,
        current_model: Any,
        version: str,
        *,
        candidate_name: str = "candidate",
        current_name: str = "current",
    ) -> TrainingCycleResult:
        """Run a full evaluation + staging cycle (without training).

        This is the post-training portion of the pipeline:
        evaluate → compare → stage → (canary runs separately)

        The actual training must be run separately after plan approval.
        """
        t0 = time.monotonic()

        # Evaluate
        comparison = self.evaluate_candidate(
            candidate_model, current_model,
            candidate_name=candidate_name,
            current_name=current_name,
        )

        # Stage if recommended
        staged = False
        if comparison["recommendation"] == "promote":
            stage_result = self.stage_candidate(version, comparison)
            staged = stage_result.get("staged", False)

        return TrainingCycleResult(
            plan_id=version,
            evaluated=True,
            staged=staged,
            candidate_score=comparison.get("candidate", {}).get("avg_score", 0),
            current_score=comparison.get("current", {}).get("avg_score", 0),
            recommendation=comparison["recommendation"],
            duration_s=round(time.monotonic() - t0, 3),
        )

    def status(self) -> dict[str, Any]:
        """Return orchestrator status."""
        queue_stats = self.distiller.stats()
        return {
            "queue_pairs": queue_stats["queued_pairs"],
            "queue_categories": queue_stats["categories"],
            "unsloth_available": self.unsloth.is_available(),
            "ab_drive": self.ab_drive.status(),
            "evaluator": self.evaluator.stats(),
            "pending_plans": sum(
                1 for p in self._plans.values()
                if p.status == "pending_approval"
            ),
            "output_dir": str(self.output_dir),
        }

    def list_plans(self) -> list[dict[str, Any]]:
        """List all training plans."""
        return [p.to_dict() for p in self._plans.values()]

    def get_plan(self, plan_id: str) -> TrainingPlan | None:
        """Get a specific training plan."""
        return self._plans.get(plan_id)
