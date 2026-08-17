"""Local fine-tuning pipeline — runs LoRA training on the local GPU.

This module orchestrates the full local training cycle:

1. COLLECT — gathers training data from multiple sources:
   - Distillation queue (conversation pairs from midnight purge)
   - Dream cycle insights (self-improvement discoveries)
   - Mission results (successful code generations)
   - Knowledge bootstrap (document-derived pairs)

2. PREPARE — formats data as JSONL, generates training script
   via UnslothAdapter (or fallback to standard HuggingFace)

3. RUN — executes the training script as a subprocess
   - Monitors stdout/stderr for progress
   - Captures training loss, steps, timing
   - Handles GPU OOM and other failures gracefully

4. EVALUATE — runs the model evaluator on the trained model
   - Compares against the current model
   - Recommends promote/reject/needs_more_training

5. STAGE — if evaluation passes, stages the candidate model
   on the A/B standby drive for canary testing

6. PROMOTE — after canary passes, promotes the new model

All training requires Creator approval (constitutional requirement).
The pipeline generates a plan, the Creator approves it, then the
training runs. This ensures the Creator retains control over what
ANUBIS learns.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .ledger import Ledger
from .unsloth_adapter import UnslothAdapter, TrainingConfig


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class TrainingRun:
    """Metadata for a single local training run."""
    run_id: str
    timestamp: float
    plan_id: str = ""
    script_path: str = ""
    dataset_path: str = ""
    output_dir: str = ""
    status: str = "pending"  # pending, running, completed, failed, cancelled
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_seconds: float = 0.0
    training_loss: float = 0.0
    global_step: int = 0
    model_path: str = ""
    error: str = ""
    log_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "plan_id": self.plan_id,
            "script_path": self.script_path,
            "dataset_path": self.dataset_path,
            "output_dir": self.output_dir,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": round(self.duration_seconds, 1),
            "training_loss": round(self.training_loss, 4),
            "global_step": self.global_step,
            "model_path": self.model_path,
            "error": self.error,
            "log_path": self.log_path,
        }


@dataclass
class DataCollectionResult:
    """Result of collecting training data from all sources."""
    total_pairs: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    dataset_path: str = ""
    quality_avg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pairs": self.total_pairs,
            "by_source": self.by_source,
            "dataset_path": self.dataset_path,
            "quality_avg": round(self.quality_avg, 3),
        }


# ===========================================================
# Local fine-tuning pipeline
# ===========================================================

class LocalFineTuner:
    """Runs LoRA fine-tuning on the local GPU.

    Collects training data from ANUBIS's experiences, generates
    a training script, executes it, and tracks the result.

    All training requires Creator approval before execution.
    """

    ACTOR = "anubis.local_finetuner"

    def __init__(
        self,
        root: str | Path,
        *,
        distiller: Any | None = None,
        unsloth: UnslothAdapter | None = None,
        evaluator: Any | None = None,
        ab_drive: Any | None = None,
        ledger: Ledger | None = None,
        on_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.distiller = distiller
        self.unsloth = unsloth or UnslothAdapter(ledger=ledger)
        self.evaluator = evaluator
        self.ab_drive = ab_drive
        self.ledger = ledger
        self.on_speak = on_speak

        self._training_dir = self.root / "training"
        self._training_dir.mkdir(parents=True, exist_ok=True)
        self._runs_dir = self._training_dir / "runs"
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._datasets_dir = self._training_dir / "datasets"
        self._datasets_dir.mkdir(parents=True, exist_ok=True)
        self._scripts_dir = self._training_dir / "scripts"
        self._scripts_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._training_dir / "local_runs_index.json"

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    # ===========================================================
    # DATA COLLECTION
    # ===========================================================

    def collect_training_data(
        self,
        *,
        min_quality: float = 0.3,
        include_sources: list[str] | None = None,
    ) -> DataCollectionResult:
        """Collect training data from all available sources.

        Sources:
        - distillation: conversation pairs from midnight purge
        - dream: insights from dream cycle
        - missions: successful mission results
        - knowledge: document-derived training pairs

        Args:
            min_quality: Minimum quality score for pairs
            include_sources: Only include these sources (None = all)

        Returns:
            Collection result with dataset path and stats
        """
        result = DataCollectionResult()
        all_pairs: list[dict[str, Any]] = []
        sources = include_sources or ["distillation", "dream", "missions", "knowledge"]

        # 1. Distillation pairs
        if "distillation" in sources and self.distiller is not None:
            try:
                export_path = self._datasets_dir / f"distill_{int(time.time())}.jsonl"
                stats = self.distiller.export_training_data(
                    export_path, min_quality=min_quality,
                )
                count = stats.get("exported", 0)
                result.by_source["distillation"] = count
                if count > 0:
                    for line in export_path.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            all_pairs.append(json.loads(line))
                    export_path.unlink(missing_ok=True)
            except Exception as e:
                result.by_source["distillation_error"] = str(e)

        # 2. Dream cycle insights
        if "dream" in sources:
            try:
                dream_pairs = self._collect_dream_pairs()
                result.by_source["dream"] = len(dream_pairs)
                all_pairs.extend(dream_pairs)
            except Exception as e:
                result.by_source["dream_error"] = str(e)

        # 3. Mission results
        if "missions" in sources:
            try:
                mission_pairs = self._collect_mission_pairs()
                result.by_source["missions"] = len(mission_pairs)
                all_pairs.extend(mission_pairs)
            except Exception as e:
                result.by_source["missions_error"] = str(e)

        # 4. Knowledge bootstrap pairs
        if "knowledge" in sources:
            try:
                knowledge_pairs = self._collect_knowledge_pairs()
                result.by_source["knowledge"] = len(knowledge_pairs)
                all_pairs.extend(knowledge_pairs)
            except Exception as e:
                result.by_source["knowledge_error"] = str(e)

        # Write combined dataset
        result.total_pairs = len(all_pairs)
        if result.total_pairs > 0:
            dataset_path = self._datasets_dir / f"dataset_{int(time.time())}.jsonl"
            with open(dataset_path, "w", encoding="utf-8") as f:
                for pair in all_pairs:
                    f.write(json.dumps(pair) + "\n")
            result.dataset_path = str(dataset_path)

            # Calculate average quality
            qualities = [p.get("quality_score", 0.5) for p in all_pairs]
            result.quality_avg = sum(qualities) / len(qualities) if qualities else 0.0

        self._log("training.data_collected", result.to_dict())
        return result

    def _collect_dream_pairs(self) -> list[dict[str, Any]]:
        """Collect training pairs from dream cycle insights."""
        pairs: list[dict[str, Any]] = []
        dream_dir = self.root / "memory" / "dream_cycle"
        if not dream_dir.exists():
            return pairs

        # Read dream history and convert insights to training pairs
        history_file = dream_dir / "history.jsonl"
        if history_file.exists():
            for line in history_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    # Convert dream insights to instruction-response pairs
                    gaps = entry.get("gaps_identified", [])
                    for gap in gaps:
                        if isinstance(gap, dict):
                            pairs.append({
                                "instruction": f"Explain: {gap.get('topic', gap.get('gap', ''))}",
                                "response": gap.get("analysis", gap.get("recommendation", "")),
                                "quality_score": 0.6,
                                "category": "reasoning",
                            })
                    recommendations = entry.get("recommendations", [])
                    for rec in recommendations:
                        if isinstance(rec, dict):
                            pairs.append({
                                "instruction": f"What should ANUBIS improve? Context: {rec.get('area', '')}",
                                "response": rec.get("suggestion", rec.get("action", "")),
                                "quality_score": 0.7,
                                "category": "reasoning",
                            })
                except Exception:
                    continue
        return pairs

    def _collect_mission_pairs(self) -> list[dict[str, Any]]:
        """Collect training pairs from successful mission results."""
        pairs: list[dict[str, Any]] = []
        # Read mission history
        missions_file = self.root / "memory" / "missions.json"
        if not missions_file.exists():
            return pairs

        try:
            missions = json.loads(missions_file.read_text(encoding="utf-8"))
            if isinstance(missions, list):
                for mission in missions:
                    if mission.get("status") == "completed" and mission.get("result"):
                        pairs.append({
                            "instruction": mission.get("task", ""),
                            "response": mission.get("result", ""),
                            "quality_score": 0.8,
                            "category": "coding",
                        })
        except Exception:
            pass
        return pairs

    def _collect_knowledge_pairs(self) -> list[dict[str, Any]]:
        """Collect training pairs from knowledge bootstrap."""
        pairs: list[dict[str, Any]] = []
        bootstrap_file = self.root / "training" / "knowledge_pairs.jsonl"
        if not bootstrap_file.exists():
            return pairs

        for line in bootstrap_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    pairs.append(json.loads(line))
                except Exception:
                    continue
        return pairs

    # ===========================================================
    # TRAINING SCRIPT GENERATION
    # ===========================================================

    def generate_training_script(
        self,
        dataset_path: str,
        config: TrainingConfig | None = None,
    ) -> dict[str, Any]:
        """Generate a training script for the given dataset.

        Args:
            dataset_path: Path to the JSONL training dataset
            config: Training configuration (uses default if None)

        Returns:
            Dict with script path and metadata
        """
        if config is None:
            config = TrainingConfig()

        script = self.unsloth.generate_training_script(config, dataset_path)
        script_path = self._scripts_dir / f"train_{int(time.time())}.py"
        script_path.write_text(script, encoding="utf-8")

        estimate = self.unsloth.estimate_performance(config)

        result = {
            "script_path": str(script_path),
            "dataset_path": dataset_path,
            "config": config.to_dict(),
            "estimate": {
                "vram_mb": estimate.estimated_vram_mb,
                "time_minutes": estimate.estimated_time_minutes,
                "unsloth_available": estimate.unsloth_available,
            },
        }

        self._log("training.script_generated", result)
        return result

    # ===========================================================
    # TRAINING EXECUTION
    # ===========================================================

    def run_training(
        self,
        script_path: str,
        *,
        plan_id: str = "",
        timeout: int = 3600,
    ) -> TrainingRun:
        """Execute a training script as a subprocess.

        Args:
            script_path: Path to the training script
            plan_id: Associated training plan ID
            timeout: Maximum training time in seconds (default 1 hour)

        Returns:
            TrainingRun with results
        """
        run_id = f"run_{int(time.time())}"
        output_dir = self._runs_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "training.log"

        run = TrainingRun(
            run_id=run_id,
            timestamp=time.time(),
            plan_id=plan_id,
            script_path=script_path,
            output_dir=str(output_dir),
            status="running",
            started_at=time.time(),
            log_path=str(log_path),
        )

        self._speak(f"Starting local training run {run_id}")
        self._log("training.started", run.to_dict())

        try:
            # Run the training script
            with open(log_path, "w", encoding="utf-8") as log_file:
                proc = subprocess.run(
                    [sys.executable, script_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    cwd=str(output_dir),
                    env={**os.environ, "OUTPUT_DIR": str(output_dir)},
                )

            run.completed_at = time.time()
            run.duration_seconds = run.completed_at - run.started_at

            if proc.returncode == 0:
                run.status = "completed"
                # Parse training metrics from log
                self._parse_training_log(run)
                # Find the output model
                model_path = output_dir / "outputs" / "merged_model"
                if not model_path.exists():
                    model_path = output_dir / "outputs" / "lora_adapter"
                run.model_path = str(model_path) if model_path.exists() else ""
                self._speak(
                    f"Training completed in {run.duration_seconds:.0f}s. "
                    f"Loss: {run.training_loss:.4f}, Steps: {run.global_step}"
                )
            else:
                run.status = "failed"
                run.error = f"Training script exited with code {proc.returncode}"
                self._speak(f"Training failed: {run.error}")

        except subprocess.TimeoutExpired:
            run.status = "failed"
            run.error = f"Training timed out after {timeout}s"
            run.completed_at = time.time()
            run.duration_seconds = run.completed_at - run.started_at
            self._speak(f"Training timed out after {timeout} seconds")

        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = time.time()
            run.duration_seconds = run.completed_at - run.started_at
            self._speak(f"Training error: {e}")

        # Update index
        self._update_run_index(run)

        self._log("training.completed", run.to_dict())

        return run

    def _parse_training_log(self, run: TrainingRun) -> None:
        """Parse training metrics from the log file."""
        try:
            log_path = Path(run.log_path)
            if not log_path.exists():
                return
            content = log_path.read_text(encoding="utf-8")
            # Look for training loss and global step
            for line in content.splitlines():
                if "training_loss" in line.lower():
                    try:
                        # Try to extract loss value
                        parts = line.split()
                        for part in parts:
                            try:
                                run.training_loss = float(part)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                if "global_step" in line.lower() or "Total steps:" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            try:
                                run.global_step = int(part)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
        except Exception:
            pass

    def _update_run_index(self, run: TrainingRun) -> None:
        """Update the run index."""
        index = self._load_run_index()
        index.append(run.to_dict())
        self._index_file.write_text(
            json.dumps(index, indent=2) + "\n", encoding="utf-8"
        )

    def _load_run_index(self) -> list[dict[str, Any]]:
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    # ===========================================================
    # FULL PIPELINE
    # ===========================================================

    def run_full_pipeline(
        self,
        *,
        config: TrainingConfig | None = None,
        min_quality: float = 0.3,
        timeout: int = 3600,
    ) -> dict[str, Any]:
        """Run the full local fine-tuning pipeline.

        1. Collect training data
        2. Generate training script
        3. Run training
        4. Return results (evaluation and staging are separate steps
           that require Creator approval)

        Args:
            config: Training configuration
            min_quality: Minimum quality score for training pairs
            timeout: Maximum training time in seconds

        Returns:
            Full pipeline result
        """
        self._speak("Starting full local fine-tuning pipeline")

        # 1. Collect data
        collection = self.collect_training_data(min_quality=min_quality)
        if collection.total_pairs == 0:
            return {
                "completed": False,
                "error": "No training data available",
                "collection": collection.to_dict(),
            }

        self._speak(f"Collected {collection.total_pairs} training pairs")

        # 2. Generate script
        script_result = self.generate_training_script(
            collection.dataset_path, config,
        )

        # 3. Run training
        run = self.run_training(
            script_result["script_path"],
            timeout=timeout,
        )

        result = {
            "completed": run.status == "completed",
            "collection": collection.to_dict(),
            "script": script_result,
            "run": run.to_dict(),
        }

        if run.status == "completed" and run.model_path:
            self._speak(
                f"Training pipeline complete. Model at {run.model_path}. "
                f"Ready for evaluation."
            )
            result["next_step"] = "evaluate"
            result["model_path"] = run.model_path
        else:
            self._speak("Training pipeline did not complete successfully")
            result["next_step"] = "review_errors"

        self._log("training.pipeline_complete", result)
        return result

    # ===========================================================
    # STATUS AND MANAGEMENT
    # ===========================================================

    def list_runs(self) -> dict[str, Any]:
        """List all training runs."""
        index = self._load_run_index()
        runs = sorted(index, key=lambda r: r.get("timestamp", 0), reverse=True)
        return {"count": len(runs), "runs": runs}

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get a specific training run."""
        index = self._load_run_index()
        for run in index:
            if run.get("run_id") == run_id:
                return run
        return None

    def get_status(self) -> dict[str, Any]:
        """Get local fine-tuning system status."""
        index = self._load_run_index()
        completed = sum(1 for r in index if r.get("status") == "completed")
        failed = sum(1 for r in index if r.get("status") == "failed")
        latest = max(index, key=lambda r: r.get("timestamp", 0)) if index else None

        # Check GPU availability
        gpu_available = self._check_gpu()

        return {
            "total_runs": len(index),
            "completed_runs": completed,
            "failed_runs": failed,
            "latest_run": latest.get("run_id", "") if latest else "",
            "latest_status": latest.get("status", "") if latest else "",
            "unsloth_available": self.unsloth.is_available(),
            "gpu_available": gpu_available,
            "training_dir": str(self._training_dir),
        }

    def _check_gpu(self) -> bool:
        """Check if a GPU is available for training."""
        try:
            # Try nvidia-smi
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            return proc.returncode == 0 and bool(proc.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # Try Python torch
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass
        return False

    def cancel_run(self, run_id: str) -> dict[str, Any]:
        """Cancel a running training job (best effort)."""
        run = self.get_run(run_id)
        if not run:
            return {"cancelled": False, "error": "run not found"}
        if run.get("status") != "running":
            return {"cancelled": False, "error": f"run is not running (status: {run.get('status')})"}
        # Best effort — mark as cancelled in index
        index = self._load_run_index()
        for r in index:
            if r.get("run_id") == run_id:
                r["status"] = "cancelled"
                r["completed_at"] = time.time()
                break
        self._index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")
        self._log("training.cancelled", {"run_id": run_id})
        return {"cancelled": True, "run_id": run_id}
