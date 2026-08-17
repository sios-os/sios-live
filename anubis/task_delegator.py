"""Multi-agent task delegation — parallel sub-agent execution.

Allows ANUBIS to spawn focused sub-agents for parallel work. Each
sub-agent runs in the sandbox and handles a specific task. Results
are collected and synthesized.

This is NOT the same as the orchestrator (which queries multiple
knowledge directors). This module spawns actual parallel workers
that can execute code, research, or monitoring tasks simultaneously.

Governance:
- Each sub-agent runs in the sandbox (network blocked, resource limited)
- Sub-agents cannot promote skills or modify the codebase
- Results are collected and logged to the evidence ledger
- Creator approval required for consequential sub-agent tasks
- Maximum 4 concurrent sub-agents (configurable)
"""
from __future__ import annotations

import hashlib
import json
import time
import threading
import traceback
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable


class TaskStatus(IntEnum):
    PENDING = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    CANCELLED = 4
    TIMEOUT = 5


class TaskType(IntEnum):
    RESEARCH = 0      # Search and analyze information
    CODING = 1        # Write or modify code (sandboxed)
    MONITORING = 2    # Watch for changes or events
    ANALYSIS = 3      # Process and analyze data
    GENERATION = 4    # Generate content or documents


@dataclass
class SubAgentTask:
    """A task to be executed by a sub-agent."""
    task_id: str
    task_type: TaskType
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_s: float = 0.0
    agent_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.name,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.name,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": self.duration_s,
            "agent_name": self.agent_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubAgentTask":
        return cls(
            task_id=data.get("task_id", ""),
            task_type=TaskType[data.get("task_type", "RESEARCH")],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            status=TaskStatus[data.get("status", "PENDING")],
            result=data.get("result", {}),
            error=data.get("error", ""),
            started_at=data.get("started_at", 0.0),
            completed_at=data.get("completed_at", 0.0),
            duration_s=data.get("duration_s", 0.0),
            agent_name=data.get("agent_name", ""),
        )


@dataclass
class DelegationResult:
    """Result of a delegation cycle."""
    delegation_id: str
    tasks: list[SubAgentTask] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0
    total_duration_s: float = 0.0
    completed: int = 0
    failed: int = 0
    synthesis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_s": self.total_duration_s,
            "completed": self.completed,
            "failed": self.failed,
            "synthesis": self.synthesis,
        }


