"""Vast.ai cloud GPU adapter for automated training.

Uses the Vast.ai REST API to:
  - Search for available GPU instances
  - Rent an instance with the Unsloth Studio template
  - Wait for it to become ready
  - SSH in and run the training pipeline
  - Monitor progress
  - Download the trained model
  - Destroy the instance when done

All actions require Creator approval (financial consent).
"""
from __future__ import annotations

import json
import time
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VAST_API = "https://console.vast.ai/api/v0"


@dataclass
class VastConfig:
    """Configuration for Vast.ai access."""
    api_key: str = ""
    endpoint: str = VAST_API

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> "VastConfig":
        path = Path(path or Path(__file__).resolve().parent.parent / "config" / "cloud_credentials.json")
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            vast = data.get("vast", {})
            return cls(
                api_key=vast.get("api_key", ""),
                endpoint=vast.get("endpoint", VAST_API),
            )
        except (json.JSONDecodeError, OSError):
            return cls()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class VastOffer:
    """A GPU rental offer from Vast.ai."""
    id: int
    gpu_name: str = ""
    gpu_ram: float = 0  # GB
    num_gpus: int = 1
    dph_total: float = 0.0  # $/hr
    reliability: float = 0.0
    dlperf: float = 0.0
    cpu_cores: int = 0
    cpu_ram: float = 0  # GB
    disk_space: float = 0  # GB
    inet_down: float = 0  # Mbps
    country: str = ""
    direct_port_count: int = 0
    cuda_max_good: str = ""


@dataclass
class VastInstance:
    """A rented Vast.ai instance."""
    id: int = 0
    label: str = ""
    machine_id: int = 0
    gpu_name: str = ""
    num_gpus: int = 1
    gpu_ram: float = 0
    dph_total: float = 0.0
    status: str = ""  # provisioning, running, exited, loading
    image: str = ""
    ssh_host: str = ""
    ssh_port: int = 0
    ports: dict = field(default_factory=dict)
    cur_state: str = ""
    host_id: int = 0
    rentable: bool = False


