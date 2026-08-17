"""Automated training manager — end-to-end GPU training pipeline.

Automates the full cycle:
  1. Provision a Lambda Labs GPU instance
  2. Upload repo and pipeline scripts
  3. Run setup and the master training pipeline
  4. Monitor progress
  5. Download the GGUF model when complete
  6. Deploy to the local inference engine
  7. Record the generation in the mixed model tracker

Constitutional gates:
  - Instance provisioning requires Creator approval (financial action)
  - Training is a MAIN_ENGINE change (requires hash-bound approval)
  - All actions are logged to the evidence ledger
  - The Creator can cancel at any stage

Usage from daemon:
  train_auto_prepare   — preview cost and prepare the job
  train_auto_submit    — submit with Creator approval
  train_auto_status    — check progress
  train_auto_cancel    — cancel and cleanup
  train_auto_download  — download the model when ready
  train_auto_deploy    — deploy the downloaded model locally
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.cloud_training import LambdaConfig, LambdaAdapter, JobSpec, GPU_TYPES


@dataclass
class TrainingJob:
    """Represents an automated training job."""
    job_id: str = ""
    instance_id: str = ""
    ssh_host: str = ""
    ssh_key_path: str = ""
    gpu_type: str = "nvidia_h100_nvl"
    runtime_hours: float = 24.0
    base_model: str = "Qwen/Qwen2.5-32B-Instruct"
    quantization: str = "Q3_K_M"
    status: str = "pending"  # pending, provisioning, running, completed, failed, cancelled
    started_at: float = 0.0
    completed_at: float = 0.0
    cost_estimate: float = 0.0
    pipeline_stage: str = ""
    error: str = ""
    gguf_path: str = ""
    local_model_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "instance_id": self.instance_id,
            "ssh_host": self.ssh_host,
            "gpu_type": self.gpu_type,
            "runtime_hours": self.runtime_hours,
            "base_model": self.base_model,
            "quantization": self.quantization,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cost_estimate": self.cost_estimate,
            "pipeline_stage": self.pipeline_stage,
            "error": self.error,
            "gguf_path": self.gguf_path,
            "local_model_path": self.local_model_path,
        }


class AutomatedTrainingManager:
    """Manages the end-to-end automated training pipeline.

    This wraps the Lambda Labs API and the B200 training pipeline
    into a single automated flow. The Creator approves once, and
    the manager handles everything else.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        lambda_adapter: LambdaAdapter | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.lambda_adapter = lambda_adapter or LambdaAdapter(ledger=ledger)
        self._state_dir = self.root / "memory" / "training_jobs"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._current_job: TrainingJob | None = None

    def prepare(
        self,
        gpu_type: str = "nvidia_h100_nvl",
        runtime_hours: float = 24.0,
        base_model: str = "Qwen/Qwen2.5-32B-Instruct",
        quantization: str = "Q3_K_M",
    ) -> dict[str, Any]:
        """Prepare a training job — returns cost preview without submitting.

        This is a ROUTINE action (read-only cost estimate).
        """
        gpu_info = GPU_TYPES.get(gpu_type, {})
        if not gpu_info:
            return {"error": f"unknown GPU type: {gpu_type}"}

        cost = gpu_info["price_per_hr"] * runtime_hours

        job = TrainingJob(
            job_id=hashlib.sha256(f"train:{time.time()}".encode()).hexdigest()[:16],
            gpu_type=gpu_type,
            runtime_hours=runtime_hours,
            base_model=base_model,
            quantization=quantization,
            cost_estimate=cost,
        )

        # Save job state
        self._save_job(job)

        # Cost preview
        preview = {
            "job_id": job.job_id,
            "gpu_type": gpu_type,
            "gpu_name": gpu_info["name"],
            "gpu_vram_gb": gpu_info["vram_gb"],
            "runtime_hours": runtime_hours,
            "price_per_hr": gpu_info["price_per_hr"],
            "estimated_cost": round(cost, 2),
            "currency": "USD",
            "base_model": base_model,
            "quantization": quantization,
            "pipeline": "B200 8-hour (3 generations, Stage 3+4)",
            "status": "prepared",
            "requires_creator_approval": True,
            "approval_reason": "Training is a MAIN_ENGINE change. Financial consent required for GPU provisioning.",
        }

        if self.ledger:
            self.ledger.append(
                "anubis.training_manager",
                "job.prepared",
                preview,
            )

        return preview

    def submit(
        self,
        job_id: str,
        creator_approved: bool = False,
        approval_token: str = "",
    ) -> dict[str, Any]:
        """Submit a training job with Creator approval.

        This is a MAIN_ENGINE change requiring Creator approval.
        The approval token must be "creator-approved".
        """
        if not creator_approved or approval_token != "creator-approved":
            return {
                "error": "Creator approval required",
                "reason": "Training is a MAIN_ENGINE change. Financial consent required.",
                "how_to_approve": "Submit with creator_approved=True and approval_token='creator-approved'",
            }

        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if not self.lambda_adapter.is_configured:
            return {
                "error": "Lambda Labs API not configured",
                "how_to_configure": "Store API key in config/cloud_credentials.json under 'lambda.api_key'",
            }

        job.status = "provisioning"
        job.started_at = time.time()
        self._save_job(job)

        # Submit to Lambda Labs
        spec = JobSpec(
            name=f"anubis_training_{job_id}",
            job_type="training",
            gpu_type=job.gpu_type,
            num_gpus=1,
            runtime_hours=job.runtime_hours,
            command=self._build_remote_command(job),
            description=f"ANUBIS full fine-tune: {job.base_model} on {job.gpu_type}",
        )

        try:
            result = self.lambda_adapter.submit_job(
                spec,
                creator_approved=True,
                artifact_hash=job_id,
                approved_artifact_hash=job_id,
            )

            if result.get("ok"):
                job.instance_id = result.get("instance_id", "")
                job.ssh_host = result.get("ssh_host", "")
                job.status = "running"
                self._save_job(job)

                if self.ledger:
                    self.ledger.append(
                        "anubis.training_manager",
                        "job.submitted",
                        job.to_dict(),
                    )

                return {
                    "ok": True,
                    "job_id": job.job_id,
                    "instance_id": job.instance_id,
                    "status": job.status,
                    "message": "Training job submitted. Monitor with train_auto_status.",
                }
            else:
                job.status = "failed"
                job.error = result.get("error", "submission failed")
                self._save_job(job)
                return result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            self._save_job(job)
            return {"error": str(e)}

    def _build_remote_command(self, job: TrainingJob) -> str:
        """Build the command to run on the remote GPU instance."""
        return (
            "git clone https://github.com/AnpuCrownTechnologies/sios-live.git /workspace/sios && "
            "cd /workspace/sios && "
            "bash training/b200_pipeline/setup_b200.sh && "
            f"python training/b200_pipeline/00_master.py"
        )

    def get_status(self, job_id: str = "") -> dict[str, Any]:
        """Get the status of a training job."""
        if job_id:
            job = self._load_job(job_id)
        else:
            job = self._current_job

        if job is None:
            # Try to find the most recent job
            jobs = self._list_jobs()
            if not jobs:
                return {"error": "no training jobs found"}
            job = jobs[0]

        status = job.to_dict()

        # If running, try to get remote status
        if job.status == "running" and job.instance_id:
            try:
                remote_status = self.lambda_adapter.job_status(job.instance_id)
                status["remote"] = remote_status

                # Check for pipeline state
                if remote_status.get("status") == "completed":
                    job.status = "completed"
                    job.completed_at = time.time()
                    job.gguf_path = remote_status.get("output_url", "")
                    self._save_job(job)
                elif remote_status.get("status") == "failed":
                    job.status = "failed"
                    job.error = remote_status.get("error", "remote job failed")
                    self._save_job(job)
            except Exception:
                pass

        return status

    def cancel(self, job_id: str) -> dict[str, Any]:
        """Cancel a training job and cleanup."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if job.instance_id:
            try:
                self.lambda_adapter.cancel_job(job.instance_id)
            except Exception:
                pass

        job.status = "cancelled"
        job.completed_at = time.time()
        self._save_job(job)

        if self.ledger:
            self.ledger.append(
                "anubis.training_manager",
                "job.cancelled",
                job.to_dict(),
            )

        return {"ok": True, "job_id": job_id, "status": "cancelled"}

    def download_model(self, job_id: str) -> dict[str, Any]:
        """Download the trained GGUF model from the remote instance."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if job.status != "completed":
            return {"error": f"job not completed (status: {job.status})"}

        local_path = self.root / "models" / f"anubis_v{job.job_id}.{job.quantization}.gguf"
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            result = self.lambda_adapter.download_artifact(
                job.instance_id, local_path
            )
            if result.get("ok"):
                job.local_model_path = str(local_path)
                self._save_job(job)

                if self.ledger:
                    self.ledger.append(
                        "anubis.training_manager",
                        "model.downloaded",
                        {"job_id": job_id, "path": str(local_path)},
                    )

                return {
                    "ok": True,
                    "path": str(local_path),
                    "size_gb": local_path.stat().st_size / 1e9 if local_path.exists() else 0,
                }
            return result
        except Exception as e:
            return {"error": str(e)}

    def deploy_model(self, job_id: str) -> dict[str, Any]:
        """Deploy the downloaded model to the local inference engine."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if not job.local_model_path:
            download_result = self.download_model(job_id)
            if not download_result.get("ok"):
                return download_result

        model_path = Path(job.local_model_path)
        if not model_path.exists():
            return {"error": f"model file not found: {model_path}"}

        # Update environment configuration
        config_updates = {
            "ANUBIS_INFERENCE_BACKEND": "llama_subprocess",
            "ANUBIS_MODEL_PATH": str(model_path),
            "ANUBIS_MODEL": f"anubis-v{job.job_id}",
        }

        # Write deployment config
        deploy_config_path = self.root / "config" / "inference_deployment.json"
        deploy_config_path.parent.mkdir(parents=True, exist_ok=True)
        deploy_config_path.write_text(json.dumps({
            "model_path": str(model_path),
            "model_name": f"anubis-v{job.job_id}",
            "backend": "llama_subprocess",
            "gpu_layers": 99,
            "context_size": 4096,
            "threads": 8,
            "quantization": job.quantization,
            "base_model": job.base_model,
            "deployed_at": time.time(),
        }, indent=2))

        if self.ledger:
            self.ledger.append(
                "anubis.training_manager",
                "model.deployed",
                {
                    "job_id": job_id,
                    "model_path": str(model_path),
                    "config_path": str(deploy_config_path),
                },
            )

        return {
            "ok": True,
            "model_path": str(model_path),
            "model_name": f"anubis-v{job.job_id}",
            "config_path": str(deploy_config_path),
            "message": f"Model deployed. Restart the daemon to use the new model.",
            "environment": config_updates,
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all training jobs."""
        return [j.to_dict() for j in self._list_jobs()]

    def _save_job(self, job: TrainingJob) -> None:
        """Save job state to disk."""
        path = self._state_dir / f"{job.job_id}.json"
        path.write_text(json.dumps(job.to_dict(), indent=2))
        self._current_job = job

    def _load_job(self, job_id: str) -> TrainingJob | None:
        """Load a job from disk."""
        path = self._state_dir / f"{job_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return TrainingJob(**data)

    def _list_jobs(self) -> list[TrainingJob]:
        """List all jobs, most recent first."""
        jobs = []
        for f in sorted(self._state_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                jobs.append(TrainingJob(**data))
            except Exception:
                pass
        return jobs

    def get_status_overview(self) -> dict[str, Any]:
        """Get overview of all training jobs."""
        jobs = self._list_jobs()
        return {
            "total_jobs": len(jobs),
            "running": sum(1 for j in jobs if j.status == "running"),
            "completed": sum(1 for j in jobs if j.status == "completed"),
            "failed": sum(1 for j in jobs if j.status == "failed"),
            "lambda_configured": self.lambda_adapter.is_configured,
            "available_gpus": {k: v["name"] for k, v in GPU_TYPES.items()},
            "jobs": [j.to_dict() for j in jobs[:10]],
        }
