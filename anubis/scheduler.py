"""Autonomous scheduler — the heartbeat of ANUBIS.

This module implements the autonomous scheduling layer that makes ANUBIS
proactive rather than reactive. It runs on a timer and triggers:

1. **Dream cycles** when ANUBIS has been idle (no Creator interaction)
2. **Midnight purge** — automatic memory purge and distillation
3. **Mission processing** — works through the mission queue
4. **Training preparation** — prepares training plans when enough data exists
5. **Evaluation** — periodic self-evaluation benchmarks
6. **Knowledge acquisition** — lawful research to fill identified gaps

The scheduler is designed to run as a background thread within the daemon.
It checks periodically and triggers the appropriate action based on time
elapsed and system state.

Governance:
- Training execution still requires Creator approval
- Knowledge acquisition goes through quarantine
- Dream cycles are logged to the evidence ledger
- The scheduler never bypasses constitutional gates

Uses only the Python standard library.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


# --------------------------------------------------------------------- types


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


@dataclass
class ScheduleConfig:
    """Configuration for the autonomous scheduler."""
    # How often to check if an action should run (seconds)
    check_interval_s: float = 60.0
    # Idle threshold before triggering dream cycle (seconds)
    idle_threshold_s: float = 300.0  # 5 minutes of no interaction
    # Time between dream cycles (seconds)
    dream_cycle_interval_s: float = 3600.0  # 1 hour
    # Time between automatic purges (seconds)
    purge_interval_s: float = 86400.0  # 24 hours
    # Time between mission queue processing (seconds)
    mission_process_interval_s: float = 1800.0  # 30 minutes
    # Time between training plan preparation checks (seconds)
    training_check_interval_s: float = 7200.0  # 2 hours
    # Time between evaluation benchmarks (seconds)
    evaluation_interval_s: float = 604800.0  # 1 week
    # Time between knowledge acquisition attempts (seconds)
    knowledge_acquire_interval_s: float = 14400.0  # 4 hours
    # Maximum missions to process per cycle
    max_missions_per_cycle: int = 3
    # Time between state snapshots (seconds)
    snapshot_interval_s: float = 3600.0  # 1 hour
    # Time between self-repair health checks (seconds)
    self_repair_check_interval_s: float = 1800.0  # 30 minutes
    # Time between drive reports (seconds)
    drive_report_interval_s: float = 86400.0  # 24 hours
    # Time between cold archive creation (seconds)
    cold_archive_interval_s: float = 7776000.0  # 90 days
    # Time between snapshot retention pruning (seconds)
    retention_interval_s: float = 86400.0  # 24 hours
    # Time between autonomous prospecting searches (seconds)
    prospecting_interval_s: float = 86400.0  # 24 hours
    # Time between autonomous research cycles (seconds)
    research_interval_s: float = 7200.0  # 2 hours
    # Whether the scheduler is enabled
    enabled: bool = True


@dataclass
class SchedulerState:
    """Tracks when each action was last run."""
    last_interaction: float = 0.0
    last_dream_cycle: float = 0.0
    last_purge: float = 0.0
    last_mission_process: float = 0.0
    last_training_check: float = 0.0
    last_evaluation: float = 0.0
    last_knowledge_acquire: float = 0.0
    last_snapshot: float = 0.0
    last_self_repair_check: float = 0.0
    last_drive_report: float = 0.0
    last_cold_archive: float = 0.0
    last_retention: float = 0.0
    last_prospecting: float = 0.0
    last_research: float = 0.0
    running: bool = False
    current_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_interaction": self.last_interaction,
            "last_dream_cycle": self.last_dream_cycle,
            "last_purge": self.last_purge,
            "last_mission_process": self.last_mission_process,
            "last_training_check": self.last_training_check,
            "last_evaluation": self.last_evaluation,
            "last_knowledge_acquire": self.last_knowledge_acquire,
            "last_snapshot": self.last_snapshot,
            "last_self_repair_check": self.last_self_repair_check,
            "last_drive_report": self.last_drive_report,
            "last_cold_archive": self.last_cold_archive,
            "last_retention": self.last_retention,
            "running": self.running,
            "current_action": self.current_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchedulerState":
        return cls(
            last_interaction=data.get("last_interaction", 0.0),
            last_dream_cycle=data.get("last_dream_cycle", 0.0),
            last_purge=data.get("last_purge", 0.0),
            last_mission_process=data.get("last_mission_process", 0.0),
            last_training_check=data.get("last_training_check", 0.0),
            last_evaluation=data.get("last_evaluation", 0.0),
            last_knowledge_acquire=data.get("last_knowledge_acquire", 0.0),
            last_snapshot=data.get("last_snapshot", 0.0),
            last_self_repair_check=data.get("last_self_repair_check", 0.0),
            last_drive_report=data.get("last_drive_report", 0.0),
            last_cold_archive=data.get("last_cold_archive", 0.0),
            last_retention=data.get("last_retention", 0.0),
            running=data.get("running", False),
            current_action=data.get("current_action", ""),
        )


# --------------------------------------------------------------- scheduler


class AutonomousScheduler:
    """Background scheduler that makes ANUBIS proactive.

    Runs in a background thread, periodically checking whether actions
    should be triggered based on time elapsed and system state.

    Usage:
        scheduler = AutonomousScheduler(model, root, ...)
        scheduler.start()  # starts background thread
        # ... daemon runs normally ...
        scheduler.stop()   # clean shutdown

    The scheduler calls registered action callbacks. If no callback is
    registered for an action, it's skipped.
    """

    ACTOR = "anubis.scheduler"

    def __init__(
        self,
        root: str | Path,
        config: ScheduleConfig | None = None,
        *,
        on_dream_cycle: Callable[[], dict[str, Any]] | None = None,
        on_purge: Callable[[], dict[str, Any]] | None = None,
        on_process_missions: Callable[[int], dict[str, Any]] | None = None,
        on_training_check: Callable[[], dict[str, Any]] | None = None,
        on_evaluation: Callable[[], dict[str, Any]] | None = None,
        on_knowledge_acquire: Callable[[], dict[str, Any]] | None = None,
        on_snapshot: Callable[[], dict[str, Any]] | None = None,
        on_self_repair_check: Callable[[], dict[str, Any]] | None = None,
        on_drive_report: Callable[[], dict[str, Any]] | None = None,
        on_cold_archive: Callable[[], dict[str, Any]] | None = None,
        on_retention: Callable[[], dict[str, Any]] | None = None,
        on_prospecting: Callable[[], dict[str, Any]] | None = None,
        on_research: Callable[[], dict[str, Any]] | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.config = config or ScheduleConfig()
        self.ledger = ledger

        self._on_dream = on_dream_cycle
        self._on_purge = on_purge
        self._on_missions = on_process_missions
        self._on_training = on_training_check
        self._on_eval = on_evaluation
        self._on_knowledge = on_knowledge_acquire
        self._on_snapshot = on_snapshot
        self._on_self_repair_check = on_self_repair_check
        self._on_drive_report = on_drive_report
        self._on_cold_archive = on_cold_archive
        self._on_retention = on_retention
        self._on_prospecting = on_prospecting
        self._on_research = on_research

        self._state_file = self.root / "memory" / "scheduler_state.json"
        self._state = self._load_state()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _load_state(self) -> SchedulerState:
        if self._state_file.exists():
            try:
                data = json.loads(
                    self._state_file.read_text(encoding="utf-8")
                )
                return SchedulerState.from_dict(data)
            except Exception:
                pass
        return SchedulerState()

    def _save_state(self) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ------------------------------------------------------------- lifecycle

    def start(self) -> None:
        """Start the scheduler background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="anubis-scheduler"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10.0)
        self._thread = None

    def notify_interaction(self) -> None:
        """Call this when the Creator interacts with ANUBIS.

        This resets the idle timer and prevents dream cycles from
        starting while the Creator is actively engaged.
        """
        with self._lock:
            self._state.last_interaction = time.time()
            self._save_state()

    def trigger_dream_cycle(self) -> dict[str, Any]:
        """Manually trigger a dream cycle (bypasses idle check)."""
        return self._run_action("dream_cycle", self._on_dream)

    def trigger_purge(self) -> dict[str, Any]:
        """Manually trigger a purge."""
        return self._run_action("purge", self._on_purge)

    def trigger_snapshot(self) -> dict[str, Any]:
        """Manually trigger a snapshot."""
        return self._run_action("snapshot", self._on_snapshot)

    def trigger_self_repair_check(self) -> dict[str, Any]:
        """Manually trigger a self-repair health check."""
        return self._run_action("self_repair_check", self._on_self_repair_check)

    def trigger_drive_report(self) -> dict[str, Any]:
        """Manually trigger a drive report."""
        return self._run_action("drive_report", self._on_drive_report)

    def trigger_cold_archive(self) -> dict[str, Any]:
        """Manually trigger a cold archive creation."""
        return self._run_action("cold_archive", self._on_cold_archive)

    def trigger_retention(self) -> dict[str, Any]:
        """Manually trigger snapshot retention pruning."""
        return self._run_action("retention", self._on_retention)

    def trigger_mission_processing(self, count: int = 3) -> dict[str, Any]:
        """Manually trigger mission processing."""
        if self._on_missions:
            return self._run_action(
                "mission_process", lambda: self._on_missions(count)
            )
        return {"error": "no mission handler registered"}

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status."""
        now = time.time()
        state = self._state.to_dict()
        state["uptime"] = now - (state.get("last_interaction", 0) or now)
        state["idle_seconds"] = now - max(
            state.get("last_interaction", 0), 0
        )
        state["config"] = {
            "check_interval_s": self.config.check_interval_s,
            "idle_threshold_s": self.config.idle_threshold_s,
            "dream_cycle_interval_s": self.config.dream_cycle_interval_s,
            "purge_interval_s": self.config.purge_interval_s,
            "mission_process_interval_s": self.config.mission_process_interval_s,
            "training_check_interval_s": self.config.training_check_interval_s,
            "evaluation_interval_s": self.config.evaluation_interval_s,
            "knowledge_acquire_interval_s": self.config.knowledge_acquire_interval_s,
            "snapshot_interval_s": self.config.snapshot_interval_s,
            "self_repair_check_interval_s": self.config.self_repair_check_interval_s,
            "drive_report_interval_s": self.config.drive_report_interval_s,
            "cold_archive_interval_s": self.config.cold_archive_interval_s,
            "retention_interval_s": self.config.retention_interval_s,
            "enabled": self.config.enabled,
        }
        state["next_actions"] = self._compute_next_actions(now)
        return state

    # ------------------------------------------------------------- internals

    def _run_loop(self) -> None:
        """Main scheduler loop — runs in background thread."""
        while not self._stop_event.is_set():
            try:
                if self.config.enabled:
                    self._tick()
            except Exception:
                pass  # scheduler must never crash the daemon
            self._stop_event.wait(self.config.check_interval_s)

    def _tick(self) -> None:
        """Check all actions and trigger any that are due."""
        now = time.time()
        state = self._state

        with self._lock:
            idle_time = now - state.last_interaction if state.last_interaction else 999999

        # 1. Dream cycle — only when idle
        if (
            idle_time > self.config.idle_threshold_s
            and now - state.last_dream_cycle > self.config.dream_cycle_interval_s
            and self._on_dream is not None
        ):
            self._run_action("dream_cycle", self._on_dream)

        # 2. Purge — time-based, not idle-dependent
        if (
            now - state.last_purge > self.config.purge_interval_s
            and self._on_purge is not None
        ):
            self._run_action("purge", self._on_purge)

        # 3. Mission processing — regular cadence
        if (
            now - state.last_mission_process > self.config.mission_process_interval_s
            and self._on_missions is not None
        ):
            self._run_action(
                "mission_process",
                lambda: self._on_missions(self.config.max_missions_per_cycle),
            )

        # 4. Training check
        if (
            now - state.last_training_check > self.config.training_check_interval_s
            and self._on_training is not None
        ):
            self._run_action("training_check", self._on_training)

        # 5. Evaluation
        if (
            now - state.last_evaluation > self.config.evaluation_interval_s
            and self._on_eval is not None
        ):
            self._run_action("evaluation", self._on_eval)

        # 6. Knowledge acquisition
        if (
            now - state.last_knowledge_acquire > self.config.knowledge_acquire_interval_s
            and self._on_knowledge is not None
        ):
            self._run_action("knowledge_acquire", self._on_knowledge)

        # 7. State snapshot — periodic immutable snapshot
        if (
            now - state.last_snapshot > self.config.snapshot_interval_s
            and self._on_snapshot is not None
        ):
            self._run_action("snapshot", self._on_snapshot)

        # 8. Self-repair health check — periodic corruption detection
        if (
            now - state.last_self_repair_check > self.config.self_repair_check_interval_s
            and self._on_self_repair_check is not None
        ):
            self._run_action("self_repair_check", self._on_self_repair_check)

        # 9. Drive report — daily drive health notification
        if (
            now - state.last_drive_report > self.config.drive_report_interval_s
            and self._on_drive_report is not None
        ):
            self._run_action("drive_report", self._on_drive_report)

        # 10. Cold archive — quarterly compressed encrypted archive
        if (
            now - state.last_cold_archive > self.config.cold_archive_interval_s
            and self._on_cold_archive is not None
        ):
            self._run_action("cold_archive", self._on_cold_archive)

        # 11. Snapshot retention — prune old snapshots
        if (
            now - state.last_retention > self.config.retention_interval_s
            and self._on_retention is not None
        ):
            self._run_action("retention", self._on_retention)

        # 12. Autonomous prospecting — search for funding opportunities
        if (
            now - state.last_prospecting > self.config.prospecting_interval_s
            and self._on_prospecting is not None
        ):
            self._run_action("prospecting", self._on_prospecting)

        # 13. Autonomous research — identify gaps and propose hypotheses
        if (
            now - state.last_research > self.config.research_interval_s
            and self._on_research is not None
        ):
            self._run_action("research", self._on_research)

    def _run_action(
        self, name: str, callback: Callable[[], dict[str, Any]] | None
    ) -> dict[str, Any]:
        """Run a single scheduled action."""
        if callback is None:
            return {"error": f"no handler for {name}"}

        with self._lock:
            self._state.running = True
            self._state.current_action = name
            self._save_state()

        self._log(f"{name}.start", {})
        result: dict[str, Any] = {}
        try:
            result = callback() or {}
        except Exception as exc:
            result = {"error": str(exc)}
            self._log(f"{name}.error", {"error": str(exc)})

        # Update last-run timestamp
        attr_map = {
            "dream_cycle": "last_dream_cycle",
            "purge": "last_purge",
            "mission_process": "last_mission_process",
            "training_check": "last_training_check",
            "evaluation": "last_evaluation",
            "knowledge_acquire": "last_knowledge_acquire",
            "snapshot": "last_snapshot",
            "self_repair_check": "last_self_repair_check",
            "drive_report": "last_drive_report",
            "cold_archive": "last_cold_archive",
            "retention": "last_retention",
            "prospecting": "last_prospecting",
            "research": "last_research",
        }
        with self._lock:
            attr = attr_map.get(name)
            if attr:
                setattr(self._state, attr, time.time())
            self._state.running = False
            self._state.current_action = ""
            self._save_state()

        self._log(f"{name}.end", result)
        return result

    def _compute_next_actions(self, now: float) -> list[dict[str, Any]]:
        """Compute when each action will next run."""
        state = self._state
        actions = [
            {
                "action": "dream_cycle",
                "next_in_s": max(
                    0,
                    self.config.dream_cycle_interval_s
                    - (now - state.last_dream_cycle),
                ),
                "requires_idle": True,
            },
            {
                "action": "purge",
                "next_in_s": max(
                    0,
                    self.config.purge_interval_s
                    - (now - state.last_purge),
                ),
            },
            {
                "action": "mission_process",
                "next_in_s": max(
                    0,
                    self.config.mission_process_interval_s
                    - (now - state.last_mission_process),
                ),
            },
            {
                "action": "training_check",
                "next_in_s": max(
                    0,
                    self.config.training_check_interval_s
                    - (now - state.last_training_check),
                ),
            },
            {
                "action": "evaluation",
                "next_in_s": max(
                    0,
                    self.config.evaluation_interval_s
                    - (now - state.last_evaluation),
                ),
            },
            {
                "action": "knowledge_acquire",
                "next_in_s": max(
                    0,
                    self.config.knowledge_acquire_interval_s
                    - (now - state.last_knowledge_acquire),
                ),
            },
            {
                "action": "snapshot",
                "next_in_s": max(
                    0,
                    self.config.snapshot_interval_s
                    - (now - state.last_snapshot),
                ),
            },
            {
                "action": "self_repair_check",
                "next_in_s": max(
                    0,
                    self.config.self_repair_check_interval_s
                    - (now - state.last_self_repair_check),
                ),
            },
            {
                "action": "drive_report",
                "next_in_s": max(
                    0,
                    self.config.drive_report_interval_s
                    - (now - state.last_drive_report),
                ),
            },
            {
                "action": "cold_archive",
                "next_in_s": max(
                    0,
                    self.config.cold_archive_interval_s
                    - (now - state.last_cold_archive),
                ),
            },
            {
                "action": "retention",
                "next_in_s": max(
                    0,
                    self.config.retention_interval_s
                    - (now - state.last_retention),
                ),
            },
        ]
        actions.sort(key=lambda a: a["next_in_s"])
        return actions

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
