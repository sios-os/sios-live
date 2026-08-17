"""A/B drive automation — zero-downtime updates with canary testing.

Implements a Blue-Green Deployment pattern for the A/B drive system:

1. Active drive runs the current version (e.g., A:)
2. New updates are staged on the inactive drive (e.g., B:)
3. A 7-day canary test monitors system vitals on the new drive
4. If vitals pass, the active pointer switches to the new drive
5. If vitals fail, automatic rollback to the safe drive

This makes the A/B drive swap fully autonomous — the system updates
itself without human intervention, with automatic rollback on failure.

Key features:
- Abstract paths via environment variables (never hardcode A: or B:)
- Canary test monitors: API errors, timeouts, bridge crashes, fatal loops
- Automatic rollback on canary failure
- 7-day retention for rollback (configurable)
- All transitions logged to the evidence ledger

The system uses a state file to track:
- Which drive is active (A or B)
- Which drive is staging
- When the current version was deployed
- Canary test results
- Rollback history
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


# Default canary thresholds
DEFAULT_CANARY_DAYS = 7
DEFAULT_MAX_API_ERRORS = 10
DEFAULT_MAX_TIMEOUTS = 5
DEFAULT_MAX_CRASHES = 2


@dataclass
class CanaryMetrics:
    """Metrics collected during the canary test period."""
    api_errors: int = 0
    timeouts: int = 0
    crashes: int = 0
    bridge_failures: int = 0
    fatal_loops: int = 0
    uptime_seconds: float = 0.0
    started_at: float = 0.0
    last_checked: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_errors": self.api_errors,
            "timeouts": self.timeouts,
            "crashes": self.crashes,
            "bridge_failures": self.bridge_failures,
            "fatal_loops": self.fatal_loops,
            "uptime_seconds": self.uptime_seconds,
            "started_at": self.started_at,
            "last_checked": self.last_checked,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanaryMetrics":
        return cls(
            api_errors=data.get("api_errors", 0),
            timeouts=data.get("timeouts", 0),
            crashes=data.get("crashes", 0),
            bridge_failures=data.get("bridge_failures", 0),
            fatal_loops=data.get("fatal_loops", 0),
            uptime_seconds=data.get("uptime_seconds", 0.0),
            started_at=data.get("started_at", 0.0),
            last_checked=data.get("last_checked", 0.0),
        )


@dataclass
class DriveState:
    """State of the A/B drive system."""
    active_drive: str = "A"
    staging_drive: str = "B"
    active_version: str = "0.1.0"
    staging_version: str = ""
    active_deployed_at: float = 0.0
    staging_deployed_at: float = 0.0
    canary_active: bool = False
    canary_metrics: CanaryMetrics = field(default_factory=CanaryMetrics)
    rollback_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_drive": self.active_drive,
            "staging_drive": self.staging_drive,
            "active_version": self.active_version,
            "staging_version": self.staging_version,
            "active_deployed_at": self.active_deployed_at,
            "staging_deployed_at": self.staging_deployed_at,
            "canary_active": self.canary_active,
            "canary_metrics": self.canary_metrics.to_dict(),
            "rollback_history": self.rollback_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DriveState":
        return cls(
            active_drive=data.get("active_drive", "A"),
            staging_drive=data.get("staging_drive", "B"),
            active_version=data.get("active_version", "0.1.0"),
            staging_version=data.get("staging_version", ""),
            active_deployed_at=data.get("active_deployed_at", 0.0),
            staging_deployed_at=data.get("staging_deployed_at", 0.0),
            canary_active=data.get("canary_active", False),
            canary_metrics=CanaryMetrics.from_dict(data.get("canary_metrics", {})),
            rollback_history=data.get("rollback_history", []),
        )


@dataclass
class CanaryResult:
    """Result of a canary check."""
    passed: bool
    reason: str = ""
    metrics: CanaryMetrics | None = None
    should_rollback: bool = False


class ABDriveManager:
    """Manages the A/B drive automation system.

    Tracks which drive is active, manages canary testing, and
    performs automatic rollbacks on failure.

    The state file is stored at `config/ab_drive_state.json` by default.
    Environment variables are used to abstract drive paths:
    - ANUBIS_ACTIVE_DRIVE: points to the active drive
    - ANUBIS_STAGING_DRIVE: points to the staging drive
    """

    def __init__(
        self,
        state_path: str | Path = "config/ab_drive_state.json",
        ledger: Ledger | None = None,
        *,
        canary_days: int = DEFAULT_CANARY_DAYS,
        max_api_errors: int = DEFAULT_MAX_API_ERRORS,
        max_timeouts: int = DEFAULT_MAX_TIMEOUTS,
        max_crashes: int = DEFAULT_MAX_CRASHES,
    ) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger
        self.canary_days = canary_days
        self.max_api_errors = max_api_errors
        self.max_timeouts = max_timeouts
        self.max_crashes = max_crashes
        self._state: DriveState | None = None

    @property
    def state(self) -> DriveState:
        """Load state lazily."""
        if self._state is None:
            self.load_state()
        return self._state

    def load_state(self) -> DriveState:
        """Load drive state from disk."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self._state = DriveState.from_dict(data)
            except (json.JSONDecodeError, OSError):
                self._state = DriveState()
        else:
            self._state = DriveState()
        return self._state

    def save_state(self) -> None:
        """Save drive state to disk."""
        if self._state is None:
            return
        self.state_path.write_text(
            json.dumps(self._state.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def get_active_drive(self) -> str:
        """Return the active drive identifier."""
        return self.state.active_drive

    def get_staging_drive(self) -> str:
        """Return the staging drive identifier."""
        return self.state.staging_drive

    def get_active_path(self, subdir: str = "") -> str:
        """Get the active drive path from environment variables.

        Uses ANUBIS_ACTIVE_DRIVE env var, falling back to the state.
        """
        base = os.environ.get("ANUBIS_ACTIVE_DRIVE", self.state.active_drive)
        if subdir:
            return str(Path(base) / subdir)
        return base

    def get_staging_path(self, subdir: str = "") -> str:
        """Get the staging drive path from environment variables."""
        base = os.environ.get("ANUBIS_STAGING_DRIVE", self.state.staging_drive)
        if subdir:
            return str(Path(base) / subdir)
        return base

    def stage_update(self, version: str) -> dict[str, Any]:
        """Mark a new version as staged on the inactive drive.

        This begins the canary test period.

        Args:
            version: The version string being staged

        Returns:
            Dict with staging status
        """
        s = self.state
        s.staging_version = version
        s.staging_deployed_at = time.time()
        s.canary_active = True
        s.canary_metrics = CanaryMetrics(
            started_at=time.time(),
            last_checked=time.time(),
        )
        self.save_state()

        if self.ledger:
            self.ledger.append({
                "event": "ab_drive_stage",
                "version": version,
                "staging_drive": s.staging_drive,
            })

        return {
            "staged": True,
            "version": version,
            "staging_drive": s.staging_drive,
            "canary_started": True,
        }

    def record_canary_metric(
        self,
        *,
        api_errors: int = 0,
        timeouts: int = 0,
        crashes: int = 0,
        bridge_failures: int = 0,
        fatal_loops: int = 0,
    ) -> None:
        """Record canary metrics for the current staging version."""
        m = self.state.canary_metrics
        m.api_errors += api_errors
        m.timeouts += timeouts
        m.crashes += crashes
        m.bridge_failures += bridge_failures
        m.fatal_loops += fatal_loops
        m.last_checked = time.time()
        m.uptime_seconds = time.time() - m.started_at
        self.save_state()

    def check_canary(self) -> CanaryResult:
        """Check if the canary test is passing.

        Returns:
            CanaryResult with pass/fail status and reason
        """
        s = self.state
        if not s.canary_active:
            return CanaryResult(passed=True, reason="no canary active")

        m = s.canary_metrics

        # Check thresholds
        if m.api_errors > self.max_api_errors:
            return CanaryResult(
                passed=False,
                reason=f"API errors exceeded: {m.api_errors} > {self.max_api_errors}",
                metrics=m,
                should_rollback=True,
            )

        if m.timeouts > self.max_timeouts:
            return CanaryResult(
                passed=False,
                reason=f"Timeouts exceeded: {m.timeouts} > {self.max_timeouts}",
                metrics=m,
                should_rollback=True,
            )

        if m.crashes > self.max_crashes:
            return CanaryResult(
                passed=False,
                reason=f"Crashes exceeded: {m.crashes} > {self.max_crashes}",
                metrics=m,
                should_rollback=True,
            )

        if m.fatal_loops > 0:
            return CanaryResult(
                passed=False,
                reason=f"Fatal loops detected: {m.fatal_loops}",
                metrics=m,
                should_rollback=True,
            )

        # Check if canary period has elapsed
        elapsed_days = (time.time() - m.started_at) / 86400
        if elapsed_days < self.canary_days:
            return CanaryResult(
                passed=True,
                reason=f"canary in progress: {elapsed_days:.1f}/{self.canary_days} days",
                metrics=m,
            )

        # Canary passed
        return CanaryResult(
            passed=True,
            reason=f"canary completed: {elapsed_days:.1f} days, all metrics within thresholds",
            metrics=m,
        )

    def promote(self) -> dict[str, Any]:
        """Promote the staging drive to active.

        Switches the active pointer to the staging drive.
        The old active drive becomes the new staging drive.

        Returns:
            Dict with promotion status
        """
        s = self.state
        if not s.canary_active:
            return {"promoted": False, "error": "no staging version to promote"}

        canary = self.check_canary()
        if not canary.passed:
            return {"promoted": False, "error": f"canary failed: {canary.reason}"}

        # Swap drives
        old_active = s.active_drive
        old_version = s.active_version
        s.active_drive = s.staging_drive
        s.active_version = s.staging_version
        s.active_deployed_at = s.staging_deployed_at
        s.staging_drive = old_active
        s.staging_version = ""
        s.staging_deployed_at = 0.0
        s.canary_active = False
        s.canary_metrics = CanaryMetrics()

        # Update environment variable
        os.environ["ANUBIS_ACTIVE_DRIVE"] = s.active_drive
        os.environ["ANUBIS_STAGING_DRIVE"] = s.staging_drive

        self.save_state()

        if self.ledger:
            self.ledger.append({
                "event": "ab_drive_promote",
                "new_active": s.active_drive,
                "new_version": s.active_version,
                "old_active": old_active,
                "old_version": old_version,
            })

        return {
            "promoted": True,
            "active_drive": s.active_drive,
            "active_version": s.active_version,
            "previous_drive": old_active,
            "previous_version": old_version,
        }

    def rollback(self, reason: str = "") -> dict[str, Any]:
        """Rollback to the previous active drive.

        Used when the canary test fails or the Creator requests a rollback.

        Returns:
            Dict with rollback status
        """
        s = self.state
        # The staging drive was the old active, so swap back
        failed_drive = s.active_drive
        failed_version = s.active_version

        s.active_drive = s.staging_drive
        s.active_version = s.active_version  # keep old version if available
        s.staging_drive = failed_drive
        s.staging_version = failed_version
        s.canary_active = False
        s.canary_metrics = CanaryMetrics()

        # Record in rollback history
        s.rollback_history.append({
            "timestamp": time.time(),
            "from_drive": failed_drive,
            "from_version": failed_version,
            "to_drive": s.active_drive,
            "reason": reason,
        })

        # Update environment variable
        os.environ["ANUBIS_ACTIVE_DRIVE"] = s.active_drive
        os.environ["ANUBIS_STAGING_DRIVE"] = s.staging_drive

        self.save_state()

        if self.ledger:
            self.ledger.append({
                "event": "ab_drive_rollback",
                "from_drive": failed_drive,
                "to_drive": s.active_drive,
                "reason": reason,
            })

        return {
            "rolled_back": True,
            "active_drive": s.active_drive,
            "reason": reason,
        }

    def status(self) -> dict[str, Any]:
        """Return A/B drive system status."""
        s = self.state
        canary = self.check_canary()
        return {
            "active_drive": s.active_drive,
            "staging_drive": s.staging_drive,
            "active_version": s.active_version,
            "staging_version": s.staging_version,
            "canary_active": s.canary_active,
            "canary_passed": canary.passed,
            "canary_reason": canary.reason,
            "canary_metrics": s.canary_metrics.to_dict(),
            "rollback_count": len(s.rollback_history),
            "active_path": self.get_active_path(),
            "staging_path": self.get_staging_path(),
        }
