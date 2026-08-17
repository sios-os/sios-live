"""Drive monitor — daily health report for A/B drives, storage, and cloud.

Generates a comprehensive daily report covering:

1. A/B DRIVE STATUS
   - Which drive is active / staging
   - Current version on each drive
   - Canary test status
   - Rollback history
   - Drive health (space, errors)

2. SNAPSHOT STATUS
   - Number of snapshots
   - Total snapshot storage
   - Latest snapshot timestamp and verification status
   - Retention policy status

3. CLOUD SYNC STATUS
   - Last sync time
   - Sync success/failure
   - Pending sync items
   - Cloud storage usage

4. DISK HEALTH
   - Free space on all drives
   - Usage percentages
   - Warning/critical thresholds
   - SMART data if available

5. POTENTIAL ISSUES
   - Drives running low on space
   - Snapshots not being created
   - Cloud sync failures
   - Drive errors or degradation
   - A/B canary test failures
   - Stale backups

The report is delivered as:
- A spoken briefing (via DEMON)
- A notification
- A structured data object for the phone app / API
- Written to the daily report log

The Creator can request it at any time:
- "Give me the drive report"
- "What's the status of my drives?"
- "Any issues with storage?"
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class DriveHealth:
    """Health information for a single drive or partition."""
    path: str
    label: str = ""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    percent_used: float = 0.0
    status: str = "unknown"  # healthy, warning, critical, unknown
    issues: list[str] = field(default_factory=list)
    # SMART / wear leveling data
    smart_available: bool = False
    smart_status: str = "unknown"  # ok, failing, unknown
    smart_wear_percent: float = -1.0  # -1 = unknown, 0-100 = wear level
    smart_temperature: float = -1.0  # Celsius, -1 = unknown
    smart_model: str = ""
    smart_serial: str = ""  # last 4 chars only for privacy
    smart_power_on_hours: float = -1.0
    estimated_lifespan_percent: float = -1.0  # remaining life, -1 = unknown

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "label": self.label,
            "total_gb": round(self.total_gb, 2),
            "used_gb": round(self.used_gb, 2),
            "free_gb": round(self.free_gb, 2),
            "percent_used": round(self.percent_used, 1),
            "status": self.status,
            "issues": self.issues,
            "smart_available": self.smart_available,
            "smart_status": self.smart_status,
            "smart_wear_percent": round(self.smart_wear_percent, 1) if self.smart_wear_percent >= 0 else -1,
            "smart_temperature": round(self.smart_temperature, 1) if self.smart_temperature >= 0 else -1,
            "smart_model": self.smart_model,
            "smart_serial": self.smart_serial,
            "smart_power_on_hours": self.smart_power_on_hours,
            "estimated_lifespan_percent": round(self.estimated_lifespan_percent, 1) if self.estimated_lifespan_percent >= 0 else -1,
        }


@dataclass
class DailyReport:
    """A complete daily drive and storage report."""
    report_id: str
    timestamp: float
    overall_status: str = "healthy"  # healthy, warning, critical
    drives: list[DriveHealth] = field(default_factory=list)
    ab_drive_status: dict[str, Any] = field(default_factory=dict)
    snapshot_status: dict[str, Any] = field(default_factory=dict)
    cloud_sync_status: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    spoken_briefing: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "drives": [d.to_dict() for d in self.drives],
            "ab_drive_status": self.ab_drive_status,
            "snapshot_status": self.snapshot_status,
            "cloud_sync_status": self.cloud_sync_status,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "spoken_briefing": self.spoken_briefing,
        }


# ===========================================================
# Drive monitor
# ===========================================================

class DriveMonitor:
    """Monitors drive health and generates daily reports.

    Can be called on demand or scheduled to run daily (e.g., as part
    of the good morning briefing or the autonomous scheduler).
    """

    ACTOR = "anubis.drive_monitor"

    # Thresholds
    DISK_WARNING_PERCENT = 85.0
    DISK_CRITICAL_PERCENT = 95.0
    DISK_CRITICAL_FREE_GB = 5.0
    SNAPSHOT_STALE_HOURS = 26  # alert if no snapshot in 26 hours
    CLOUD_STALE_HOURS = 48     # alert if no cloud sync in 48 hours

    def __init__(
        self,
        root: str | Path,
        *,
        ab_drive: Any | None = None,
        snapshot_manager: Any | None = None,
        cloud_sync: Any | None = None,
        ledger: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
        on_notify: Callable[[str, str], None] | None = None,
        extra_drives: list[str] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ab_drive = ab_drive
        self.snapshot_manager = snapshot_manager
        self.cloud_sync = cloud_sync
        self.ledger = ledger
        self.on_speak = on_speak
        self.on_notify = on_notify
        self.extra_drives = extra_drives or []

        self._state_dir = self.root / "memory" / "drive_monitor"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._reports_file = self._state_dir / "daily_reports.jsonl"

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

    def _notify(self, title: str, body: str) -> None:
        if self.on_notify:
            try:
                self.on_notify(title, body)
            except Exception:
                pass

    # ===========================================================
    # DRIVE HEALTH CHECKS
    # ===========================================================

    def _check_disk_usage(self, path: str, label: str = "") -> DriveHealth:
        """Check disk usage for a given path."""
        health = DriveHealth(path=path, label=label)
        try:
            if os.name == "nt":
                usage = shutil.disk_usage(path)
                total = usage.total
                used = usage.used
                free = usage.free
            else:
                stat = os.statvfs(path)
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free

            health.total_gb = total / (1024 ** 3)
            health.used_gb = used / (1024 ** 3)
            health.free_gb = free / (1024 ** 3)
            health.percent_used = (used / total * 100) if total > 0 else 100

            # Determine status
            if health.percent_used >= self.DISK_CRITICAL_PERCENT or health.free_gb < self.DISK_CRITICAL_FREE_GB:
                health.status = "critical"
                health.issues.append(f"Disk space critical: {health.free_gb:.1f} GB free ({health.percent_used:.0f}% used)")
            elif health.percent_used >= self.DISK_WARNING_PERCENT:
                health.status = "warning"
                health.issues.append(f"Disk space low: {health.free_gb:.1f} GB free ({health.percent_used:.0f}% used)")
            else:
                health.status = "healthy"

        except Exception as e:
            health.status = "unknown"
            health.issues.append(f"Could not check disk: {e}")

        # Check SMART data
        try:
            smart = self._check_smart_health(path)
            health.smart_available = smart.get("available", False)
            health.smart_status = smart.get("status", "unknown")
            health.smart_wear_percent = smart.get("wear_percent", -1.0)
            health.smart_temperature = smart.get("temperature", -1.0)
            health.smart_model = smart.get("model", "")
            health.smart_serial = smart.get("serial", "")
            health.smart_power_on_hours = smart.get("power_on_hours", -1.0)
            health.estimated_lifespan_percent = smart.get("estimated_lifespan", -1.0)

            # Adjust status based on SMART
            if health.smart_status == "failing":
                if health.status == "healthy":
                    health.status = "warning"
                health.issues.append(f"SMART reports drive failing: {health.smart_model}")
            elif health.estimated_lifespan_percent >= 0 and health.estimated_lifespan_percent < 10:
                if health.status == "healthy":
                    health.status = "warning"
                health.issues.append(
                    f"Drive lifespan critical: {health.estimated_lifespan_percent:.0f}% remaining"
                )
        except Exception:
            pass

        return health

    def _check_smart_health(self, path: str) -> dict[str, Any]:
        """Check SMART health data for the drive containing the given path.

        Uses smartctl on Linux and wmic/PowerShell on Windows.
        Returns degraded gracefully if tools are not available.
        """
        result: dict[str, Any] = {"available": False}

        try:
            if os.name == "nt":
                # Windows: use PowerShell to get physical disk info
                cmd = [
                    "powershell", "-Command",
                    "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,"
                    "HealthStatus,OperationalStatus | ConvertTo-Json"
                ]
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    try:
                        data = json.loads(proc.stdout.strip())
                        if isinstance(data, dict):
                            data = [data]
                        for disk in data:
                            model = disk.get("FriendlyName", "")
                            health_status = disk.get("HealthStatus", "")
                            media_type = disk.get("MediaType", "")
                            if health_status:
                                result["available"] = True
                                result["model"] = model
                                result["status"] = "ok" if health_status.lower() == "healthy" else "failing"
                                result["wear_percent"] = -1.0
                    except Exception:
                        pass
            else:
                # Linux: try smartctl
                # First, find the device for this path
                device = self._find_device_for_path(path)
                if device:
                    cmd = ["smartctl", "-A", "-H", "-i", device]
                    proc = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=10,
                    )
                    if proc.returncode is not None:
                        output = proc.stdout
                        result["available"] = True

                        # Parse health status
                        if "PASSED" in output:
                            result["status"] = "ok"
                        elif "FAILED" in output:
                            result["status"] = "failing"
                        else:
                            result["status"] = "unknown"

                        # Parse model
                        for line in output.splitlines():
                            if "Model Family" in line or "Device Model" in line:
                                result["model"] = line.split(":", 1)[1].strip()
                                break

                        # Parse wear level (SSD)
                        for line in output.splitlines():
                            if "Wear_Leveling_Count" in line or "Media_Wearout_Indicator" in line:
                                parts = line.split()
                                if len(parts) >= 10:
                                    # RAW_VALUE is typically the remaining percentage
                                    try:
                                        raw = int(parts[-1])
                                        if raw <= 100:
                                            result["wear_percent"] = float(raw)
                                            result["estimated_lifespan"] = float(raw)
                                    except Exception:
                                        pass
                            if "Percentage Used" in line:  # NVMe
                                for part in line.split():
                                    if part.replace(".", "").replace("%", "").isdigit():
                                        used = float(part.replace("%", ""))
                                        result["wear_percent"] = used
                                        result["estimated_lifespan"] = 100.0 - used
                                        break

                        # Parse temperature
                        for line in output.splitlines():
                            if "Temperature_Celsius" in line or "Temperature:" in line:
                                parts = line.split()
                                for part in parts:
                                    try:
                                        val = int(part)
                                        if 0 < val < 200:
                                            result["temperature"] = float(val)
                                            break
                                    except Exception:
                                        pass

                        # Parse power-on hours
                        for line in output.splitlines():
                            if "Power_On_Hours" in line or "Power Cycles" in line:
                                parts = line.split()
                                for part in parts:
                                    try:
                                        val = int(part)
                                        if val > 0:
                                            result["power_on_hours"] = float(val)
                                            break
                                    except Exception:
                                        pass

                        # Parse serial (last 4 chars only)
                        for line in output.splitlines():
                            if "Serial Number" in line:
                                serial = line.split(":", 1)[1].strip()
                                result["serial"] = serial[-4:] if len(serial) > 4 else serial
                                break

        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        return result

    def _find_device_for_path(self, path: str) -> str:
        """Find the block device for a given path (Linux only).

        Uses df to find the mount point, then maps to a device.
        """
        try:
            proc = subprocess.run(
                ["df", path], capture_output=True, text=True, timeout=5,
            )
            if proc.returncode == 0:
                lines = proc.stdout.strip().splitlines()
                if len(lines) >= 2:
                    device = lines[1].split()[0]
                    # Convert /dev/sda1 -> /dev/sda for smartctl
                    if device.startswith("/dev/sd") and len(device) > 8:
                        device = device.rstrip("0123456789")
                    elif device.startswith("/dev/nvme"):
                        # /dev/nvme0n1p1 -> /dev/nvme0n1
                        parts = device.split("p")
                        if len(parts) > 1:
                            device = "p".join(parts[:-1])
                    return device
        except Exception:
            pass
        return ""

    def _get_all_drive_paths(self) -> list[tuple[str, str]]:
        """Get all drive paths to check, with labels."""
        paths: list[tuple[str, str]] = []

        # Root directory (where ANUBIS lives)
        paths.append((str(self.root), "ANUBIS root"))

        # A/B drive paths
        if self.ab_drive:
            try:
                active_path = self.ab_drive.get_active_path()
                staging_path = self.ab_drive.get_staging_path()
                paths.append((active_path, f"Drive {self.ab_drive.get_active_drive()} (active)"))
                paths.append((staging_path, f"Drive {self.ab_drive.get_staging_drive()} (standby)"))
            except Exception:
                pass

        # Extra drives
        for drive in self.extra_drives:
            paths.append((drive, f"Extra: {drive}"))

        # Home directory
        home = str(Path.home())
        if home not in [p[0] for p in paths]:
            paths.append((home, "Home directory"))

        # Deduplicate
        seen: set[str] = set()
        unique: list[tuple[str, str]] = []
        for path, label in paths:
            # Normalize path
            norm = os.path.realpath(path) if os.path.exists(path) else path
            if norm not in seen:
                seen.add(norm)
                unique.append((path, label))

        return unique

    # ===========================================================
    # SNAPSHOT STATUS
    # ===========================================================

    def _get_snapshot_status(self) -> dict[str, Any]:
        """Get snapshot system status."""
        if self.snapshot_manager is None:
            return {"available": False}

        try:
            status = self.snapshot_manager.get_status()
            status["available"] = True

            # Check if snapshots are stale
            latest_ts = status.get("latest_timestamp", 0)
            if latest_ts > 0:
                age_hours = (time.time() - latest_ts) / 3600
                status["latest_age_hours"] = round(age_hours, 1)
                status["stale"] = age_hours > self.SNAPSHOT_STALE_HOURS
            else:
                status["stale"] = True
                status["latest_age_hours"] = -1

            return status
        except Exception as e:
            return {"available": True, "error": str(e)}

    # ===========================================================
    # CLOUD SYNC STATUS
    # ===========================================================

    def _get_cloud_sync_status(self) -> dict[str, Any]:
        """Get cloud sync status."""
        if self.cloud_sync is None:
            return {"available": False}

        try:
            # Try to get status from cloud sync module
            if hasattr(self.cloud_sync, "get_status"):
                status = self.cloud_sync.get_status()
            elif hasattr(self.cloud_sync, "status"):
                status = self.cloud_sync.status()
            else:
                status = {"available": True}

            status["available"] = True

            # Check last sync time
            last_sync = status.get("last_sync", status.get("last_sync_time", 0))
            if last_sync > 0:
                age_hours = (time.time() - last_sync) / 3600
                status["last_sync_age_hours"] = round(age_hours, 1)
                status["stale"] = age_hours > self.CLOUD_STALE_HOURS
            else:
                status["stale"] = True
                status["last_sync_age_hours"] = -1

            return status
        except Exception as e:
            return {"available": True, "error": str(e)}

    # ===========================================================
    # A/B DRIVE STATUS
    # ===========================================================

    def _get_ab_drive_status(self) -> dict[str, Any]:
        """Get A/B drive system status."""
        if self.ab_drive is None:
            return {"available": False}

        try:
            status = self.ab_drive.status()
            status["available"] = True
            return status
        except Exception as e:
            return {"available": True, "error": str(e)}

    # ===========================================================
    # REPORT GENERATION
    # ===========================================================

    def generate_report(self) -> DailyReport:
        """Generate a complete daily drive and storage report."""
        report = DailyReport(
            report_id=f"drive_report_{int(time.time())}",
            timestamp=time.time(),
        )

        # 1. Check all drives
        all_paths = self._get_all_drive_paths()
        for path, label in all_paths:
            health = self._check_disk_usage(path, label)
            report.drives.append(health)
            if health.status == "critical":
                report.issues.extend(health.issues)
            elif health.status == "warning":
                report.issues.extend(health.issues)

        # 2. A/B drive status
        report.ab_drive_status = self._get_ab_drive_status()
        if report.ab_drive_status.get("available"):
            canary_reason = report.ab_drive_status.get("canary_reason", "")
            if "exceeded" in canary_reason.lower() or "failed" in canary_reason.lower():
                report.issues.append(f"A/B canary test issue: {canary_reason}")

        # 3. Snapshot status
        report.snapshot_status = self._get_snapshot_status()
        if report.snapshot_status.get("stale"):
            age = report.snapshot_status.get("latest_age_hours", -1)
            if age < 0:
                report.issues.append("No snapshots have been created yet")
            else:
                report.issues.append(f"Snapshots are stale — last snapshot was {age:.0f} hours ago")

        # 4. Cloud sync status
        report.cloud_sync_status = self._get_cloud_sync_status()
        if report.cloud_sync_status.get("stale") and report.cloud_sync_status.get("available"):
            age = report.cloud_sync_status.get("last_sync_age_hours", -1)
            if age < 0:
                report.issues.append("Cloud sync has never run")
            else:
                report.issues.append(f"Cloud sync is stale — last sync was {age:.0f} hours ago")

        # 5. Determine overall status
        if any(d.status == "critical" for d in report.drives):
            report.overall_status = "critical"
        elif report.issues:
            report.overall_status = "warning"
        else:
            report.overall_status = "healthy"

        # 6. Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        # 7. Generate spoken briefing
        report.spoken_briefing = self._generate_briefing(report)

        # Save report
        self._save_report(report)
        self._log("drive_report", {"status": report.overall_status, "issues": len(report.issues)})

        return report

    def _generate_recommendations(self, report: DailyReport) -> list[str]:
        """Generate actionable recommendations based on the report."""
        recs: list[str] = []

        for drive in report.drives:
            if drive.status == "critical":
                recs.append(f"Free up space on {drive.label} — only {drive.free_gb:.1f} GB left")
            elif drive.status == "warning":
                recs.append(f"Monitor {drive.label} — {drive.percent_used:.0f}% used, {drive.free_gb:.1f} GB free")
            # SMART recommendations
            if drive.smart_status == "failing":
                recs.append(f"URGENT: Replace {drive.label} ({drive.smart_model}) — SMART reports failing")
            elif drive.estimated_lifespan_percent >= 0 and drive.estimated_lifespan_percent < 10:
                recs.append(f"Replace {drive.label} soon — only {drive.estimated_lifespan_percent:.0f}% lifespan remaining")
            elif drive.estimated_lifespan_percent >= 0 and drive.estimated_lifespan_percent < 25:
                recs.append(f"Monitor {drive.label} — {drive.estimated_lifespan_percent:.0f}% lifespan remaining")

        if report.snapshot_status.get("stale"):
            recs.append("Create a new snapshot — current snapshots are stale")

        if report.cloud_sync_status.get("stale") and report.cloud_sync_status.get("available"):
            recs.append("Run a cloud sync — last sync is stale")

        if report.ab_drive_status.get("available"):
            canary = report.ab_drive_status.get("canary_reason", "")
            if "exceeded" in canary.lower():
                recs.append("Review A/B canary test — metrics exceeded thresholds, consider rollback")

        if not recs:
            recs.append("All systems healthy — no action needed")

        return recs

    def _generate_briefing(self, report: DailyReport) -> str:
        """Generate a spoken briefing for DEMON to read."""
        parts: list[str] = []

        # Overall status
        if report.overall_status == "healthy":
            parts.append("All drives and storage are healthy.")
        elif report.overall_status == "warning":
            parts.append(f"I've found {len(report.issues)} issue(s) that need attention.")
        else:
            parts.append(f"Critical storage issues detected: {len(report.issues)} problem(s).")

        # Drive summary
        if report.drives:
            parts.append("Drive status:")
            for d in report.drives:
                line = f"  {d.label}: {d.free_gb:.1f} GB free of {d.total_gb:.1f} GB ({d.percent_used:.0f}% used) — {d.status}"
                if d.smart_available:
                    line += f" | SMART: {d.smart_status}"
                    if d.estimated_lifespan_percent >= 0:
                        line += f", lifespan: {d.estimated_lifespan_percent:.0f}%"
                    if d.smart_temperature >= 0:
                        line += f", temp: {d.smart_temperature:.0f}C"
                parts.append(line)

        # A/B drive
        if report.ab_drive_status.get("available"):
            active = report.ab_drive_status.get("active_drive", "?")
            staging = report.ab_drive_status.get("staging_drive", "?")
            version = report.ab_drive_status.get("active_version", "?")
            canary = report.ab_drive_status.get("canary_active", False)
            parts.append(f"A/B drives: Drive {active} is active (version {version}), Drive {staging} is standby.")
            if canary:
                parts.append(f"Canary test in progress: {report.ab_drive_status.get('canary_reason', '')}")

        # Snapshots
        if report.snapshot_status.get("available"):
            count = report.snapshot_status.get("snapshot_count", 0)
            size = report.snapshot_status.get("total_size_mb", 0)
            verified = report.snapshot_status.get("latest_verified", False)
            parts.append(f"Snapshots: {count} total, {size:.1f} MB. Latest verified: {verified}.")
            if report.snapshot_status.get("stale"):
                age = report.snapshot_status.get("latest_age_hours", -1)
                parts.append(f"Warning: last snapshot is {age:.0f} hours old.")

        # Cloud sync
        if report.cloud_sync_status.get("available"):
            age = report.cloud_sync_status.get("last_sync_age_hours", -1)
            if age >= 0:
                parts.append(f"Cloud sync: last sync {age:.1f} hours ago.")
            else:
                parts.append("Cloud sync: never synced.")
            if report.cloud_sync_status.get("stale"):
                parts.append("Warning: cloud sync is stale.")
        else:
            parts.append("Cloud sync: not configured.")

        # Issues
        if report.issues:
            parts.append("Issues found:")
            for issue in report.issues:
                parts.append(f"  - {issue}")

        # Recommendations
        if report.recommendations:
            parts.append("Recommendations:")
            for rec in report.recommendations:
                parts.append(f"  - {rec}")

        return "\n".join(parts)

    def _save_report(self, report: DailyReport) -> None:
        """Save report to the daily reports log."""
        try:
            with open(self._reports_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(report.to_dict()) + "\n")
        except Exception:
            pass

    # ===========================================================
    # DELIVER REPORT
    # ===========================================================

    def deliver_report(self, *, speak: bool = True, notify: bool = True) -> dict[str, Any]:
        """Generate and deliver the daily report.

        Speaks the briefing via DEMON and sends a notification.
        """
        report = self.generate_report()

        if speak and report.spoken_briefing:
            self._speak(report.spoken_briefing)

        if notify:
            title = f"Drive Report — {report.overall_status.upper()}"
            body = "\n".join(report.issues) if report.issues else "All systems healthy."
            self._notify(title, body)

        return report.to_dict()

    # ===========================================================
    # REPORT HISTORY
    # ===========================================================

    def get_report_history(self, limit: int = 30) -> dict[str, Any]:
        """Get past daily reports."""
        reports: list[dict[str, Any]] = []
        if self._reports_file.exists():
            try:
                with open(self._reports_file, "r", encoding="utf-8") as f:
                    for line in f:
                        reports.append(json.loads(line.strip()))
            except Exception:
                pass
        reports = reports[-limit:]
        return {"count": len(reports), "reports": reports}

    def get_last_report(self) -> dict[str, Any] | None:
        """Get the most recent report."""
        history = self.get_report_history(limit=1)
        if history["reports"]:
            return history["reports"][0]
        return None

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get drive monitor status."""
        last_report = self.get_last_report()
        return {
            "has_ab_drive": self.ab_drive is not None,
            "has_snapshot_manager": self.snapshot_manager is not None,
            "has_cloud_sync": self.cloud_sync is not None,
            "last_report_time": last_report.get("timestamp", 0) if last_report else 0,
            "last_report_status": last_report.get("overall_status", "none") if last_report else "none",
            "monitored_paths": [p[0] for p in self._get_all_drive_paths()],
        }