class VastAdapter:
    """Vast.ai cloud GPU adapter.

    All rental actions require Creator approval (financial consent).
    """

    def __init__(self, config: VastConfig | None = None) -> None:
        self.config = config or VastConfig.from_file()

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured

    def _api_request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Make an authenticated API request to Vast.ai."""
        url = f"{self.config.endpoint}{path}"
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return {"error": f"HTTP {e.code}: {error_body}"}
        except urllib.error.URLError as e:
            return {"error": f"URL error: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def search_offers(
        self,
        gpu_name: str = "H100 NVL",
        min_gpu_ram: float = 80,
        min_reliability: float = 0.9,
        max_price: float = 5.0,
        num_gpus: int = 1,
    ) -> list[VastOffer]:
        """Search for available GPU offers on Vast.ai."""
        query = {
            "verified": {"eq": True},
            "external": {"eq": False},
            "rentable": {"eq": True},
            "num_gpus": {"ge": num_gpus},
            "gpu_ram": {"ge": min_gpu_ram * 1024},
            "reliability": {"ge": min_reliability},
            "dph_total": {"le": max_price},
            "gpu_name": {"eq": gpu_name},
        }

        result = self._api_request("PUT", "/bundles/", {"query": query, "sort": {"dph_total": "asc"}})

        if "error" in result:
            return []

        offers = result.get("offers", [])
        parsed = []
        for off in offers:
            try:
                parsed.append(VastOffer(
                    id=off.get("id", 0),
                    gpu_name=off.get("gpu_name", ""),
                    gpu_ram=off.get("gpu_ram", 0) / 1024,
                    num_gpus=off.get("num_gpus", 1),
                    dph_total=off.get("dph_total", 0),
                    reliability=off.get("reliability", 0),
                    dlperf=off.get("dlperf", 0),
                    cpu_cores=off.get("cpu_cores", 0),
                    cpu_ram=off.get("cpu_ram", 0) / 1024,
                    disk_space=off.get("disk_space", 0),
                    inet_down=off.get("inet_down", 0),
                    country=off.get("geolocation", {}).get("country", ""),
                    direct_port_count=off.get("direct_port_count", 0),
                    cuda_max_good=off.get("cuda_max_good", ""),
                ))
            except Exception:
                continue

        return parsed

    def list_instances(self) -> list[VastInstance]:
        """List all rented instances."""
        result = self._api_request("GET", "/instances/")

        if "error" in result:
            return []

        instances = result.get("instances", [])
        parsed = []
        for inst in instances:
            try:
                ssh_host = ""
                ssh_port = 0
                ports = inst.get("ports", {})
                for port_key, port_info in ports.items():
                    if "22" in port_key:
                        ssh_host = port_info[0].get("host", "")
                        ssh_port = port_info[0].get("port", 0)

                parsed.append(VastInstance(
                    id=inst.get("id", 0),
                    label=inst.get("label", ""),
                    machine_id=inst.get("machine_id", 0),
                    gpu_name=inst.get("gpu_name", ""),
                    num_gpus=inst.get("num_gpus", 1),
                    gpu_ram=inst.get("gpu_ram", 0) / 1024 if inst.get("gpu_ram") else 0,
                    dph_total=inst.get("dph_total", 0),
                    status=inst.get("actual_status", ""),
                    image=inst.get("image_uuid", ""),
                    ssh_host=ssh_host,
                    ssh_port=ssh_port,
                    ports=ports,
                    cur_state=inst.get("cur_state", ""),
                    host_id=inst.get("host_id", 0),
                    rentable=inst.get("rentable", False),
                ))
            except Exception:
                continue

        return parsed

    def rent_instance(
        self,
        offer_id: int,
        image: str = "vastai/unsloth-studio:latest",
        disk_gb: float = 200,
        label: str = "anubis-training",
        on_start: str = "",
        creator_approved: bool = False,
        approval_token: str = "",
    ) -> dict:
        """Rent a GPU instance. Requires Creator approval."""
        if not creator_approved or approval_token != "creator-approved":
            return {
                "error": "Creator approval required",
                "reason": "Renting a GPU instance is a financial action. Financial consent law applies.",
                "how_to_approve": "Submit with creator_approved=True and approval_token='creator-approved'",
            }

        if not self.is_configured:
            return {"error": "Vast.ai API not configured"}

        data = {
            "client_id": "me",
            "bundle": offer_id,
            "image": image,
            "disk": disk_gb,
            "label": label,
            "on_start": on_start,
            "runtype": "ssh",
            "python_args": "",
            "env": {"JUPYTER_DIR": "/workspace"},
            "test": False,
        }

        result = self._api_request("PUT", "/create/", data)

        if "error" in result:
            return result

        return {
            "ok": True,
            "instance_id": result.get("new_contract", 0),
            "label": label,
            "offer_id": offer_id,
            "image": image,
            "disk_gb": disk_gb,
            "message": "Instance provisioning. Use wait_for_ready() to wait for SSH access.",
        }

    def wait_for_ready(self, instance_id: int, timeout_s: int = 600, poll_interval: int = 10) -> dict:
        """Wait for an instance to be ready for SSH."""
        start = time.time()
        while time.time() - start < timeout_s:
            instances = self.list_instances()
            for inst in instances:
                if inst.id == instance_id:
                    if inst.status == "running" and inst.ssh_host and inst.ssh_port:
                        return {
                            "ok": True,
                            "instance_id": instance_id,
                            "ssh_host": inst.ssh_host,
                            "ssh_port": inst.ssh_port,
                            "status": inst.status,
                        }
                    if inst.status in ("exited", "error"):
                        return {"error": f"Instance failed (status: {inst.status})"}
            time.sleep(poll_interval)

        return {"error": f"Timeout waiting for instance {instance_id}"}

    def destroy_instance(self, instance_id: int) -> dict:
        """Destroy a rented instance."""
        result = self._api_request("DELETE", f"/instances/{instance_id}/")

        if "error" in result:
            return result

        return {"ok": True, "instance_id": instance_id, "status": "destroyed"}

    def stop_instance(self, instance_id: int) -> dict:
        """Stop a rented instance (can be restarted)."""
        result = self._api_request("PUT", f"/instances/{instance_id}/", {"state": "stop"})
        return result

    def start_instance(self, instance_id: int) -> dict:
        """Start a stopped instance."""
        result = self._api_request("PUT", f"/instances/{instance_id}/", {"state": "start"})
        return result

    def get_instance(self, instance_id: int) -> VastInstance | None:
        """Get a single instance by ID."""
        for inst in self.list_instances():
            if inst.id == instance_id:
                return inst
        return None

    def search_and_rent(
        self,
        gpu_name: str = "H100 NVL",
        min_gpu_ram: float = 80,
        min_reliability: float = 0.9,
        max_price: float = 5.0,
        disk_gb: float = 200,
        image: str = "vastai/unsloth-studio:latest",
        label: str = "anubis-training",
        creator_approved: bool = False,
        approval_token: str = "",
    ) -> dict:
        """Search for offers, pick the cheapest, and rent it. One-call automation."""
        if not creator_approved or approval_token != "creator-approved":
            return {
                "error": "Creator approval required",
                "reason": "Renting a GPU is a financial action. Financial consent law applies.",
            }

        # Search for offers
        offers = self.search_offers(
            gpu_name=gpu_name,
            min_gpu_ram=min_gpu_ram,
            min_reliability=min_reliability,
            max_price=max_price,
        )

        if not offers:
            return {
                "error": f"No offers found for {gpu_name} with min {min_gpu_ram}GB VRAM under ${max_price}/hr",
            }

        # Pick the cheapest
        best = min(offers, key=lambda o: o.dph_total)

        # Rent it
        result = self.rent_instance(
            offer_id=best.id,
            image=image,
            disk_gb=disk_gb,
            label=label,
            creator_approved=True,
            approval_token="creator-approved",
        )

        if "error" in result:
            return result

        return {
            "ok": True,
            "instance_id": result.get("instance_id"),
            "offer": {
                "id": best.id,
                "gpu_name": best.gpu_name,
                "gpu_ram_gb": best.gpu_ram,
                "dph_total": best.dph_total,
                "reliability": best.reliability,
                "country": best.country,
                "cuda_max": best.cuda_max_good,
            },
            "message": "Instance provisioning. Use wait_for_ready() then run_pipeline().",
        }

    def run_pipeline_over_ssh(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_key_path: str | None = None,
        repo_url: str = "https://github.com/sios-os/sios-live.git",
    ) -> dict:
        """Run the training pipeline over SSH on the rented instance.

        This executes the setup and master pipeline in the background.
        Returns immediately — use monitor_pipeline() to check progress.
        """
        ssh_opts = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
        if ssh_key_path:
            ssh_opts.extend(["-i", ssh_key_path])

        # Build the command to run on the remote instance
        remote_cmd = (
            f"git clone {repo_url} /workspace/sios 2>/dev/null; "
            f"cd /workspace/sios && "
            f"bash training/b200_pipeline/setup_h100_unsloth.sh > /workspace/setup.log 2>&1 && "
            f"nohup python training/b200_pipeline/00_master.py > /workspace/pipeline.log 2>&1 &"
        )

        cmd = ["ssh"] + ssh_opts + ["-p", str(ssh_port), f"root@{ssh_host}", remote_cmd]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {
                "ok": True,
                "message": "Pipeline started in background on remote instance",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"ok": True, "message": "Pipeline started (SSH timeout is expected for background process)"}
        except Exception as e:
            return {"error": str(e)}

    def monitor_pipeline(self, ssh_host: str, ssh_port: int, ssh_key_path: str | None = None) -> dict:
        """Check the training pipeline progress over SSH."""
        ssh_opts = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
        if ssh_key_path:
            ssh_opts.extend(["-i", ssh_key_path])

        remote_cmd = (
            "cat /workspace/training_output/pipeline_state.json 2>/dev/null; "
            "echo '---TAIL---'; "
            "tail -20 /workspace/pipeline.log 2>/dev/null"
        )

        cmd = ["ssh"] + ssh_opts + ["-p", str(ssh_port), f"root@{ssh_host}", remote_cmd]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {
                "ok": True,
                "output": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"error": str(e)}

    def download_model(
        self,
        ssh_host: str,
        ssh_port: int,
        local_path: str | Path,
        ssh_key_path: str | None = None,
        quant: str = "Q3_K_M",
    ) -> dict:
        """Download the trained GGUF model from the remote instance."""
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        ssh_opts = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
        if ssh_key_path:
            ssh_opts.extend(["-i", ssh_key_path])

        # Find the GGUF file
        remote_find = "ls /workspace/training_output/gguf/*.gguf 2>/dev/null | head -1"
        find_cmd = ["ssh"] + ssh_opts + ["-p", str(ssh_port), f"root@{ssh_host}", remote_find]

        try:
            find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=30)
            remote_file = find_result.stdout.strip()
            if not remote_file:
                return {"error": "No GGUF model found on remote instance. Pipeline may not be complete."}

            # Download via SCP
            scp_cmd = ["scp"] + ssh_opts + ["-P", str(ssh_port), f"root@{ssh_host}:{remote_file}", str(local_path)]

            subprocess.run(scp_cmd, check=True, timeout=3600)

            size_gb = local_path.stat().st_size / 1e9 if local_path.exists() else 0
            return {
                "ok": True,
                "local_path": str(local_path),
                "remote_path": remote_file,
                "size_gb": size_gb,
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"SCP failed: {e.stderr or str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def get_status_overview(self) -> dict:
        """Get overview of Vast.ai account."""
        if not self.is_configured:
            return {"configured": False, "error": "Vast.ai API not configured"}

        instances = self.list_instances()
        return {
            "configured": True,
            "total_instances": len(instances),
            "running": sum(1 for i in instances if i.status == "running"),
            "instances": [
                {
                    "id": i.id,
                    "label": i.label,
                    "gpu_name": i.gpu_name,
                    "status": i.status,
                    "dph_total": i.dph_total,
                    "ssh_host": i.ssh_host,
                    "ssh_port": i.ssh_port,
                }
                for i in instances
            ],
        }
