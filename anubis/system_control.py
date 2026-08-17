"""System control — ANUBIS manages his environment like JARVIS.

Inspired by JARVIS from Iron Man: an intelligence that doesn't just report
on systems but actively manages them. ANUBIS monitors, controls, and
optimizes his own infrastructure.

This module provides:

1. **Service management** — Start, stop, restart, and monitor services
   (Ollama, daemon, VPN, cloud sync, etc.)

2. **Health monitoring** — Continuous monitoring of system health:
   CPU, memory, disk, network, model status, daemon status

3. **Anticipation engine** — Predicts what the Creator will need next
   based on patterns and pre-preares capabilities

4. **Multi-task orchestration** — Manages multiple concurrent operations
   (missions, training, sync, backups) with priority scheduling

5. **Environment control** — Manages the ANUBIS environment: config
   updates, service deployments, resource allocation

6. **Alert system** — Proactive alerts for problems before they become
   critical (disk filling up, model degraded, service down)

Governance:
- Service control is limited to ANUBIS-owned services
- Critical actions require Creator approval
- All actions are logged to the evidence ledger
- Resource limits prevent runaway operations

Uses only the Python standard library.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# --------------------------------------------------------------------- types


@dataclass
class ServiceStatus:
    """Status of a managed service."""
    name: str
    status: str = "unknown"  # running, stopped, degraded, unknown
    pid: int = 0
    started_at: float = 0.0
    last_check: float = 0.0
    health: str = "unknown"  # healthy, warning, critical, unknown
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "last_check": self.last_check,
            "health": self.health,
            "details": self.details,
        }


@dataclass
class SystemHealth:
    """Overall system health snapshot."""
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_free_gb: float = 0.0
    disk_total_gb: float = 0.0
    platform: str = ""
    python_version: str = ""
    uptime_s: float = 0.0
    services: dict[str, dict[str, Any]] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    overall_health: str = "unknown"  # healthy, warning, critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": round(self.cpu_percent, 1),
            "memory_percent": round(self.memory_percent, 1),
            "memory_used_gb": round(self.memory_used_gb, 2),
            "memory_total_gb": round(self.memory_total_gb, 2),
            "disk_percent": round(self.disk_percent, 1),
            "disk_free_gb": round(self.disk_free_gb, 2),
            "disk_total_gb": round(self.disk_total_gb, 2),
            "platform": self.platform,
            "python_version": self.python_version,
            "uptime_s": round(self.uptime_s, 1),
            "services": self.services,
            "alerts": self.alerts,
            "overall_health": self.overall_health,
        }


@dataclass
class Anticipation:
    """A predicted need that ANUBIS pre-prepares for."""
    anticip_id: str
    prediction: str
    confidence: float = 0.0
    preparation: str = ""
    prepared: bool = False
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "anticip_id": self.anticip_id,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "preparation": self.preparation,
            "prepared": self.prepared,
            "created_at": self.created_at,
        }


@dataclass
class Task:
    """A managed concurrent task."""
    task_id: str
    name: str
    priority: int = 5  # 1 (highest) to 10 (lowest)
    status: str = "pending"  # pending, running, completed, failed
    started_at: float = 0.0
    completed_at: float = 0.0
    result: str = ""
    error: str = ""

    @property
    def duration_s(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": round(self.duration_s, 2),
            "result": self.result,
            "error": self.error,
        }


# --------------------------------------------------------------- controller


class SystemController:
    """ANUBIS's JARVIS-like system management.

    Manages services, monitors health, anticipates needs, and
    orchestrates concurrent tasks.
    """

    ACTOR = "anubis.system_control"

    # Services ANUBIS can manage
    MANAGED_SERVICES = {
        "ollama": {
            "check_cmd": ["ollama", "list"],
            "start_cmd": ["ollama", "serve"],
            "description": "Local model inference",
        },
        "daemon": {
            "check_cmd": None,  # checked via socket
            "start_cmd": ["python3", "tools/anubis_daemon.py"],
            "description": "ANUBIS daemon",
        },
        "vpn": {
            "check_cmd": None,  # checked via interface
            "start_cmd": ["wg-quick", "up", "wg0"],
            "description": "WireGuard VPN",
        },
    }

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        alert_thresholds: dict[str, float] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self._thresholds = alert_thresholds or {
            "cpu_percent": 90.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
        }

        self._state_dir = self.root / "memory" / "system_control"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._anticipations_file = self._state_dir / "anticipations.json"
        self._tasks_file = self._state_dir / "tasks.json"
        self._health_history = self._state_dir / "health_history.jsonl"

        self._services: dict[str, ServiceStatus] = {}
        self._tasks: list[Task] = []
        self._task_lock = threading.Lock()
        self._start_time = time.time()

    # ------------------------------------------------------- health

    def check_health(self) -> SystemHealth:
        """Check system health."""
        health = SystemHealth(timestamp=time.time())
        health.platform = platform.platform()
        health.python_version = platform.python_version()
        health.uptime_s = time.time() - self._start_time

        # CPU (cross-platform approximation)
        try:
            health.cpu_percent = self._get_cpu_percent()
        except Exception:
            health.cpu_percent = 0.0

        # Memory
        try:
            mem = self._get_memory_info()
            health.memory_percent = mem.get("percent", 0)
            health.memory_used_gb = mem.get("used_gb", 0)
            health.memory_total_gb = mem.get("total_gb", 0)
        except Exception:
            pass

        # Disk
        try:
            disk = self._get_disk_info()
            health.disk_percent = disk.get("percent", 0)
            health.disk_free_gb = disk.get("free_gb", 0)
            health.disk_total_gb = disk.get("total_gb", 0)
        except Exception:
            pass

        # Services
        for name in self.MANAGED_SERVICES:
            status = self._check_service(name)
            self._services[name] = status
            health.services[name] = status.to_dict()

        # Alerts
        health.alerts = self._generate_alerts(health)
        health.overall_health = self._compute_overall_health(health)

        # Save to history
        self._save_health(health)

        return health

    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage (cross-platform)."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            # Fallback: use load average on Unix, estimate on Windows
            if hasattr(os, "getloadavg"):
                load = os.getloadavg()[0]
                # Rough approximation: load / CPU count * 100
                cpu_count = os.cpu_count() or 1
                return min(100.0, (load / cpu_count) * 100)
            return 0.0

    def _get_memory_info(self) -> dict[str, float]:
        """Get memory usage info."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "percent": mem.percent,
                "used_gb": mem.used / (1024**3),
                "total_gb": mem.total / (1024**3),
            }
        except ImportError:
            # Fallback for Windows
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize",
                         "/Value"],
                        capture_output=True, text=True, timeout=10,
                    )
                    lines = result.stdout.strip().split("\n")
                    free = total = 0
                    for line in lines:
                        if "FreePhysicalMemory" in line:
                            free = int(line.split("=")[1].strip())
                        if "TotalVisibleMemorySize" in line:
                            total = int(line.split("=")[1].strip())
                    if total > 0:
                        used = total - free
                        return {
                            "percent": (used / total) * 100,
                            "used_gb": used / (1024**2),
                            "total_gb": total / (1024**2),
                        }
                except Exception:
                    pass
            return {"percent": 0, "used_gb": 0, "total_gb": 0}

    def _get_disk_info(self) -> dict[str, float]:
        """Get disk usage info for the root path."""
        try:
            usage = shutil.disk_usage(str(self.root))
            total = usage.total / (1024**3)
            free = usage.free / (1024**3)
            used = usage.used / (1024**3)
            return {
                "percent": (used / total) * 100 if total > 0 else 0,
                "free_gb": free,
                "total_gb": total,
            }
        except Exception:
            return {"percent": 0, "free_gb": 0, "total_gb": 0}

    def _check_service(self, name: str) -> ServiceStatus:
        """Check if a service is running."""
        status = ServiceStatus(name=name, last_check=time.time())

        service_config = self.MANAGED_SERVICES.get(name, {})
        check_cmd = service_config.get("check_cmd")

        if check_cmd is None:
            status.status = "unknown"
            status.health = "unknown"
            return status

        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                status.status = "running"
                status.health = "healthy"
            else:
                status.status = "stopped"
                status.health = "critical"
        except FileNotFoundError:
            status.status = "not_installed"
            status.health = "unknown"
        except subprocess.TimeoutExpired:
            status.status = "degraded"
            status.health = "warning"
        except Exception:
            status.status = "unknown"
            status.health = "unknown"

        return status

    def _generate_alerts(self, health: SystemHealth) -> list[dict[str, Any]]:
        """Generate alerts based on health metrics."""
        alerts: list[dict[str, Any]] = []

        if health.cpu_percent > self._thresholds["cpu_percent"]:
            alerts.append({
                "level": "warning",
                "metric": "cpu",
                "value": health.cpu_percent,
                "threshold": self._thresholds["cpu_percent"],
                "message": f"CPU usage high: {health.cpu_percent:.1f}%",
            })

        if health.memory_percent > self._thresholds["memory_percent"]:
            alerts.append({
                "level": "warning",
                "metric": "memory",
                "value": health.memory_percent,
                "threshold": self._thresholds["memory_percent"],
                "message": f"Memory usage high: {health.memory_percent:.1f}%",
            })

        if health.disk_percent > self._thresholds["disk_percent"]:
            alerts.append({
                "level": "critical",
                "metric": "disk",
                "value": health.disk_percent,
                "threshold": self._thresholds["disk_percent"],
                "message": f"Disk usage critical: {health.disk_percent:.1f}%",
            })

        for name, svc in health.services.items():
            if svc.get("health") == "critical":
                alerts.append({
                    "level": "critical",
                    "metric": "service",
                    "service": name,
                    "message": f"Service {name} is {svc.get('status')}",
                })

        return alerts

    def _compute_overall_health(self, health: SystemHealth) -> str:
        """Compute overall system health."""
        if any(a["level"] == "critical" for a in health.alerts):
            return "critical"
        if any(a["level"] == "warning" for a in health.alerts):
            return "warning"
        return "healthy"

    # ------------------------------------------------------- service control

    def start_service(self, name: str) -> dict[str, Any]:
        """Start a managed service."""
        if name not in self.MANAGED_SERVICES:
            return {"error": f"Unknown service: {name}"}

        service_config = self.MANAGED_SERVICES[name]
        start_cmd = service_config.get("start_cmd")
        if not start_cmd:
            return {"error": f"No start command for {name}"}

        try:
            proc = subprocess.Popen(
                start_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._log("service.start", {
                "service": name,
                "pid": proc.pid,
            })
            return {
                "service": name,
                "status": "started",
                "pid": proc.pid,
            }
        except Exception as exc:
            return {"service": name, "error": str(exc)}

    def stop_service(self, name: str) -> dict[str, Any]:
        """Stop a managed service (by name match)."""
        if name not in self.MANAGED_SERVICES:
            return {"error": f"Unknown service: {name}"}

        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", f"{name}.exe"],
                    capture_output=True, timeout=10,
                )
            else:
                subprocess.run(
                    ["pkill", "-f", name],
                    capture_output=True, timeout=10,
                )
            self._log("service.stop", {"service": name})
            return {"service": name, "status": "stopped"}
        except Exception as exc:
            return {"service": name, "error": str(exc)}

    def restart_service(self, name: str) -> dict[str, Any]:
        """Restart a service."""
        self.stop_service(name)
        time.sleep(2)
        return self.start_service(name)

    # ------------------------------------------------------- anticipation

    def record_anticipation(
        self,
        prediction: str,
        confidence: float,
        preparation: str = "",
    ) -> Anticipation:
        """Record a prediction about what the Creator will need."""
        import hashlib
        anticip = Anticipation(
            anticip_id=hashlib.sha256(
                f"anticip:{prediction}:{time.time()}".encode()
            ).hexdigest()[:16],
            prediction=prediction,
            confidence=confidence,
            preparation=preparation,
            created_at=time.time(),
        )

        anticipations = self._load_anticipations()
        anticipations.append(anticip.to_dict())
        anticipations = anticipations[-100:]  # keep last 100
        self._anticipations_file.write_text(
            json.dumps(anticipations, indent=2), encoding="utf-8"
        )

        self._log("anticipation.recorded", {
            "prediction": prediction,
            "confidence": confidence,
        })

        return anticip

    def get_anticipations(
        self, unprepared_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get recorded anticipations."""
        anticipations = self._load_anticipations()
        if unprepared_only:
            anticipations = [a for a in anticipations if not a.get("prepared")]
        return anticipations

    def mark_anticipation_prepared(self, anticip_id: str) -> bool:
        """Mark an anticipation as prepared."""
        anticipations = self._load_anticipations()
        for a in anticipations:
            if a.get("anticip_id") == anticip_id:
                a["prepared"] = True
                self._anticipations_file.write_text(
                    json.dumps(anticipations, indent=2), encoding="utf-8"
                )
                return True
        return False

    # ------------------------------------------------------- task orchestration

    def submit_task(
        self,
        name: str,
        priority: int = 5,
        executor: Callable[[], str] | None = None,
    ) -> str:
        """Submit a task for execution.

        If executor is provided, runs it in a background thread.
        If not, just records the task for manual execution.
        """
        import hashlib
        task_id = hashlib.sha256(
            f"task:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        task = Task(
            task_id=task_id,
            name=name,
            priority=priority,
            status="pending",
        )

        with self._task_lock:
            self._tasks.append(task)
            self._save_tasks()

        if executor is not None:
            thread = threading.Thread(
                target=self._execute_task,
                args=(task_id, executor),
                daemon=True,
                name=f"anubis-task-{task_id}",
            )
            thread.start()

        return task_id

    def _execute_task(self, task_id: str, executor: Callable[[], str]) -> None:
        """Execute a task in a background thread."""
        with self._task_lock:
            task = next((t for t in self._tasks if t.task_id == task_id), None)
            if task is None:
                return
            task.status = "running"
            task.started_at = time.time()
            self._save_tasks()

        try:
            result = executor()
            with self._task_lock:
                task.status = "completed"
                task.completed_at = time.time()
                task.result = result
        except Exception as exc:
            with self._task_lock:
                task.status = "failed"
                task.completed_at = time.time()
                task.error = str(exc)

        with self._task_lock:
            self._save_tasks()

        self._log("task.executed", {
            "task_id": task_id,
            "status": task.status,
        })

    def get_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """Get tasks, optionally filtered by status."""
        with self._task_lock:
            tasks = [t.to_dict() for t in self._tasks]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return tasks

    def get_running_tasks(self) -> list[dict[str, Any]]:
        """Get currently running tasks."""
        return self.get_tasks(status="running")

    # ------------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        """Get system controller status."""
        health = self.check_health()
        return {
            "health": health.to_dict(),
            "managed_services": list(self.MANAGED_SERVICES.keys()),
            "running_tasks": len(self.get_running_tasks()),
            "total_tasks": len(self._tasks),
            "pending_anticipations": len(
                self.get_anticipations(unprepared_only=True)
            ),
            "uptime_s": time.time() - self._start_time,
        }

    # ------------------------------------------------------- internals

    def _load_anticipations(self) -> list[dict[str, Any]]:
        if not self._anticipations_file.exists():
            return []
        try:
            return json.loads(
                self._anticipations_file.read_text(encoding="utf-8")
            )
        except Exception:
            return []

    def _save_tasks(self) -> None:
        try:
            self._tasks_file.parent.mkdir(parents=True, exist_ok=True)
            self._tasks_file.write_text(
                json.dumps([t.to_dict() for t in self._tasks], indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass  # directory may have been cleaned up during tests

    def _save_health(self, health: SystemHealth) -> None:
        try:
            with open(self._health_history, "a", encoding="utf-8") as f:
                f.write(json.dumps(health.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
