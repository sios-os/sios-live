"""Mixed model training strategy — progressive weight replacement.

ANUBIS's path to becoming his own unique model is not a single training run.
It's a gradual process where he starts as a mix of existing models and
progressively replaces external weights with his own:

Stage 1: **Distillation** — Learn from multiple teacher models (Gemini, Groq,
qwen2.5-coder) by recording their outputs as training pairs. ANUBIS's behavior
is a mix of these teachers.

Stage 2: **Initial fine-tune** — Fine-tune a small base model (e.g., a 1B
parameter model) on accumulated distillation data. This produces "ANUBIS v0.1"
— a model that has learned from all teachers but has its own weights.

Stage 3: **Mixture of Experts** — Run ANUBIS's small model alongside teacher
models. Use his model for tasks where it performs well, teachers where they
perform better. The cloud_phaseout system manages this transition.

Stage 4: **Iterative improvement** — Each training cycle produces a new
version. Versions are evaluated, compared, and promoted if better. Over time,
ANUBIS's model handles more tasks and teachers handle fewer.

Stage 5: **Self-distillation** — Once ANUBIS's model is good enough, he
generates his own training data by solving problems and verifying the
solutions. This removes the need for teacher models entirely.

Stage 6: **Full sovereignty** — ANUBIS's model handles all tasks. Teacher
models are retired. His weights are entirely his own.

This module manages the progression through these stages, tracking which
stage ANUBIS is in and what's needed to advance.

Uses only the Python standard library.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------- stages

STAGES = {
    1: "distillation",
    2: "initial_finetune",
    3: "mixture_of_experts",
    4: "iterative_improvement",
    5: "self_distillation",
    6: "full_sovereignty",
}

STAGE_DESCRIPTIONS = {
    1: "Learning from multiple teacher models by recording outputs as training pairs",
    2: "Fine-tuning a small base model on accumulated distillation data",
    3: "Running ANUBIS model alongside teachers, transitioning per-capability",
    4: "Iterative training cycles producing progressively better versions",
    5: "ANUBIS generates his own training data by solving and verifying problems",
    6: "ANUBIS's model handles all tasks. Teachers retired. Full sovereignty.",
}


@dataclass
class ModelGeneration:
    """A generation of ANUBIS's model."""
    gen_id: str
    version: str  # e.g., "0.1", "0.2", "1.0"
    stage: int
    base_model: str  # what was the starting point
    training_pairs_used: int = 0
    teachers_used: list[str] = field(default_factory=list)
    capabilities_tested: int = 0
    capabilities_passed: int = 0
    overall_score: float = 0.0
    created_at: float = 0.0
    artifact_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gen_id": self.gen_id,
            "version": self.version,
            "stage": self.stage,
            "base_model": self.base_model,
            "training_pairs_used": self.training_pairs_used,
            "teachers_used": self.teachers_used,
            "capabilities_tested": self.capabilities_tested,
            "capabilities_passed": self.capabilities_passed,
            "overall_score": self.overall_score,
            "created_at": self.created_at,
            "artifact_path": self.artifact_path,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelGeneration":
        return cls(
            gen_id=data.get("gen_id", ""),
            version=data.get("version", ""),
            stage=data.get("stage", 1),
            base_model=data.get("base_model", ""),
            training_pairs_used=data.get("training_pairs_used", 0),
            teachers_used=data.get("teachers_used", []),
            capabilities_tested=data.get("capabilities_tested", 0),
            capabilities_passed=data.get("capabilities_passed", 0),
            overall_score=data.get("overall_score", 0.0),
            created_at=data.get("created_at", 0.0),
            artifact_path=data.get("artifact_path", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class StageProgress:
    """Progress within a stage."""
    stage: int
    started_at: float = 0.0
    completed_at: float = 0.0
    requirements_total: int = 0
    requirements_met: int = 0
    notes: str = ""

    @property
    def is_complete(self) -> bool:
        return (
            self.requirements_total > 0
            and self.requirements_met >= self.requirements_total
        )

    @property
    def progress_pct(self) -> float:
        if self.requirements_total == 0:
            return 0.0
        return (self.requirements_met / self.requirements_total) * 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "stage_name": STAGES.get(self.stage, "unknown"),
            "description": STAGE_DESCRIPTIONS.get(self.stage, ""),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "requirements_total": self.requirements_total,
            "requirements_met": self.requirements_met,
            "progress_pct": round(self.progress_pct, 1),
            "is_complete": self.is_complete,
            "notes": self.notes,
        }


# --------------------------------------------------------------- manager


class MixedModelStrategy:
    """Manages ANUBIS's progressive transition to a unique model.

    Tracks:
    - Current stage
    - Progress within stage
    - All model generations
    - Teacher dependency levels
    - Advancement criteria

    The strategy is designed to be checked by the training orchestrator
    and dream cycle to determine what training work should happen next.
    """

    ACTOR = "anubis.mixed_model"

    # Requirements to advance from each stage
    STAGE_REQUIREMENTS = {
        1: {  # distillation
            "min_training_pairs": 500,
            "min_teachers": 2,
            "min_categories": 3,
        },
        2: {  # initial_finetune
            "min_training_pairs": 1000,
            "base_model_selected": True,
            "training_run_completed": True,
            "min_overall_score": 0.3,
        },
        3: {  # mixture_of_experts
            "min_capabilities_tested": 10,
            "min_capabilities_graduated": 3,
            "phaseout_active": True,
        },
        4: {  # iterative_improvement
            "min_generations": 3,
            "min_score_improvement": 0.15,
            "self_distill_data": True,
        },
        5: {  # self_distillation
            "min_self_generated_pairs": 2000,
            "min_capabilities_graduated": 8,
            "teacher_free_categories": 5,
        },
        6: {  # full_sovereignty
            "all_capabilities_graduated": True,
            "no_teachers_needed": True,
        },
    }

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._state_dir = self.root / "memory" / "model_strategy"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_dir / "state.json"
        self._generations_file = self._state_dir / "generations.json"
        self._progress_file = self._state_dir / "stage_progress.json"

    def get_current_stage(self) -> int:
        """Get the current stage number."""
        state = self._load_state()
        return state.get("current_stage", 1)

    def get_stage_info(self) -> dict[str, Any]:
        """Get detailed info about the current stage."""
        stage = self.get_current_stage()
        progress = self._load_progress().get(str(stage), {})
        requirements = self.STAGE_REQUIREMENTS.get(stage, {})
        generations = self.get_generations()

        return {
            "current_stage": stage,
            "stage_name": STAGES.get(stage, "unknown"),
            "description": STAGE_DESCRIPTIONS.get(stage, ""),
            "progress": progress,
            "requirements": requirements,
            "total_generations": len(generations),
            "latest_generation": generations[-1] if generations else None,
            "all_stages": [
                {
                    "stage": s,
                    "name": STAGES[s],
                    "description": STAGE_DESCRIPTIONS[s],
                }
                for s in sorted(STAGES.keys())
            ],
        }

    def get_generations(self) -> list[dict[str, Any]]:
        """Get all model generations."""
        if not self._generations_file.exists():
            return []
        try:
            data = json.loads(
                self._generations_file.read_text(encoding="utf-8")
            )
            return data
        except Exception:
            return []

    def record_generation(self, gen: ModelGeneration) -> None:
        """Record a new model generation."""
        generations = self.get_generations()
        generations.append(gen.to_dict())
        self._generations_file.write_text(
            json.dumps(generations, indent=2), encoding="utf-8"
        )

        # Update state if this generation advances the stage
        state = self._load_state()
        if gen.stage > state.get("current_stage", 1):
            state["current_stage"] = gen.stage
            self._save_state(state)

    def update_progress(
        self,
        stage: int,
        *,
        requirements_met: int | None = None,
        requirements_total: int | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        """Update progress within a stage."""
        progress = self._load_progress()
        key = str(stage)
        current = progress.get(key, {
            "stage": stage,
            "started_at": time.time(),
            "requirements_total": 0,
            "requirements_met": 0,
            "notes": "",
        })

        if requirements_met is not None:
            current["requirements_met"] = requirements_met
        if requirements_total is not None:
            current["requirements_total"] = requirements_total
        if notes:
            current["notes"] = notes

        if (
            current["requirements_total"] > 0
            and current["requirements_met"] >= current["requirements_total"]
            and not current.get("completed_at")
        ):
            current["completed_at"] = time.time()

        progress[key] = current
        self._progress_file.write_text(
            json.dumps(progress, indent=2), encoding="utf-8"
        )
        return current

    def check_advancement(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Check if ANUBIS can advance to the next stage.

        Args:
            metrics: Current metrics (training_pairs, teachers, scores, etc.)

        Returns:
            Dict with advancement status and what's missing
        """
        stage = self.get_current_stage()
        requirements = self.STAGE_REQUIREMENTS.get(stage, {})

        met = 0
        total = len(requirements)
        missing: list[str] = []

        for req, threshold in requirements.items():
            value = metrics.get(req, 0)
            if isinstance(threshold, bool):
                if value == threshold:
                    met += 1
                else:
                    missing.append(f"{req}: need {threshold}, have {value}")
            elif isinstance(threshold, (int, float)):
                if value >= threshold:
                    met += 1
                else:
                    missing.append(
                        f"{req}: need {threshold}, have {value}"
                    )

        can_advance = met >= total and total > 0

        result = {
            "current_stage": stage,
            "stage_name": STAGES.get(stage, "unknown"),
            "requirements_met": met,
            "requirements_total": total,
            "can_advance": can_advance,
            "missing": missing,
            "next_stage": stage + 1 if can_advance else None,
            "next_stage_name": STAGES.get(stage + 1) if can_advance else None,
        }

        # Update progress
        self.update_progress(
            stage,
            requirements_met=met,
            requirements_total=total,
            notes="; ".join(missing) if missing else "All requirements met",
        )

        return result

    def advance_stage(self, notes: str = "") -> dict[str, Any]:
        """Advance to the next stage. Called after check_advancement confirms."""
        state = self._load_state()
        current = state.get("current_stage", 1)
        next_stage = current + 1

        if next_stage > max(STAGES.keys()):
            return {"error": "Already at maximum stage"}

        state["current_stage"] = next_stage
        state["advanced_at"] = time.time()
        self._save_state(state)

        # Initialize progress for new stage
        self.update_progress(
            next_stage,
            requirements_met=0,
            requirements_total=len(self.STAGE_REQUIREMENTS.get(next_stage, {})),
            notes=notes or f"Advanced from stage {current}",
        )

        return {
            "advanced_from": current,
            "advanced_to": next_stage,
            "stage_name": STAGES.get(next_stage, "unknown"),
            "description": STAGE_DESCRIPTIONS.get(next_stage, ""),
        }

    def get_teacher_dependency(self) -> dict[str, Any]:
        """Get current teacher dependency level."""
        stage = self.get_current_stage()
        generations = self.get_generations()

        # Calculate how much we still depend on teachers
        if stage == 1:
            dependency = 1.0  # fully dependent
        elif stage == 2:
            dependency = 0.8
        elif stage == 3:
            dependency = 0.5
        elif stage == 4:
            dependency = 0.3
        elif stage == 5:
            dependency = 0.1
        elif stage == 6:
            dependency = 0.0
        else:
            dependency = 1.0

        return {
            "current_stage": stage,
            "teacher_dependency": dependency,
            "self_sovereignty": 1.0 - dependency,
            "generations_trained": len(generations),
            "latest_score": (
                generations[-1].get("overall_score", 0.0)
                if generations else 0.0
            ),
        }

    def get_status(self) -> dict[str, Any]:
        """Get full strategy status."""
        return {
            "current_stage": self.get_current_stage(),
            "stage_info": self.get_stage_info(),
            "teacher_dependency": self.get_teacher_dependency(),
            "generations": len(self.get_generations()),
        }

    # ------------------------------------------------------- internals

    def _load_state(self) -> dict[str, Any]:
        if self._state_file.exists():
            try:
                return json.loads(
                    self._state_file.read_text(encoding="utf-8")
                )
            except Exception:
                pass
        return {"current_stage": 1}

    def _save_state(self, state: dict[str, Any]) -> None:
        self._state_file.write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )

    def _load_progress(self) -> dict[str, Any]:
        if self._progress_file.exists():
            try:
                return json.loads(
                    self._progress_file.read_text(encoding="utf-8")
                )
            except Exception:
                pass
        return {}
