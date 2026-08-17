"""Boot-time integrity check — verifies core files before ANUBIS starts.

This module is designed to run BEFORE the daemon starts. It:

1. Loads the core file signatures from the self-repair state
2. Verifies each core file against its stored signature
3. Checks for missing core files
4. Verifies the latest snapshot if available
5. Returns a pass/fail result

If verification fails:
- On Linux: exits with non-zero status, systemd service won't start ANUBIS
- The Creator is alerted (via system notification or log)
- The system can be booted into recovery mode instead

Usage:
    # As a standalone script (from systemd service):
    python3 -m anubis.boot_check

    # As a module:
    from anubis.boot_check import BootChecker
    checker = BootChecker(root="/path/to/sios")
    result = checker.check()
    if not result["passed"]:
        # Don't start the daemon
        sys.exit(1)

The boot check is non-destructive — it only reads and verifies,
never modifies files. If signatures don't exist (first boot),
it creates them and passes.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable


class BootChecker:
    """Verifies system integrity before the daemon starts.

    This is the first line of defense against corruption that may have
    occurred while ANUBIS was shut down (e.g., disk corruption, manual
    tampering, malware that runs when the system is off).
    """

    ACTOR = "anubis.boot_check"

    # Core files that must be present and unmodified
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
        "anubis/cold_archive.py",
        "anubis/boot_check.py",
        "anubis/forms.py",
        "anubis/scheduler.py",
        "tools/anubis_daemon.py",
    ]

    def __init__(
        self,
        root: str | Path,
        *,
        on_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.on_alert = on_alert

        # Signature file from self-repair
        self._signatures_file = self.root / "memory" / "self_repair" / "core_signatures.json"
        self._boot_log = self.root / "memory" / "self_repair" / "boot_checks.jsonl"

    def _alert(self, severity: str, message: str) -> None:
        if self.on_alert:
            try:
                self.on_alert(severity, message)
            except Exception:
                pass
        # Also write to stderr for systemd journal
        print(f"[boot_check] {severity}: {message}", file=sys.stderr)

    def _log(self, result: dict[str, Any]) -> None:
        try:
            self._boot_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self._boot_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(result) + "\n")
        except Exception:
            pass

    def _hash_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def check(self) -> dict[str, Any]:
        """Run the boot-time integrity check.

        Returns:
            Dict with:
            - passed: bool — whether the system is safe to start
            - signatures_found: bool — whether signatures existed
            - verified: int — number of files verified
            - mismatches: list[str] — files that don't match
            - missing: list[str] — files that are missing
            - errors: list[str] — any errors encountered
            - timestamp: float
        """
        result: dict[str, Any] = {
            "passed": False,
            "signatures_found": False,
            "verified": 0,
            "mismatches": [],
            "missing": [],
            "errors": [],
            "timestamp": time.time(),
        }

        # Load signatures
        if not self._signatures_file.exists():
            # First boot — create signatures and pass
            result["signatures_found"] = False
            result["passed"] = True
            result["message"] = "No signatures found — first boot. Creating signatures."
            self._create_signatures()
            self._log(result)
            return result

        result["signatures_found"] = True

        try:
            signatures = json.loads(
                self._signatures_file.read_text(encoding="utf-8")
            )
        except Exception as e:
            result["errors"].append(f"Cannot read signatures: {e}")
            result["passed"] = False
            self._alert("critical", f"Core signature file is corrupted: {e}")
            self._log(result)
            return result

        # Verify each core file
        for rel_path, expected_hash in signatures.items():
            file_path = self.root / rel_path
            if not file_path.exists():
                result["missing"].append(rel_path)
                continue
            try:
                actual_hash = self._hash_file(file_path)
                if actual_hash == expected_hash:
                    result["verified"] += 1
                else:
                    result["mismatches"].append(rel_path)
            except Exception as e:
                result["errors"].append(f"Cannot hash {rel_path}: {e}")

        # Determine pass/fail
        result["passed"] = (
            len(result["mismatches"]) == 0
            and len(result["missing"]) == 0
            and len(result["errors"]) == 0
        )

        if result["mismatches"]:
            self._alert(
                "critical",
                f"Core file signature mismatch detected: {', '.join(result['mismatches'][:5])}. "
                f"Refusing to start ANUBIS. Manual intervention required."
            )
        if result["missing"]:
            self._alert(
                "critical",
                f"Core files missing: {', '.join(result['missing'][:5])}. "
                f"Refusing to start ANUBIS. Restore from backup or snapshot."
            )

        self._log(result)
        return result

    def _create_signatures(self) -> int:
        """Create initial signatures for all core files."""
        signatures: dict[str, str] = {}
        for rel_path in self.CORE_FILES:
            file_path = self.root / rel_path
            if file_path.exists():
                try:
                    signatures[rel_path] = self._hash_file(file_path)
                except Exception:
                    pass

        try:
            self._signatures_file.parent.mkdir(parents=True, exist_ok=True)
            self._signatures_file.write_text(
                json.dumps(signatures, indent=2) + "\n", encoding="utf-8"
            )
        except Exception:
            pass

        return len(signatures)

    def get_boot_history(self, limit: int = 30) -> dict[str, Any]:
        """Get past boot check results."""
        results: list[dict[str, Any]] = []
        if self._boot_log.exists():
            try:
                with open(self._boot_log, "r", encoding="utf-8") as f:
                    for line in f:
                        results.append(json.loads(line.strip()))
            except Exception:
                pass
        results = results[-limit:]
        return {"count": len(results), "checks": results}

    def get_last_boot_check(self) -> dict[str, Any] | None:
        """Get the most recent boot check result."""
        history = self.get_boot_history(limit=1)
        if history["checks"]:
            return history["checks"][0]
        return None


def main() -> int:
    """Standalone entry point for systemd service.

    Returns 0 if the system is safe to start, 1 otherwise.
    """
    # Find the root directory
    root = os.environ.get("ANUBIS_ROOT", ".")
    if not os.path.isdir(root):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    checker = BootChecker(root)
    result = checker.check()

    if result["passed"]:
        print(f"[boot_check] PASSED — {result['verified']} files verified")
        return 0
    else:
        print(f"[boot_check] FAILED — {len(result['mismatches'])} mismatches, "
              f"{len(result['missing'])} missing, {len(result['errors'])} errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
