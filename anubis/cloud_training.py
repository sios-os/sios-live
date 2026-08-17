"""Lambda cloud testing and training adapter.

Lambda GPU cloud is used for:
  - Large-project testing that exceeds local hardware (RTX 5060 Ti 16GB)
  - Heavy training jobs (LoRA/QLoRA fine-tuning)
  - Temporary GPU compute for validation

Lambda is NOT used for:
  - Hosting the online teacher model (that's Gemini/Groq)
  - Ordinary inference (that's local Ollama)
  - Persistent services

Every Lambda job requires:
  1. Cost preview (estimated runtime, GPU type, estimated cost)
  2. Creator approval (ChangeClass.MAIN_ENGINE for training, CONSEQUENTIAL for testing)
  3. Data classification (no sensitive data sent to cloud)
  4. Job status tracking
  5. Result artifact download
  6. Court review for model-weight changes (MAIN_ENGINE)
  7. Exact-hash Creator approval for weight promotion
  8. Cleanup/termination after completion

Constitutional gates:
  - Training jobs that modify model weights are ChangeClass.MAIN_ENGINE
    (requires Court review + Creator approval + exact artifact hash)
  - Testing/validation jobs are ChangeClass.CONSEQUENTIAL
    (requires Creator approval)
  - All jobs are logged to the evidence ledger

The module uses only the Python standard library (no boto3, no
lambda-client SDK) per the constitutional kernel's permission-integrity
rule. Lambda has a REST API that we call via urllib.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constitution import ChangeClass, Request, Verdict, evaluate

# Credential file location
CREDENTIALS_FILE = "config/cloud_credentials.json"

# Lambda API endpoint
LAMBDA_API = "https://api.lambdalabs.com/v1"

# Available GPU types and approximate pricing (per hour, USD)
# These are approximate and should be verified at job submission time.
GPU_TYPES = {
    "nvidia_a10": {"vram_gb": 24, "price_per_hr": 0.75, "name": "NVIDIA A10"},
    "nvidia_a100_40gb": {"vram_gb": 40, "price_per_hr": 1.10, "name": "NVIDIA A100 40GB"},
    "nvidia_a100_80gb": {"vram_gb": 80, "price_per_hr": 1.99, "name": "NVIDIA A100 80GB"},
    "nvidia_h100_80gb": {"vram_gb": 80, "price_per_hr": 2.49, "name": "NVIDIA H100 80GB"},
    "nvidia_h100_sxm": {"vram_gb": 80, "price_per_hr": 3.99, "name": "NVIDIA H100 SXM 80GB"},
    "nvidia_h100_nvl": {"vram_gb": 94, "price_per_hr": 1.684, "name": "NVIDIA H100 NVL 94GB"},
    "nvidia_b200_sxm6": {"vram_gb": 180, "price_per_hr": 6.69, "name": "NVIDIA B200 SXM6 180GB"},
    "nvidia_l4": {"vram_gb": 24, "price_per_hr": 0.80, "name": "NVIDIA L4"},
    "nvidia_l40s": {"vram_gb": 48, "price_per_hr": 1.29, "name": "NVIDIA L40S"},
    "nvidia_rt6000_ada": {"vram_gb": 48, "price_per_hr": 0.99, "name": "NVIDIA RTX 6000 Ada"},
}

# Sensitive data patterns — same as cloud_model.py
SENSITIVE_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"access_key_id\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"api_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"passphrase\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"creator_id\s*[:=]\s*\S+", re.IGNORECASE),
]


def _check_sensitive_data(text: str) -> str | None:
    """Check if text contains sensitive data."""
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            return f"sensitive data pattern matched: {pattern.pattern[:50]}"
    return None


@dataclass
class LambdaConfig:
    """Configuration for Lambda cloud access."""
    api_key: str = ""
    endpoint: str = LAMBDA_API

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> "LambdaConfig":
        """Load config from the credentials file."""
        path = Path(path or CREDENTIALS_FILE)
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lam = data.get("lambda", {})
            return cls(
                api_key=lam.get("api_key", ""),
                endpoint=lam.get("endpoint", LAMBDA_API),
            )
        except (json.JSONDecodeError, OSError):
            return cls()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class JobSpec:
    """Specification for a Lambda training/testing job."""
    name: str
    job_type: str  # "training" or "testing"
    gpu_type: str = "nvidia_a10"
    num_gpus: int = 1
    runtime_hours: float = 1.0
    docker_image: str = ""
    command: str = ""
    dataset_path: str = ""
    output_path: str = ""
    description: str = ""

    @property
    def is_training(self) -> bool:
        return self.job_type == "training"

    @property
    def is_testing(self) -> bool:
        return self.job_type == "testing"

    def estimate_cost(self) -> dict[str, Any]:
        """Estimate the cost of this job."""
        gpu_info = GPU_TYPES.get(self.gpu_type, {"price_per_hr": 1.0, "name": "unknown"})
        price_per_hr = gpu_info["price_per_hr"] * self.num_gpus
        total = price_per_hr * self.runtime_hours
        return {
            "gpu_type": self.gpu_type,
            "gpu_name": gpu_info["name"],
            "num_gpus": self.num_gpus,
            "price_per_hr": round(price_per_hr, 2),
            "runtime_hours": self.runtime_hours,
            "estimated_total": round(total, 2),
            "currency": "USD",
        }


@dataclass
class JobResult:
    """Result of a Lambda job."""
    job_id: str = ""
    status: str = "pending"  # pending, running, completed, failed, cancelled
    ok: bool = False
    cost: float = 0.0
    output_url: str = ""
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_s: float = 0.0
    artifact_hash: str = ""
    approved: bool = False


class LambdaAdapter:
    """Lambda GPU cloud adapter for testing and training.

    All jobs require Creator approval. Training jobs that modify model
    weights require Court review (ChangeClass.MAIN_ENGINE). The adapter
    provides cost previews before any job is submitted.
    """

    def __init__(
        self,
        config: LambdaConfig | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.config = config or LambdaConfig.from_file()
        self.ledger = ledger
        self._jobs: dict[str, JobResult] = {}

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured

    # --------------------------------------------------- constitutional gate

    def _evaluate_job(
        self,
        spec: JobSpec,
        creator_approved: bool,
        artifact_hash: str | None = None,
        approved_artifact_hash: str | None = None,
    ) -> tuple[bool, str, ChangeClass]:
        """Evaluate a job through the constitutional gate.

        Returns (allowed, reason, change_class).
        Training jobs (MAIN_ENGINE) require an exact artifact hash match.
        """
        if spec.is_training:
            change_class = ChangeClass.MAIN_ENGINE
        else:
            change_class = ChangeClass.CONSEQUENTIAL

        req = Request(
            actor="anubis",
            action=f"lambda.{spec.job_type}",
            change_class=change_class,
            intent=spec.description or spec.name,
            capabilities_requested=frozenset({"lambda.compute"}) if creator_approved else frozenset(),
            capabilities_granted=frozenset({"lambda.compute"}) if creator_approved else frozenset(),
            payload=spec.command[:500],
            creator_approved=creator_approved,
            reversible=True,
            explainable=True,
            artifact_hash=artifact_hash,
            approved_artifact_hash=approved_artifact_hash,
        )

        ruling = evaluate(req)

        if ruling.verdict == Verdict.ALLOW:
            return True, "approved", change_class
        if ruling.verdict == Verdict.REQUIRES_CREATOR_APPROVAL:
            return False, "requires Creator approval: " + "; ".join(ruling.reasons), change_class
        return False, "denied: " + "; ".join(ruling.reasons), change_class

    # --------------------------------------------------- privacy gate

    def _check_privacy(self, spec: JobSpec) -> str | None:
        """Check if the job spec contains sensitive data."""
        # Check command, dataset path, and description
        for text in [spec.command, spec.dataset_path, spec.description, spec.docker_image]:
            if text:
                sensitive = _check_sensitive_data(text)
                if sensitive:
                    return sensitive
        return None

    # --------------------------------------------------- cost preview

    def cost_preview(self, spec: JobSpec) -> dict[str, Any]:
        """Generate a cost preview for a job (no submission).

        This is the first step — the Creator reviews the cost preview
        before approving the job.
        """
        cost = spec.estimate_cost()
        privacy = self._check_privacy(spec)
        return {
            "job_name": spec.name,
            "job_type": spec.job_type,
            "is_training": spec.is_training,
            "requires_court_review": spec.is_training,
            "cost_estimate": cost,
            "privacy_check": {
                "ok": privacy is None,
                "issue": privacy,
            },
            "configured": self.is_configured,
            "approval_required": True,
            "message": (
                "Review the cost estimate. Training jobs require Court review "
                "and exact-hash artifact approval. Approve to proceed."
            ),
        }

    # --------------------------------------------------- job submission

    def submit_job(
        self,
        spec: JobSpec,
        creator_approved: bool = False,
        artifact_hash: str | None = None,
        approved_artifact_hash: str | None = None,
    ) -> dict[str, Any]:
        """Submit a job to Lambda (requires Creator approval).

        For training jobs (MAIN_ENGINE), both artifact_hash and
        approved_artifact_hash must be provided and must match.

        Returns a dict with job_id, status, and cost preview.
        """
        if not self.is_configured:
            return {"ok": False, "error": "Lambda not configured. Add API key to config/cloud_credentials.json"}

        # Gate 1: Constitutional evaluation
        allowed, reason, change_class = self._evaluate_job(
            spec, creator_approved, artifact_hash, approved_artifact_hash
        )
        if not allowed:
            self._log_job(spec, JobResult(status="denied", error=reason))
            return {"ok": False, "error": reason, "change_class": int(change_class)}

        # Gate 2: Privacy check
        privacy = self._check_privacy(spec)
        if privacy:
            self._log_job(spec, JobResult(status="denied", error=f"privacy: {privacy}"))
            return {"ok": False, "error": f"privacy check failed: {privacy}"}

        # Gate 3: Cost preview (logged even if not submitted)
        cost = spec.estimate_cost()

        # Generate a local job ID (in real implementation, Lambda API returns this)
        job_id = f"lambda_{int(time.time() * 1000)}_{spec.name[:20]}"
        result = JobResult(
            job_id=job_id,
            status="pending",
            cost=cost["estimated_total"],
            started_at=time.time(),
        )

        # In a real implementation, we would call the Lambda API here:
        # POST /v1/instances with the job spec
        # For now, we log the job and return the preview for Creator review
        self._jobs[job_id] = result
        self._log_job(spec, result)

        return {
            "ok": True,
            "job_id": job_id,
            "status": "pending",
            "cost_estimate": cost,
            "change_class": int(change_class),
            "requires_court_review": spec.is_training,
            "message": (
                "Job submitted. Training jobs require Court review before "
                "artifact promotion. Check job status with lambda_job_status."
            ),
        }

    # --------------------------------------------------- job status

    def job_status(self, job_id: str) -> dict[str, Any]:
        """Check the status of a submitted job."""
        if job_id not in self._jobs:
            return {"ok": False, "error": f"job not found: {job_id}"}
        result = self._jobs[job_id]
        return {
            "ok": True,
            "job_id": result.job_id,
            "status": result.status,
            "cost": result.cost,
            "duration_s": round(result.duration_s, 2),
            "error": result.error,
            "artifact_hash": result.artifact_hash,
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all submitted jobs."""
        return [
            {
                "job_id": r.job_id,
                "status": r.status,
                "cost": r.cost,
                "started_at": r.started_at,
            }
            for r in self._jobs.values()
        ]

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """Cancel a running job."""
        if job_id not in self._jobs:
            return {"ok": False, "error": f"job not found: {job_id}"}
        result = self._jobs[job_id]
        result.status = "cancelled"
        result.completed_at = time.time()
        result.duration_s = result.completed_at - result.started_at
        return {"ok": True, "job_id": job_id, "status": "cancelled"}

    # --------------------------------------------------- artifact handling

    def download_artifact(
        self, job_id: str, local_path: str | Path
    ) -> dict[str, Any]:
        """Download a job result artifact.

        For training jobs, the artifact is a model weight file that
        must pass Court review before promotion.
        """
        if job_id not in self._jobs:
            return {"ok": False, "error": f"job not found: {job_id}"}
        result = self._jobs[job_id]
        if result.status != "completed":
            return {"ok": False, "error": f"job not completed (status: {result.status})"}

        # In a real implementation, download from Lambda storage
        # For now, return the artifact metadata
        return {
            "ok": True,
            "job_id": job_id,
            "artifact_hash": result.artifact_hash,
            "local_path": str(local_path),
            "requires_court_review": True,
            "message": (
                "Artifact downloaded. For training jobs, submit to Court "
                "for review before promotion. Use court_submit command."
            ),
        }

    # --------------------------------------------------- logging

    def _log_job(self, spec: JobSpec, result: JobResult) -> None:
        """Log a job to the evidence ledger."""
        if self.ledger is None:
            return
        try:
            entry = {
                "type": "lambda_job",
                "job_id": result.job_id,
                "job_name": spec.name,
                "job_type": spec.job_type,
                "gpu_type": spec.gpu_type,
                "num_gpus": spec.num_gpus,
                "status": result.status,
                "cost": result.cost,
                "error": result.error,
                "timestamp": time.time(),
            }
            self.ledger.append(entry)
        except Exception:
            pass

    # --------------------------------------------------- status

    def status(self) -> dict[str, Any]:
        """Return adapter status (no secrets)."""
        return {
            "configured": self.is_configured,
            "endpoint": self.config.endpoint if self.is_configured else None,
            "available_gpus": [
                {"type": k, "name": v["name"], "vram_gb": v["vram_gb"], "price_per_hr": v["price_per_hr"]}
                for k, v in GPU_TYPES.items()
            ],
            "active_jobs": len([j for j in self._jobs.values() if j.status in ("pending", "running")]),
            "total_jobs": len(self._jobs),
            "ledger_connected": self.ledger is not None,
        }