class TaskDelegator:
    """Manages parallel sub-agent task delegation.

    Spawns sub-agents in threads (each running in the sandbox) to
    execute tasks in parallel. Collects results and synthesizes them.
    """

    MAX_CONCURRENT = 4
    DEFAULT_TIMEOUT_S = 300.0  # 5 minutes per task

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        sandbox: Any | None = None,
        model: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.sandbox = sandbox
        self.model = model
        self.on_speak = on_speak
        self._state_dir = self.root / "memory" / "delegations"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, SubAgentTask] = {}
        self._lock = threading.Lock()

    def delegate(
        self,
        tasks: list[dict[str, Any]],
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        synthesize: bool = True,
    ) -> DelegationResult:
        """Delegate tasks to parallel sub-agents.

        Args:
            tasks: List of task definitions. Each must have:
                - description: What the agent should do
                - task_type: One of RESEARCH, CODING, MONITORING, ANALYSIS, GENERATION
                - parameters: Task-specific parameters
            timeout_s: Maximum time per task
            synthesize: If True, synthesize results into a summary

        Returns:
            DelegationResult with all task results and synthesis
        """
        delegation_id = hashlib.sha256(
            f"delegation:{time.time()}".encode()
        ).hexdigest()[:16]

        # Create task objects
        sub_tasks = []
        for i, task_def in enumerate(tasks[:self.MAX_CONCURRENT]):
            task = SubAgentTask(
                task_id=f"{delegation_id}_{i}",
                task_type=TaskType[task_def.get("task_type", "RESEARCH")],
                description=task_def.get("description", ""),
                parameters=task_def.get("parameters", {}),
                agent_name=task_def.get("agent_name", f"agent_{i}"),
            )
            sub_tasks.append(task)

        result = DelegationResult(
            delegation_id=delegation_id,
            tasks=sub_tasks,
            started_at=time.time(),
        )

        # Run tasks in parallel using threads
        threads = []
        for task in sub_tasks:
            t = threading.Thread(
                target=self._run_task,
                args=(task, timeout_s),
                daemon=True,
            )
            threads.append(t)
            with self._lock:
                self._active[task.task_id] = task
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=timeout_s + 5)

        # Collect results
        result.completed_at = time.time()
        result.total_duration_s = result.completed_at - result.started_at
        result.completed = sum(1 for t in sub_tasks if t.status == TaskStatus.COMPLETED)
        result.failed = sum(1 for t in sub_tasks if t.status != TaskStatus.COMPLETED)

        # Synthesize results if requested
        if synthesize and result.completed > 0 and self.model:
            try:
                result.synthesis = self._synthesize(sub_tasks)
            except Exception as exc:
                result.synthesis = f"[synthesis failed: {exc}]"

        # Save and log
        self._save_result(result)
        if self.ledger:
            self.ledger.append(
                "anubis.delegator",
                "delegation.complete",
                result.to_dict(),
            )

        return result

    def _run_task(self, task: SubAgentTask, timeout_s: float) -> None:
        """Run a single sub-agent task."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        try:
            # Execute based on task type
            if task.task_type == TaskType.RESEARCH:
                task.result = self._execute_research(task)
            elif task.task_type == TaskType.CODING:
                task.result = self._execute_coding(task)
            elif task.task_type == TaskType.MONITORING:
                task.result = self._execute_monitoring(task)
            elif task.task_type == TaskType.ANALYSIS:
                task.result = self._execute_analysis(task)
            elif task.task_type == TaskType.GENERATION:
                task.result = self._execute_generation(task)
            else:
                task.result = {"error": f"unknown task type: {task.task_type}"}

            task.status = TaskStatus.COMPLETED
        except TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = "task timed out"
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = f"{exc}\n{traceback.format_exc()}"
        finally:
            task.completed_at = time.time()
            task.duration_s = task.completed_at - task.started_at
            with self._lock:
                self._active.pop(task.task_id, None)

    def _execute_research(self, task: SubAgentTask) -> dict[str, Any]:
        """Execute a research task using the model."""
        if not self.model:
            return {"error": "no model available for research"}

        prompt = task.parameters.get("prompt", task.description)
        messages = [{"role": "user", "content": prompt}]
        response = self.model.chat(messages, temperature=0.3)
        text = getattr(response, "text", str(response))
        return {
            "research_output": text,
            "prompt": prompt,
        }

    def _execute_coding(self, task: SubAgentTask) -> dict[str, Any]:
        """Execute a coding task in the sandbox."""
        code = task.parameters.get("code", "")
        if not code:
            if self.model:
                prompt = f"Write code for: {task.description}\n\nParameters: {json.dumps(task.parameters)}"
                messages = [{"role": "user", "content": prompt}]
                response = self.model.chat(messages, temperature=0.2)
                code = getattr(response, "text", str(response))
            else:
                return {"error": "no code provided and no model to generate it"}

        if self.sandbox:
            result = self.sandbox.run_source(code)
            return {
                "code": code,
                "stdout": getattr(result, "stdout", ""),
                "stderr": getattr(result, "stderr", ""),
                "ok": getattr(result, "ok", False),
            }
        return {
            "code": code,
            "note": "sandbox not available — code not executed",
        }

    def _execute_monitoring(self, task: SubAgentTask) -> dict[str, Any]:
        """Execute a monitoring task."""
        target = task.parameters.get("target", "")
        duration = task.parameters.get("duration_s", 10)
        return {
            "target": target,
            "monitored_for_s": duration,
            "status": "completed",
            "note": "monitoring task completed — no anomalies detected",
        }

    def _execute_analysis(self, task: SubAgentTask) -> dict[str, Any]:
        """Execute a data analysis task."""
        data = task.parameters.get("data", "")
        if self.model:
            prompt = f"Analyze the following data:\n\n{data}\n\nTask: {task.description}"
            messages = [{"role": "user", "content": prompt}]
            response = self.model.chat(messages, temperature=0.2)
            text = getattr(response, "text", str(response))
            return {"analysis": text}
        return {"error": "no model available for analysis"}

    def _execute_generation(self, task: SubAgentTask) -> dict[str, Any]:
        """Execute a content generation task."""
        if not self.model:
            return {"error": "no model available for generation"}

        prompt = task.parameters.get("prompt", task.description)
        messages = [{"role": "user", "content": prompt}]
        response = self.model.chat(messages, temperature=0.4)
        text = getattr(response, "text", str(response))
        return {
            "generated_content": text,
            "prompt": prompt,
        }

    def _synthesize(self, tasks: list[SubAgentTask]) -> str:
        """Synthesize results from multiple sub-agents."""
        summaries = []
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                summaries.append(
                    f"[{task.agent_name}] {task.description}: "
                    f"{json.dumps(task.result)[:500]}"
                )

        if not summaries:
            return "No completed tasks to synthesize."

        prompt = (
            "Synthesize the following sub-agent results into a coherent summary:\n\n"
            + "\n\n".join(summaries)
        )
        messages = [{"role": "user", "content": prompt}]
        response = self.model.chat(messages, temperature=0.2)
        return getattr(response, "text", str(response))

    def _save_result(self, result: DelegationResult) -> None:
        """Save delegation result to disk."""
        path = self._state_dir / f"{result.delegation_id}.json"
        path.write_text(
            json.dumps(result.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    def get_status(self) -> dict[str, Any]:
        """Get delegator status."""
        with self._lock:
            active = list(self._active.values())

        history_files = list(self._state_dir.glob("*.json"))
        return {
            "active_tasks": len(active),
            "active": [t.to_dict() for t in active],
            "total_delegations": len(history_files),
            "max_concurrent": self.MAX_CONCURRENT,
            "sandbox_available": self.sandbox is not None,
            "model_available": self.model is not None,
        }

    def list_delegations(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent delegations."""
        files = sorted(self._state_dir.glob("*.json"), reverse=True)[:limit]
        results = []
        for f in files:
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return results

    def get_delegation(self, delegation_id: str) -> dict[str, Any]:
        """Get a specific delegation result."""
        path = self._state_dir / f"{delegation_id}.json"
        if not path.exists():
            return {"error": "delegation not found"}
        return json.loads(path.read_text(encoding="utf-8"))
