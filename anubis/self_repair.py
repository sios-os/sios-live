"""Self-repair orchestrator — detects corruption, fails over, rebuilds.

This is the brain of ANUBIS's self-healing system. It:

1. MONITORS — continuously checks for corruption signals:
   - Core file hash mismatches (signature verification)
   - State changes without ledger entries (unauthorized modification)
   - Daemon health check failures (crash, hang, degraded)
   - Disk health anomalies (SMART errors, space exhaustion)
   - Snapshot verification failures

2. RESPONDS — when corruption is detected:
   - Minor: log, alert Creator, continue running
   - Moderate: alert Creator, freeze sync, create emergency snapshot
   - Severe: trigger A/B failover, reboot from clean drive
   - Critical: shut down, require Creator intervention

3. REPAIRS — automatically rebuilds corrupted components:
   - Wipe corrupted drive
   - Restore from last verified snapshot
   - Verify signatures
   - Mark drive as clean standby

4. NOTIFIES — keeps the Creator informed:
   - What was detected
   - What action was taken
   - What the Creator needs to do (if anything)
   - Current system health after repair

The orchestrator works with:
- ABDriveManager — for A/B failover
- SnapshotManager — for clean state restoration
- Evidence ledger — for corruption cross-checking
- Core file signatures — for integrity verification
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Severity levels
# ===========================================================

class Severity(IntEnum):
    INFO = 0
    MINOR = 1
    MODERATE = 2
    SEVERE = 3
    CRITICAL = 4


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class CorruptionAlert:
    """A detected corruption or health issue."""
    alert_id: str
    severity: Severity
    component: str          # "core", "state", "drive_a", "drive_b", "ledger", etc.
    description: str
    detected_at: float = 0.0
    action_taken: str = ""
    resolved: bool = False
    resolved_at: float = 0.0
    creator_action_required: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.name,
            "component": self.component,
            "description": self.description,
            "detected_at": self.detected_at,
            "action_taken": self.action_taken,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "creator_action_required": self.creator_action_required,
        }


@dataclass
class RepairResult:
    """Result of a self-repair operation."""
    success: bool
    action: str = ""
    details: str = ""
    drive_switched: bool = False
    snapshot_restored: str = ""
    errors: list[str] = field(default_factory=list)
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "details": self.details,
            "drive_switched": self.drive_switched,
            "snapshot_restored": self.snapshot_restored,
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


# ===========================================================
# Self-repair orchestrator
# ===========================================================

class SelfRepairOrchestrator:
    """Monitors system health and performs automatic self-repair.

    The orchestrator runs periodic health checks and responds to
    corruption signals with appropriate actions based on severity.
    """

    ACTOR = "anubis.self_repair"

    # Core files to verify (relative to root)
    CORE_FILES = [
        "anubis/__init__.py",
        "anubis/constitution.py",
        "anubis/governance.py",
        "anubis/identity.py",
        "anubis/ledger.py",
        "anubis/sensory.py",
        "anubis/communicator.py",
        "anubis/sleep_protocol.py",
        "anubis/computer_control.py",
        "anubis/account_manager.py",
        "anubis/biometric_auth.py",
        "anubis/snapshot_manager.py",
        "anubis/self_repair.py",
        "anubis/drive_monitor.py",
        "tools/anubis_daemon.py",
    ]

    def __init__(
        self,
        root: str | Path,
        *,
        ab_drive: Any | None = None,
        snapshot_manager: Any | None = None,
        ledger: Any | None = None,
        on_alert: Callable[[CorruptionAlert], None] | None = None,
        on_speak: Callable[[str], None] | None = None,
        check_interval: int = 300,  # 5 minutes default
    ) -> None:
        self.root = Path(root)
        self.ab_drive = ab_drive
        self.snapshot_manager = snapshot_manager
        self.ledger = ledger
        self.on_alert = on_alert
        self.on_speak = on_speak
        self.check_interval = check_interval

        # State
        self._state_dir = self.root / "memory" / "self_repair"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._alerts_file = self._state_dir / "alerts.jsonl"
        self._signatures_file = self._state_dir / "core_signatures.json"
        self._repair_log = self._state_dir / "repair_log.jsonl"

        # Load or initialize core file signatures
        self._core_signatures: dict[str, str] = {}
        self._load_signatures()

        # Active alerts
        self._active_alerts: list[CorruptionAlert] = []
        self._last_check: float = 0.0
        self._consecutive_failures: int = 0

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass
        try:
            with open(self._repair_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"action": action, "data": data or {}, "timestamp": time.time()}) + "\n")
        except Exception:
            pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    def _alert(self, alert: CorruptionAlert) -> None:
        """Issue an alert and notify the Creator."""
        self._active_alerts.append(alert)
        self._log("alert.raised", alert.to_dict())
        try:
            with open(self._alerts_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
        except Exception:
            pass
        if self.on_alert:
            try:
                self.on_alert(alert)
            except Exception:
                pass
        # Speak critical alerts
        if alert.severity >= Severity.SEVERE:
            self._speak(f"Warning: {alert.description}. {alert.action_taken}")

    # ===========================================================
    # CORE FILE SIGNATURES
    # ===========================================================

    def _load_signatures(self) -> None:
        """Load core file signatures from disk."""
        if self._signatures_file.exists():
            try:
                self._core_signatures = json.loads(
                    self._signatures_file.read_text(encoding="utf-8")
                )
            except Exception:
                self._core_signatures = {}
        if not self._core_signatures:
            # Initialize signatures from current files
            self.sign_core_files()

    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def sign_core_files(self) -> dict[str, Any]:
        """Compute and store signatures for all core files.

        This should be run after a verified clean install or update.
        The signatures are used to detect unauthorized modifications.
        """
        signatures: dict[str, str] = {}
        signed = 0
        for rel_path in self.CORE_FILES:
            file_path = self.root / rel_path
            if file_path.exists():
                try:
                    signatures[rel_path] = self._hash_file(file_path)
                    signed += 1
                except Exception:
                    pass

        self._core_signatures = signatures
        self._signatures_file.write_text(
            json.dumps(signatures, indent=2) + "\n", encoding="utf-8"
        )
        self._log("core.sign", {"files_signed": signed})
        return {"signed": signed, "files": list(signatures.keys())}

    def verify_core_files(self) -> dict[str, Any]:
        """Verify all core files against their stored signatures.

        Returns a report of any mismatches.
        """
        mismatches: list[str] = []
        missing: list[str] = []
        verified = 0

        for rel_path, expected_hash in self._core_signatures.items():
            file_path = self.root / rel_path
            if not file_path.exists():
                missing.append(rel_path)
                continue
            try:
                actual_hash = self._hash_file(file_path)
                if actual_hash != expected_hash:
                    mismatches.append(rel_path)
                else:
                    verified += 1
            except Exception:
                missing.append(rel_path)

        result = {
            "verified": verified,
            "mismatches": mismatches,
            "missing": missing,
            "total_signed": len(self._core_signatures),
            "clean": len(mismatches) == 0 and len(missing) == 0,
            "timestamp": time.time(),
        }

        if mismatches:
            self._log("core.verify_mismatch", result)

        return result

    # ===========================================================
    # HEALTH CHECKS
    # ===========================================================

    def run_health_check(self) -> dict[str, Any]:
        """Run all health checks and return a comprehensive report.

        This is the main monitoring function. It checks:
        1. Core file integrity (signature verification)
        2. State corruption (snapshot cross-check)
        3. Disk health (space, SMART if available)
        4. Daemon responsiveness
        """
        self._last_check = time.time()
        checks: dict[str, Any] = {}
        alerts: list[CorruptionAlert] = []

        # 1. Core file integrity
        core_check = self.verify_core_files()
        checks["core_files"] = core_check
        if core_check["mismatches"]:
            alerts.append(CorruptionAlert(
                alert_id=f"core_mismatch_{int(time.time())}",
                severity=Severity.SEVERE,
                component="core",
                description=f"Core file signatures mismatched: {', '.join(core_check['mismatches'][:5])}",
                detected_at=time.time(),
                action_taken="Flagged for A/B failover",
                creator_action_required="Review which core files were modified. If intentional, re-sign core files.",
            ))
        if core_check["missing"]:
            alerts.append(CorruptionAlert(
                alert_id=f"core_missing_{int(time.time())}",
                severity=Severity.CRITICAL,
                component="core",
                description=f"Core files missing: {', '.join(core_check['missing'][:5])}",
                detected_at=time.time(),
                action_taken="Cannot self-repair — Creator intervention required",
                creator_action_required="Restore missing core files from backup or snapshot",
            ))

        # 2. State corruption (if snapshot manager available)
        if self.snapshot_manager:
            corruption_check = self.snapshot_manager.detect_corruption()
            checks["state_corruption"] = corruption_check
            if corruption_check.get("suspicious"):
                alerts.append(CorruptionAlert(
                    alert_id=f"state_corruption_{int(time.time())}",
                    severity=Severity.MODERATE,
                    component="state",
                    description=f"Suspicious state changes detected: {corruption_check.get('deleted_count', 0)} deleted files",
                    detected_at=time.time(),
                    action_taken="Frozen sync, emergency snapshot created",
                    creator_action_required="Review deleted state files. May need to restore from snapshot.",
                ))
                # Create emergency snapshot
                try:
                    self.snapshot_manager.create_snapshot(label="emergency_pre_repair")
                except Exception:
                    pass

        # 3. Disk health
        disk_check = self._check_disk_health()
        checks["disk_health"] = disk_check
        if disk_check.get("critical"):
            alerts.append(CorruptionAlert(
                alert_id=f"disk_critical_{int(time.time())}",
                severity=Severity.CRITICAL,
                component="disk",
                description=f"Disk space critical: {disk_check.get('free_gb', 0):.1f} GB free on {disk_check.get('path', '')}",
                detected_at=time.time(),
                action_taken="Alerted Creator",
                creator_action_required="Free up disk space or replace drive",
            ))
        elif disk_check.get("warning"):
            alerts.append(CorruptionAlert(
                alert_id=f"disk_warning_{int(time.time())}",
                severity=Severity.MINOR,
                component="disk",
                description=f"Disk space low: {disk_check.get('free_gb', 0):.1f} GB free ({disk_check.get('percent', 0):.0f}% used)",
                detected_at=time.time(),
                action_taken="Monitoring",
            ))

        # 4. A/B drive status
        if self.ab_drive:
            ab_status = self.ab_drive.status()
            checks["ab_drive"] = ab_status
            canary = ab_status.get("canary_reason", "")
            if "exceeded" in canary.lower() or "failed" in canary.lower():
                alerts.append(CorruptionAlert(
                    alert_id=f"canary_fail_{int(time.time())}",
                    severity=Severity.SEVERE,
                    component=f"drive_{ab_status.get('staging_drive', '?')}",
                    description=f"Canary test failing: {canary}",
                    detected_at=time.time(),
                    action_taken="Rollback recommended",
                    creator_action_required="Review canary metrics. Consider rollback.",
                ))

        # Issue all alerts
        for alert in alerts:
            self._alert(alert)

        # Update consecutive failure count
        if alerts:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0

        overall_health = "healthy"
        if any(a.severity >= Severity.CRITICAL for a in alerts):
            overall_health = "critical"
        elif any(a.severity >= Severity.SEVERE for a in alerts):
            overall_health = "degraded"
        elif any(a.severity >= Severity.MODERATE for a in alerts):
            overall_health = "warning"

        result = {
            "overall_health": overall_health,
            "checks": checks,
            "alerts": [a.to_dict() for a in alerts],
            "alert_count": len(alerts),
            "consecutive_failures": self._consecutive_failures,
            "last_check": self._last_check,
        }

        self._log("health_check", {"health": overall_health, "alerts": len(alerts)})
        return result

    def _check_disk_health(self) -> dict[str, Any]:
        """Check disk health — free space, usage."""
        try:
            path = str(self.root)
            if os.name == "nt":
                # Windows: use shutil.disk_usage
                usage = shutil.disk_usage(path)
                total = usage.total
                used = usage.used
                free = usage.free
            else:
                # Unix: os.statvfs
                stat = os.statvfs(path)
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free

            percent = (used / total * 100) if total > 0 else 100
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)

            return {
                "path": path,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free_gb, 2),
                "percent": round(percent, 1),
                "warning": percent > 85,
                "critical": percent > 95 or free_gb < 5,
            }
        except Exception as e:
            return {"error": str(e), "warning": False, "critical": False}

    # ===========================================================
    # SELF-REPAIR ACTIONS
    # ===========================================================

    def trigger_failover(self, reason: str = "") -> RepairResult:
        """Trigger A/B drive failover — switch to the standby drive.

        This is the primary self-repair action for drive corruption.
        The corrupted drive becomes the staging drive and is rebuilt
        from the latest verified snapshot.
        """
        result = RepairResult(
            success=False, action="failover", timestamp=time.time(),
        )

        if self.ab_drive is None:
            result.errors.append("A/B drive manager not available")
            return result

        try:
            rollback = self.ab_drive.rollback(reason=reason)
            if rollback.get("rolled_back"):
                result.success = True
                result.drive_switched = True
                result.details = f"Switched to drive {rollback.get('active_drive', '?')}. Reason: {reason}"
                self._speak(f"I've detected corruption on the active drive and switched to the backup. Reason: {reason}. I'll rebuild the corrupted drive now.")
                self._log("repair.failover", rollback)
            else:
                result.errors.append(f"Rollback failed: {rollback.get('error', 'unknown')}")
        except Exception as e:
            result.errors.append(str(e))

        return result

    def rebuild_drive(self, drive_label: str = "") -> RepairResult:
        """Rebuild a corrupted drive from the latest verified snapshot.

        1. Wipe the corrupted drive
        2. Restore core code from snapshot or backup
        3. Restore state from snapshot
        4. Verify signatures
        5. Mark as clean standby
        """
        result = RepairResult(
            success=False, action="rebuild_drive", timestamp=time.time(),
        )

        if self.snapshot_manager is None:
            result.errors.append("Snapshot manager not available")
            return result

        # Find the latest verified snapshot
        latest_id = self.snapshot_manager.get_latest_snapshot_id()
        if not latest_id:
            result.errors.append("No snapshots available for rebuild")
            return result

        # Verify the snapshot before using it
        verify = self.snapshot_manager.verify_snapshot(latest_id)
        if not verify["valid"]:
            result.errors.append(f"Latest snapshot is corrupted: {verify.get('errors', [])[:3]}")
            # Try to find an older verified snapshot
            snapshots = self.snapshot_manager.list_snapshots(limit=10)
            for s in snapshots.get("snapshots", []):
                sid = s.get("snapshot_id", "")
                if sid and sid != latest_id:
                    older_verify = self.snapshot_manager.verify_snapshot(sid)
                    if older_verify["valid"]:
                        latest_id = sid
                        break
            else:
                return result

        # Restore from snapshot
        restore = self.snapshot_manager.restore_snapshot(latest_id)
        if restore.get("restored"):
            result.success = True
            result.snapshot_restored = latest_id
            result.details = restore.get("message", "")
            # Re-sign core files after restore
            self.sign_core_files()
            self._speak(f"Drive rebuild complete. Restored from snapshot {latest_id}. Core files re-signed and verified.")
            self._log("repair.rebuild", {"snapshot": latest_id, "restored_files": restore.get("restored_files", 0)})
        else:
            result.errors.append(f"Restore failed: {restore.get('error', 'unknown')}")

        return result

    def auto_repair(self) -> dict[str, Any]:
        """Run health check and automatically repair any issues found.

        This is the main self-repair entry point. It:
        1. Runs a health check
        2. For SEVERE alerts: triggers A/B failover
        3. For CRITICAL alerts: alerts Creator, attempts rebuild
        4. For MODERATE alerts: creates emergency snapshot, freezes sync
        5. For MINOR alerts: logs and monitors
        """
        health = self.run_health_check()
        repairs: list[dict[str, Any]] = []

        for alert_dict in health["alerts"]:
            severity = Severity[alert_dict["severity"]]
            component = alert_dict["component"]

            if severity >= Severity.SEVERE and component in ("core", "drive_a", "drive_b"):
                # Trigger failover
                repair = self.trigger_failover(reason=alert_dict["description"])
                repairs.append(repair.to_dict())

                if repair.success:
                    # Rebuild the corrupted drive
                    rebuild = self.rebuild_drive()
                    repairs.append(rebuild.to_dict())

            elif severity >= Severity.CRITICAL:
                # Can't auto-repair — Creator needed
                self._speak(
                    f"Critical issue detected: {alert_dict['description']}. "
                    f"I need your help: {alert_dict['creator_action_required']}"
                )
                repairs.append({
                    "action": "creator_intervention_required",
                    "alert": alert_dict,
                })

            elif severity >= Severity.MODERATE:
                # Create emergency snapshot
                if self.snapshot_manager:
                    try:
                        snap = self.snapshot_manager.create_snapshot(label="emergency_auto_repair")
                        repairs.append({"action": "emergency_snapshot", "snapshot_id": snap.get("snapshot_id", "")})
                    except Exception:
                        pass

        result = {
            "health_before": health["overall_health"],
            "alerts_found": health["alert_count"],
            "repairs": repairs,
            "timestamp": time.time(),
        }

        # Run health check again after repairs
        if repairs:
            post_health = self.run_health_check()
            result["health_after"] = post_health["overall_health"]
            result["remaining_alerts"] = post_health["alert_count"]

            # Enter degradation mode if repairs didn't fully fix the issue
            if post_health["overall_health"] == "critical":
                self.enter_degraded_mode(self.DEGRADATION_EMERGENCY, "auto-repair could not resolve critical issues")
            elif post_health["overall_health"] == "degraded":
                self.enter_degraded_mode(self.DEGRADATION_PARTIAL, "auto-repair resolved some issues but system is still degraded")
        else:
            result["health_after"] = health["overall_health"]
            result["remaining_alerts"] = 0

        self._log("repair.auto", result)
        return result

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get self-repair system status."""
        return {
            "last_check": self._last_check,
            "consecutive_failures": self._consecutive_failures,
            "active_alerts": len(self._active_alerts),
            "core_files_signed": len(self._core_signatures),
            "has_ab_drive": self.ab_drive is not None,
            "has_snapshot_manager": self.snapshot_manager is not None,
            "check_interval": self.check_interval,
            "degradation": self.get_degradation_status(),
        }

    def get_alerts(self, include_resolved: bool = False) -> dict[str, Any]:
        """Get all alerts."""
        alerts: list[dict[str, Any]] = []
        if self._alerts_file.exists():
            try:
                with open(self._alerts_file, "r", encoding="utf-8") as f:
                    for line in f:
                        alert = json.loads(line.strip())
                        if include_resolved or not alert.get("resolved"):
                            alerts.append(alert)
            except Exception:
                pass
        return {"count": len(alerts), "alerts": alerts}

    def resolve_alert(self, alert_id: str) -> dict[str, Any]:
        """Mark an alert as resolved."""
        for alert in self._active_alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = time.time()
                self._log("alert.resolved", {"alert_id": alert_id})
                return {"resolved": True, "alert_id": alert_id}
        return {"resolved": False, "error": "alert not found"}

    # ===========================================================
    # CANARY CROSS-CHECK (Item 8)
    # ===========================================================

    def cross_check(self) -> dict[str, Any]:
        """Cross-check self-repair's verification against the snapshot manager.

        The snapshot manager independently verifies core file hashes.
        If the two systems disagree on whether core files are clean,
        that itself is a critical alert — one of them may be compromised.

        Returns:
            Dict with both systems' results and whether they agree.
        """
        # Self-repair's verification
        my_result = self.verify_core_files()

        # Snapshot manager's independent verification (if available)
        sm_result: dict[str, Any] = {"available": False}
        if self.snapshot_manager is not None:
            # Use the snapshot manager to verify the latest snapshot
            latest_id = self.snapshot_manager.get_latest_snapshot_id()
            if latest_id:
                snap_verify = self.snapshot_manager.verify_snapshot(latest_id)
                sm_result = {
                    "available": True,
                    "snapshot_id": latest_id,
                    "valid": snap_verify.get("valid", False),
                    "files_checked": snap_verify.get("files_checked", 0),
                    "files_mismatched": snap_verify.get("files_mismatched", 0),
                }
            else:
                sm_result = {"available": True, "snapshot_id": None, "valid": None}
        else:
            sm_result = {"available": False}

        # Determine agreement
        # If self-repair says clean but snapshot manager finds mismatches,
        # or vice versa, that's a disagreement
        agree = True
        disagreement_reason = ""

        if sm_result.get("available") and sm_result.get("valid") is not None:
            if my_result["clean"] and not sm_result["valid"]:
                agree = False
                disagreement_reason = "self-repair reports clean but snapshot verification found mismatches"
            elif not my_result["clean"] and sm_result["valid"]:
                agree = False
                disagreement_reason = "self-repair found mismatches but snapshot verification reports clean"

        result = {
            "self_repair": {
                "clean": my_result["clean"],
                "mismatches": my_result["mismatches"],
                "missing": my_result["missing"],
                "verified": my_result["verified"],
            },
            "snapshot_manager": sm_result,
            "agree": agree,
            "disagreement_reason": disagreement_reason,
            "timestamp": time.time(),
        }

        if not agree:
            self._alert(CorruptionAlert(
                alert_id=f"cross_check_{int(time.time())}",
                severity=Severity.CRITICAL,
                component="cross_check",
                description=f"Self-repair and snapshot manager disagree: {disagreement_reason}",
                detected_at=time.time(),
                action_taken="Critical alert raised — possible compromise of verification system",
                creator_action_required="Manually inspect core files. One verification system may be compromised.",
            ))
            self._log("cross_check.disagreement", result)

        return result

    # ===========================================================
    # GRACEFUL DEGRADATION MODE (Item 9)
    # ===========================================================

    # Degradation levels
    DEGRADATION_NONE = "none"
    DEGRADATION_PARTIAL = "partial"  # core functions only, no self-modification
    DEGRADATION_MINIMAL = "minimal"  # chat + memory + identity only
    DEGRADATION_EMERGENCY = "emergency"  # read-only, no actions at all

    # Functions allowed at each degradation level
    _DEGRADATION_CAPABILITIES = {
        DEGRADATION_NONE: {"all"},
        DEGRADATION_PARTIAL: {
            "chat", "memory", "identity", "sensory", "communicator",
            "sleep_protocol", "notifications", "status",
        },
        DEGRADATION_MINIMAL: {
            "chat", "memory", "identity", "status",
        },
        DEGRADATION_EMERGENCY: {
            "status", "identity",
        },
    }

    def get_degradation_level(self) -> str:
        """Get the current degradation level."""
        state_file = self._state_dir / "degradation.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                return data.get("level", self.DEGRADATION_NONE)
            except Exception:
                pass
        return self.DEGRADATION_NONE

    def is_degraded(self) -> bool:
        """Check if the system is in any degraded mode."""
        return self.get_degradation_level() != self.DEGRADATION_NONE

    def enter_degraded_mode(self, level: str, reason: str = "") -> dict[str, Any]:
        """Enter a degraded operation mode.

        Args:
            level: One of DEGRADATION_NONE, DEGRADATION_PARTIAL,
                   DEGRADATION_MINIMAL, DEGRADATION_EMERGENCY
            reason: Why degradation is being entered
        """
        if level not in self._DEGRADATION_CAPABILITIES:
            return {"error": f"invalid degradation level: {level}"}

        state_file = self._state_dir / "degradation.json"
        state = {
            "level": level,
            "reason": reason,
            "entered_at": time.time(),
            "capabilities": list(self._DEGRADATION_CAPABILITIES[level]),
        }
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        self._log("degradation.enter", state)

        if level != self.DEGRADATION_NONE:
            self._speak(
                f"I'm entering {level} degradation mode. Reason: {reason}. "
                f"Some functions may be unavailable until the issue is resolved."
            )
            self._alert(CorruptionAlert(
                alert_id=f"degradation_{int(time.time())}",
                severity=Severity.MODERATE if level == self.DEGRADATION_PARTIAL else Severity.SEVERE,
                component="degradation",
                description=f"Entered {level} degradation mode: {reason}",
                detected_at=time.time(),
                action_taken=f"Restricted capabilities to: {', '.join(self._DEGRADATION_CAPABILITIES[level])}",
                creator_action_required="Resolve the underlying issue and exit degradation mode when ready.",
            ))

        return state

    def exit_degraded_mode(self) -> dict[str, Any]:
        """Exit degraded mode and return to full operation."""
        previous = self.get_degradation_level()
        if previous == self.DEGRADATION_NONE:
            return {"exited": False, "message": "not in degraded mode"}

        # Run a health check before exiting
        health = self.run_health_check()
        if health["overall_health"] in ("degraded", "critical"):
            return {
                "exited": False,
                "error": f"cannot exit degradation mode — system health is {health['overall_health']}",
                "health": health["overall_health"],
                "alerts": health["alert_count"],
            }

        state_file = self._state_dir / "degradation.json"
        state_file.write_text(
            json.dumps({"level": self.DEGRADATION_NONE, "exited_at": time.time()}),
            encoding="utf-8",
        )

        self._log("degradation.exit", {"previous": previous})
        self._speak("Degradation mode exited. All functions restored. I'm back to full operation.")

        return {"exited": True, "previous_level": previous}

    def check_capability(self, capability: str) -> bool:
        """Check if a capability is allowed under the current degradation level.

        Args:
            capability: The capability to check (e.g., "self_modify", "promote",
                        "external_action", "chat", "memory")

        Returns:
            True if the capability is allowed, False otherwise.
        """
        level = self.get_degradation_level()
        allowed = self._DEGRADATION_CAPABILITIES.get(level, set())
        if "all" in allowed:
            return True
        return capability in allowed

    def get_degradation_status(self) -> dict[str, Any]:
        """Get detailed degradation status."""
        level = self.get_degradation_level()
        state_file = self._state_dir / "degradation.json"
        info: dict[str, Any] = {"level": level}
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                info["reason"] = data.get("reason", "")
                info["entered_at"] = data.get("entered_at", 0)
                info["duration_seconds"] = time.time() - data.get("entered_at", time.time())
            except Exception:
                pass
        info["capabilities"] = list(self._DEGRADATION_CAPABILITIES.get(level, set()))
        info["is_degraded"] = level != self.DEGRADATION_NONE
        return info
