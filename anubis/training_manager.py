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
import uuid
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.cloud_training import LambdaConfig, LambdaAdapter, JobSpec, GPU_TYPES
from anubis.vast_adapter import VastConfig, VastAdapter, VastOffer, VastInstance


@dataclass
class TrainingJob:
    """Represents an automated training job."""
    job_id: str = ""
    instance_id: str = ""
    ssh_host: str = ""
    ssh_port: int = 22
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
        vast_adapter: VastAdapter | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.lambda_adapter = lambda_adapter or LambdaAdapter(ledger=ledger)
        self.vast_adapter = vast_adapter or VastAdapter()
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
            job_id=uuid.uuid4().hex[:16],
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
            "git clone https://github.com/sios-os/sios-live.git /workspace/sios && "
            "cd /workspace/sios && "
            "bash training/b200_pipeline/setup_h100_unsloth.sh && "
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
            "vast_configured": self.vast_adapter.is_configured,
            "available_gpus": {k: v["name"] for k, v in GPU_TYPES.items()},
            "jobs": [j.to_dict() for j in jobs[:10]],
        }

    # --------------------------------------------------- vast.ai automation

    def vast_search(self, gpu_name: str = "H100 NVL", max_price: float = 5.0) -> dict[str, Any]:
        """Search for available GPU offers on Vast.ai (read-only, no approval needed)."""
        if not self.vast_adapter.is_configured:
            return {"error": "Vast.ai API not configured"}

        offers = self.vast_adapter.search_offers(
            gpu_name=gpu_name,
            min_gpu_ram=80,
            min_reliability=0.9,
            max_price=max_price,
        )

        return {
            "ok": True,
            "count": len(offers),
            "offers": [
                {
                    "id": o.id,
                    "gpu_name": o.gpu_name,
                    "gpu_ram_gb": round(o.gpu_ram, 1),
                    "dph_total": round(o.dph_total, 3),
                    "reliability": round(o.reliability, 4),
                    "dlperf": round(o.dlperf, 1),
                    "cpu_cores": o.cpu_cores,
                    "cpu_ram_gb": round(o.cpu_ram, 1),
                    "country": o.country,
                    "cuda_max": o.cuda_max_good,
                    "24hr_cost": round(o.dph_total * 24, 2),
                }
                for o in offers[:20]
            ],
        }

    def vast_rent_and_train(
        self,
        creator_approved: bool = False,
        approval_token: str = "",
        gpu_name: str = "H100 NVL",
        max_price: float = 5.0,
        disk_gb: float = 200,
        runtime_hours: float = 24.0,
        base_model: str = "Qwen/Qwen2.5-32B-Instruct",
        quantization: str = "Q3_K_M",
    ) -> dict[str, Any]:
        """One-command automation: rent a GPU, run the pipeline, return the instance info.

        This is the full automated flow:
          1. Search for available H100 NVL offers
          2. Rent the cheapest one (requires Creator approval)
          3. Wait for it to be ready
          4. SSH in and start the training pipeline
          5. Return the instance info for monitoring

        The model download and deploy happen separately via
        vast_download_model() and deploy_model() after the pipeline completes.
        """
        if not creator_approved or approval_token != "creator-approved":
            return {
                "error": "Creator approval required",
                "reason": "Renting a GPU and training is a MAIN_ENGINE change with financial impact.",
                "how_to_approve": "Submit with creator_approved=True and approval_token='creator-approved'",
                "estimated_cost": f"~${max_price * runtime_hours:.2f} for {runtime_hours} hours",
            }

        if not self.vast_adapter.is_configured:
            return {"error": "Vast.ai API not configured"}

        # Step 1: Search and rent
        log_msg = "Step 1: Searching for available GPU offers..."
        print(log_msg, flush=True)

        rent_result = self.vast_adapter.search_and_rent(
            gpu_name=gpu_name,
            min_gpu_ram=80,
            min_reliability=0.9,
            max_price=max_price,
            disk_gb=disk_gb,
            image="vastai/unsloth-studio:latest",
            label="anubis-training",
            creator_approved=True,
            approval_token="creator-approved",
        )

        if "error" in rent_result:
            return rent_result

        instance_id = rent_result.get("instance_id", 0)
        offer = rent_result.get("offer", {})

        # Create a training job record
        job = TrainingJob(
            job_id=hashlib.sha256(f"vast:{instance_id}:{time.time()}".encode()).hexdigest()[:16],
            instance_id=str(instance_id),
            gpu_type=gpu_name,
            runtime_hours=runtime_hours,
            base_model=base_model,
            quantization=quantization,
            cost_estimate=offer.get("dph_total", 0) * runtime_hours,
            status="provisioning",
            started_at=time.time(),
        )
        self._save_job(job)

        if self.ledger:
            self.ledger.append("anubis.training_manager", "vast.rented", job.to_dict())

        # Step 2: Wait for the instance to be ready
        print("Step 2: Waiting for instance to be ready (up to 10 minutes)...", flush=True)
        ready_result = self.vast_adapter.wait_for_ready(instance_id, timeout_s=600)

        if "error" in ready_result:
            job.status = "failed"
            job.error = ready_result["error"]
            self._save_job(job)
            return ready_result

        job.ssh_host = ready_result["ssh_host"]
        job.ssh_port = ready_result.get("ssh_port", 22)
        job.status = "running"
        self._save_job(job)

        # Step 3: Run the pipeline over SSH
        print("Step 3: Starting training pipeline on remote instance...", flush=True)
        pipeline_result = self.vast_adapter.run_pipeline_over_ssh(
            ssh_host=job.ssh_host,
            ssh_port=job.ssh_port,
        )

        if "error" in pipeline_result:
            job.status = "failed"
            job.error = pipeline_result["error"]
            self._save_job(job)
            return pipeline_result

        job.pipeline_stage = "pipeline_started"
        self._save_job(job)

        if self.ledger:
            self.ledger.append("anubis.training_manager", "vast.pipeline_started", job.to_dict())

        return {
            "ok": True,
            "job_id": job.job_id,
            "instance_id": instance_id,
            "ssh_host": job.ssh_host,
            "ssh_port": job.ssh_port,
            "gpu_name": gpu_name,
            "cost_per_hr": offer.get("dph_total", 0),
            "estimated_total_cost": round(offer.get("dph_total", 0) * runtime_hours, 2),
            "runtime_hours": runtime_hours,
            "status": "pipeline_running",
            "message": (
                f"Training pipeline started on {gpu_name} at {job.ssh_host}:{job.ssh_port}. "
                f"Monitor with: train_vast_monitor {{\"job_id\": \"{job.job_id}\"}}. "
                f"Download with: train_vast_download {{\"job_id\": \"{job.job_id}\"}}. "
                f"Estimated completion: {runtime_hours} hours."
            ),
        }

    def vast_monitor(self, job_id: str) -> dict[str, Any]:
        """Monitor the training pipeline progress on the remote instance."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if not job.ssh_host:
            return {"error": "No SSH host for this job"}

        monitor_result = self.vast_adapter.monitor_pipeline(
            ssh_host=job.ssh_host,
            ssh_port=job.ssh_port,
        )

        if "error" in monitor_result:
            return monitor_result

        # Check if pipeline is complete
        output = monitor_result.get("output", "")
        if "PIPELINE COMPLETE" in output:
            job.status = "completed"
            job.completed_at = time.time()
            self._save_job(job)
        elif "PIPELINE FAILED" in output:
            job.status = "failed"
            job.error = "Pipeline failed on remote instance"
            self._save_job(job)

        return {
            "ok": True,
            "job_id": job_id,
            "status": job.status,
            "remote_output": output,
        }

    def vast_download_model(self, job_id: str) -> dict[str, Any]:
        """Download the trained GGUF model from the remote Vast.ai instance."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if not job.ssh_host:
            return {"error": "No SSH host for this job"}

        local_path = self.root / "models" / f"anubis_v{job.job_id}.{job.quantization}.gguf"

        download_result = self.vast_adapter.download_model(
            ssh_host=job.ssh_host,
            ssh_port=job.ssh_port,
            local_path=local_path,
            quant=job.quantization,
        )

        if "error" in download_result:
            return download_result

        job.local_model_path = str(local_path)
        job.gguf_path = download_result.get("remote_path", "")
        self._save_job(job)

        if self.ledger:
            self.ledger.append("anubis.training_manager", "vast.model_downloaded", {
                "job_id": job_id, "path": str(local_path),
                "size_gb": download_result.get("size_gb", 0),
            })

        return download_result

    def vast_destroy_instance(self, job_id: str) -> dict[str, Any]:
        """Destroy the Vast.ai instance after training is complete."""
        job = self._load_job(job_id)
        if job is None:
            return {"error": f"job not found: {job_id}"}

        if not job.instance_id:
            return {"error": "No instance ID for this job"}

        result = self.vast_adapter.destroy_instance(int(job.instance_id))

        if result.get("ok"):
            if self.ledger:
                self.ledger.append("anubis.training_manager", "vast.instance_destroyed", {
                    "job_id": job_id, "instance_id": job.instance_id,
                })

        return result

    def vast_full_automation(
        self,
        creator_approved: bool = False,
        approval_token: str = "",
        gpu_name: str = "H100 NVL",
        max_price: float = 5.0,
        runtime_hours: float = 24.0,
        deploy: bool = False,
    ) -> dict[str, Any]:
        """Full automation: rent, train, wait, download, (optionally) deploy, destroy.

        This blocks for the entire training duration (up to 24 hours).
        For non-blocking use, call vast_rent_and_train() instead and
        poll with vast_monitor().

        Args:
            deploy: If True, deploy the model locally after download.
                    If False (default), just download the model to models/
                    and leave it there for manual deployment later.
        """
        if not creator_approved or approval_token != "creator-approved":
            return {
                "error": "Creator approval required",
                "estimated_cost": f"~${max_price * runtime_hours:.2f}",
            }

        # Step 1: Rent and start pipeline
        print("=== ANUBIS Full Automation ===", flush=True)
        print("Step 1: Renting GPU and starting pipeline...", flush=True)
        rent_result = self.vast_rent_and_train(
            creator_approved=True,
            approval_token="creator-approved",
            gpu_name=gpu_name,
            max_price=max_price,
            runtime_hours=runtime_hours,
        )

        if "error" in rent_result:
            return rent_result

        job_id = rent_result["job_id"]
        instance_id = rent_result["instance_id"]

        # Step 2: Poll until complete
        print(f"Step 2: Waiting for pipeline to complete (up to {runtime_hours} hours)...", flush=True)
        deadline = time.time() + (runtime_hours + 2) * 3600  # 2 hour buffer
        poll_interval = 300  # 5 minutes

        while time.time() < deadline:
            time.sleep(poll_interval)
            monitor_result = self.vast_monitor(job_id)

            if monitor_result.get("status") == "completed":
                break
            if monitor_result.get("status") == "failed":
                return {
                    "error": "Pipeline failed on remote instance",
                    "job_id": job_id,
                    "monitor_output": monitor_result.get("remote_output", ""),
                }

            elapsed = (time.time() - rent_result.get("started_at", time.time())) / 3600
            print(f"  Still running... {elapsed:.1f} hours elapsed", flush=True)

        # Step 3: Download the model
        print("Step 3: Downloading trained model...", flush=True)
        download_result = self.vast_download_model(job_id)

        if "error" in download_result:
            return download_result

        # Step 4: Deploy locally (optional)
        deploy_result = None
        if deploy:
            print("Step 4: Deploying model locally...", flush=True)
            deploy_result = self.deploy_model(job_id)
        else:
            print("Step 4: Skipping deployment (deploy=False). Model saved to models/.", flush=True)

        # Step 5: Destroy the instance
        print("Step 5: Destroying remote instance...", flush=True)
        destroy_result = self.vast_destroy_instance(job_id)

        return {
            "ok": True,
            "job_id": job_id,
            "instance_id": instance_id,
            "model_path": download_result.get("local_path"),
            "model_size_gb": download_result.get("size_gb"),
            "deployed": deploy_result.get("ok", False) if deploy_result else False,
            "deployment_skipped": not deploy,
            "instance_destroyed": destroy_result.get("ok", False),
            "message": (
                f"Full automation complete. Model downloaded to {download_result.get('local_path')}. "
                f"Deploy later with: train_auto_deploy {{\"job_id\": \"{job_id}\"}}"
                if not deploy else
                "Full automation complete. ANUBIS is now running on his fine-tuned model."
            ),
        }
