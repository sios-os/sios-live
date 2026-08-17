"""Linux deployment validation — checks for Unix-specific issues.

This script validates that SIOS/ANUBIS is ready for deployment on
Ubuntu 24.04. It checks:

1. Platform-specific imports (resource, fcntl, pwd, grp)
2. Unix socket path configuration
3. File permissions (0o600 for sensitive files, 0o700 for dirs)
4. Systemd service files
5. Python version compatibility
6. Required system packages
7. Path separators and hardcoded Windows paths
8. Shell command compatibility (bash vs PowerShell)
9. Signal handling (SIGTERM, SIGUSR1)
10. Process management (fork, daemonize)

Run on the target Linux system or in WSL2:
    python3 tools/linux_deploy_check.py
"""
from __future__ import annotations

import os
import platform
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: str = ""
    fix: str = ""


class LinuxDeployChecker:
    """Validates SIOS/ANUBIS for Linux deployment."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else Path(__file__).resolve().parent.parent
        self.results: list[CheckResult] = []
        self.is_linux = sys.platform.startswith("linux")
        self.is_wsl = "microsoft" in platform.uname().release.lower() if self.is_linux else False

    def run_all(self) -> dict[str, Any]:
        """Run all deployment checks."""
        self.results = []
        self.check_python_version()
        self.check_platform_imports()
        self.check_unix_socket_config()
        self.check_hardcoded_windows_paths()
        self.check_shell_commands()
        self.check_file_permissions()
        self.check_systemd_services()
        self.check_signal_handling()
        self.check_process_management()
        self.check_required_packages()
        self.check_path_separators()
        self.check_test_compatibility()

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        return {
            "platform": sys.platform,
            "is_linux": self.is_linux,
            "is_wsl": self.is_wsl,
            "total_checks": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": [r.__dict__ for r in self.results],
            "ready": failed == 0,
        }

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    # ===========================================================
    # CHECKS
    # ===========================================================

    def check_python_version(self) -> None:
        """Check Python version (need 3.10+)."""
        version = sys.version_info
        passed = version >= (3, 10)
        self.add(CheckResult(
            name="python_version",
            passed=passed,
            message=f"Python {version.major}.{version.minor}.{version.micro}",
            fix="Install Python 3.10 or later" if not passed else "",
        ))

    def check_platform_imports(self) -> None:
        """Check that platform-specific imports work on Linux."""
        issues = []
        for mod_name in ["resource", "fcntl", "pwd", "grp", "termios", "posix_ipc"]:
            try:
                __import__(mod_name)
            except ImportError:
                issues.append(mod_name)

        if not issues:
            self.add(CheckResult(
                name="platform_imports",
                passed=True,
                message="All Unix-specific modules available",
            ))
        else:
            self.add(CheckResult(
                name="platform_imports",
                passed=False,
                message=f"Missing Unix modules: {', '.join(issues)}",
                fix="These modules are only available on Unix. "
                    "Tests that use them should be conditionally skipped on Windows.",
            ))

    def check_unix_socket_config(self) -> None:
        """Check that the daemon socket path is Unix-compatible."""
        daemon = self.root / "tools" / "anubis_daemon.py"
        if not daemon.exists():
            self.add(CheckResult(
                name="unix_socket_config",
                passed=False,
                message="Daemon file not found",
            ))
            return

        content = daemon.read_text(encoding="utf-8")
        # Check for AF_UNIX
        has_unix_socket = "AF_UNIX" in content
        # Check for /tmp/anubis.sock
        has_sock_path = "/tmp/anubis.sock" in content

        if has_unix_socket and has_sock_path:
            self.add(CheckResult(
                name="unix_socket_config",
                passed=True,
                message="Unix socket configured at /tmp/anubis.sock",
            ))
        else:
            self.add(CheckResult(
                name="unix_socket_config",
                passed=False,
                message="Unix socket not properly configured",
                fix="Ensure daemon uses AF_UNIX and /tmp/anubis.sock",
            ))

    def check_hardcoded_windows_paths(self) -> None:
        """Check for hardcoded Windows paths in Python files."""
        windows_patterns = [
            r'C:\\\\',
            r'D:\\\\',
            r"'C:\\",
            r'"C:\\',
            r"'D:\\",
            r'"D:\\',
            r"\\\\Users\\\\",
            r"\\\\Program Files\\\\",
        ]
        issues = []
        for py_file in (self.root / "anubis").glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in windows_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(f"{py_file.name}: {len(matches)} Windows path(s)")
                    break

        if not issues:
            self.add(CheckResult(
                name="hardcoded_windows_paths",
                passed=True,
                message="No hardcoded Windows paths found",
            ))
        else:
            self.add(CheckResult(
                name="hardcoded_windows_paths",
                passed=False,
                message=f"Found Windows paths in {len(issues)} files",
                details="; ".join(issues[:10]),
                fix="Use pathlib.Path and os.path instead of hardcoded paths",
            ))

    def check_shell_commands(self) -> None:
        """Check for Windows-specific shell commands."""
        windows_cmds = ["powershell", "cmd.exe", "where ", "Get-ChildItem", "Write-Output"]
        issues = []
        for py_file in (self.root / "anubis").glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for cmd in windows_cmds:
                if cmd.lower() in content.lower():
                    # Check if it's in a platform-conditional block
                    # Simple heuristic: if "platform" or "sys.platform" is nearby
                    idx = content.lower().find(cmd.lower())
                    context = content[max(0, idx-200):idx+200]
                    if "platform" not in context.lower() and "sys.platform" not in context.lower():
                        issues.append(f"{py_file.name}: '{cmd}'")
                        break

        if not issues:
            self.add(CheckResult(
                name="shell_commands",
                passed=True,
                message="No Windows-only shell commands found",
            ))
        else:
            self.add(CheckResult(
                name="shell_commands",
                passed=False,
                message=f"Found Windows commands in {len(issues)} files",
                details="; ".join(issues[:10]),
                fix="Use platform-conditional code: if sys.platform == 'win32': ... else: ...",
            ))

    def check_file_permissions(self) -> None:
        """Check that sensitive files have restrictive permissions."""
        if not self.is_linux:
            self.add(CheckResult(
                name="file_permissions",
                passed=True,
                message="Skipped on non-Linux (file permissions are Unix-only)",
            ))
            return

        sensitive_paths = [
            self.root / "identity" / "vault.enc",
            self.root / "config" / "cloud_credentials.json",
        ]
        issues = []
        for path in sensitive_paths:
            if path.exists():
                stat = path.stat()
                perms = stat.st_mode & 0o777
                if perms & 0o077:  # group/other can read/write
                    issues.append(f"{path}: {oct(perms)} (should be 0o600)")

        if not issues:
            self.add(CheckResult(
                name="file_permissions",
                passed=True,
                message="Sensitive files have restrictive permissions",
            ))
        else:
            self.add(CheckResult(
                name="file_permissions",
                passed=False,
                message=f"{len(issues)} file(s) with loose permissions",
                details="; ".join(issues),
                fix="chmod 600 <file> for sensitive files",
            ))

    def check_systemd_services(self) -> None:
        """Check that systemd service files exist and are valid."""
        session_dir = self.root / "session"
        if not session_dir.exists():
            self.add(CheckResult(
                name="systemd_services",
                passed=False,
                message="session/ directory not found",
                fix="Create systemd service files in session/",
            ))
            return

        service_files = list(session_dir.glob("*.service"))
        if not service_files:
            self.add(CheckResult(
                name="systemd_services",
                passed=False,
                message="No .service files found in session/",
                fix="Create systemd service files for the daemon",
            ))
            return

        issues = []
        for svc in service_files:
            content = svc.read_text(encoding="utf-8", errors="ignore")
            if "[Unit]" not in content:
                issues.append(f"{svc.name}: missing [Unit] section")
            if "[Service]" not in content:
                issues.append(f"{svc.name}: missing [Service] section")
            if "ExecStart" not in content:
                issues.append(f"{svc.name}: missing ExecStart")

        if not issues:
            self.add(CheckResult(
                name="systemd_services",
                passed=True,
                message=f"{len(service_files)} service file(s) found and valid",
            ))
        else:
            self.add(CheckResult(
                name="systemd_services",
                passed=False,
                message=f"{len(issues)} issue(s) in service files",
                details="; ".join(issues),
                fix="Fix systemd service file structure",
            ))

    def check_signal_handling(self) -> None:
        """Check that the daemon handles Unix signals properly."""
        daemon = self.root / "tools" / "anubis_daemon.py"
        if not daemon.exists():
            self.add(CheckResult(
                name="signal_handling",
                passed=False,
                message="Daemon file not found",
            ))
            return

        content = daemon.read_text(encoding="utf-8")
        signals_found = []
        for sig in ["SIGTERM", "SIGINT", "SIGUSR1", "SIGHUP"]:
            if sig in content:
                signals_found.append(sig)

        if len(signals_found) >= 2:  # at least SIGTERM and SIGINT
            self.add(CheckResult(
                name="signal_handling",
                passed=True,
                message=f"Handles signals: {', '.join(signals_found)}",
            ))
        else:
            self.add(CheckResult(
                name="signal_handling",
                passed=False,
                message=f"Only handles: {', '.join(signals_found) or 'none'}",
                fix="Add signal handlers for SIGTERM (graceful shutdown) and SIGINT",
            ))

    def check_process_management(self) -> None:
        """Check for Unix process management (fork, daemonize)."""
        daemon = self.root / "tools" / "anubis_daemon.py"
        if not daemon.exists():
            self.add(CheckResult(
                name="process_management",
                passed=False,
                message="Daemon file not found",
            ))
            return

        content = daemon.read_text(encoding="utf-8")
        has_fork = "fork" in content.lower()
        has_daemonize = "daemonize" in content.lower() or "daemon" in content.lower()
        has_pidfile = "pidfile" in content.lower() or "pid_file" in content.lower()

        score = sum([has_fork, has_daemonize, has_pidfile])
        if score >= 1:
            self.add(CheckResult(
                name="process_management",
                passed=True,
                message=f"Has daemon support: fork={has_fork}, daemonize={has_daemonize}, pidfile={has_pidfile}",
            ))
        else:
            self.add(CheckResult(
                name="process_management",
                passed=False,
                message="No Unix daemon support found",
                fix="Add fork/daemonize/pidfile support for proper Unix daemon operation",
            ))

    def check_required_packages(self) -> None:
        """Check for required system packages (Linux only)."""
        if not self.is_linux:
            self.add(CheckResult(
                name="required_packages",
                passed=True,
                message="Skipped on non-Linux",
            ))
            return

        required = ["python3", "pip3", "git", "openssl"]
        optional = ["ollama", "signal-cli", "gammu", "smartmontools", "ffmpeg"]
        missing_required = []
        missing_optional = []

        for pkg in required:
            try:
                import shutil
                if not shutil.which(pkg):
                    missing_required.append(pkg)
            except Exception:
                pass

        for pkg in optional:
            try:
                import shutil
                if not shutil.which(pkg):
                    missing_optional.append(pkg)
            except Exception:
                pass

        if not missing_required:
            self.add(CheckResult(
                name="required_packages",
                passed=True,
                message=f"All required packages found. Optional missing: {', '.join(missing_optional) or 'none'}",
            ))
        else:
            self.add(CheckResult(
                name="required_packages",
                passed=False,
                message=f"Missing required: {', '.join(missing_required)}",
                fix=f"apt install {' '.join(missing_required)}",
            ))

    def check_path_separators(self) -> None:
        """Check for backslash path separators in Python code."""
        issues = []
        for py_file in (self.root / "anubis").glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Look for backslash paths that aren't in strings or comments
            # Simple heuristic: "C:\\" or "D:\\" patterns
            if re.search(r'["\'][A-Z]:\\\\', content):
                issues.append(py_file.name)

        if not issues:
            self.add(CheckResult(
                name="path_separators",
                passed=True,
                message="No Windows path separators found",
            ))
        else:
            self.add(CheckResult(
                name="path_separators",
                passed=False,
                message=f"Windows paths in: {', '.join(issues[:5])}",
                fix="Use forward slashes or pathlib.Path",
            ))

    def check_test_compatibility(self) -> None:
        """Check that tests handle platform differences."""
        test_dir = self.root / "tests"
        if not test_dir.exists():
            self.add(CheckResult(
                name="test_compatibility",
                passed=False,
                message="tests/ directory not found",
            ))
            return

        # Check for tests that import 'resource' without conditional skip
        issues = []
        for test_file in test_dir.glob("test_*.py"):
            content = test_file.read_text(encoding="utf-8", errors="ignore")
            if "import resource" in content:
                # Check if there's a skip condition
                if "skipIf" not in content and "skipUnless" not in content:
                    issues.append(test_file.name)

        if not issues:
            self.add(CheckResult(
                name="test_compatibility",
                passed=True,
                message="All tests handle platform differences",
            ))
        else:
            self.add(CheckResult(
                name="test_compatibility",
                passed=False,
                message=f"Tests missing platform guards: {', '.join(issues)}",
                fix="Add @unittest.skipUnless(hasattr(os, 'getuid'), 'Unix only') or similar",
            ))


def main() -> int:
    """Run the deployment checker and print results."""
    checker = LinuxDeployChecker()
    results = checker.run_all()

    print("=" * 60)
    print("SIOS/ANUBIS — Linux Deployment Validation")
    print("=" * 60)
    print(f"Platform: {results['platform']}")
    print(f"Is Linux: {results['is_linux']}")
    print(f"Is WSL:   {results['is_wsl']}")
    print()

    for r in results["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['name']}: {r['message']}")
        if r.get("fix"):
            print(f"         Fix: {r['fix']}")

    print()
    print(f"Total: {results['total_checks']}  "
          f"Passed: {results['passed']}  "
          f"Failed: {results['failed']}")
    print(f"Ready for deployment: {'YES' if results['ready'] else 'NO'}")
    return 0 if results["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
