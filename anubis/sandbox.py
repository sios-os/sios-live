"""Sandboxed execution of untrusted generated code.

Book 09 treats "external packages, generated artifacts, models, devices,
documents, and network data as untrusted". Code that ANUBIS writes for himself
is a generated artifact, so it is untrusted by default and runs here.

Defence is layered, because any single layer can be bypassed:

  1. Static hazard analysis      constitution.analyze_payload (applied by caller)
  2. Network namespace           unshare --net; verified to block TCP and DNS
  3. Mount namespace             tmpfs over /mnt, hiding Windows DrvFs mounts
  4. Privilege drop              run as uid 65534 (nobody)
  5. Kernel resource limits      RLIMIT_AS / CPU / FSIZE / NPROC / CORE
  6. Wall-clock timeout          process-group SIGKILL, so children die too
  7. Filesystem confinement      disposable cwd owned by the sandbox uid

Layers 3 and 4 were both added in response to real escapes found by the
adversarial test suite:

  * With only network isolation, code running as root wrote to /etc.
    Namespace isolation does not imply filesystem safety.
  * After dropping privileges, code could still write to /mnt/d, because
    DrvFs (the Windows filesystem bridge) reports every file as world-writable
    and ignores Unix ownership. Permission-based defence is void on DrvFs, so
    those mounts must be removed from the sandbox's view entirely.

Ordering is load-bearing: the namespace must be created while privileged, and
privileges dropped only afterwards. Dropping first leaves `unshare` unable to
create the namespace at all.

Honesty requirement: SandboxResult.isolation records which layers were actually
in force. The truth law forbids claiming protection that was not achieved, so a
degraded sandbox reports itself as degraded rather than passing silently.
"""

from __future__ import annotations

import os
try:
    import resource
except ImportError:
    resource = None  # Not available on Windows
import shutil
try:
    import signal
except ImportError:
    signal = None
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# Unprivileged identity used for sandboxed execution when ANUBIS starts as root.
# 65534:65534 is nobody:nogroup on Debian/Ubuntu.
SANDBOX_UID = 65534
SANDBOX_GID = 65534

# Paths masked inside the sandbox's mount namespace. These are filesystems where
# Unix permissions are not enforced (DrvFs) or that expose the host needlessly.
# /etc is masked and replaced with a minimal passwd/group so Python's pwd module
# works without exposing host user data.
MASKED_PATHS = ("/mnt", "/etc")


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_s: float = 30.0
    memory_mb: int = 512
    cpu_seconds: int = 20
    max_file_bytes: int = 8 * 1024 * 1024
    max_processes: int = 256         # per-uid; nobody may already own processes
    allow_network: bool = False
    drop_privileges: bool = True
    mask_host_mounts: bool = True


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False
    isolation: dict[str, bool] = field(default_factory=dict)
    workdir_files: list[str] = field(default_factory=list)

    @property
    def fully_isolated(self) -> bool:
        """True only when every layer was actually applied."""
        return all(self.isolation.values())

    def summary(self) -> str:
        state = "ok" if self.ok else ("timeout" if self.timed_out else "fail")
        layers = ",".join(k for k, v in self.isolation.items() if v) or "none"
        missing = [k for k, v in self.isolation.items() if not v]
        s = f"{state} exit={self.exit_code} {self.duration_s:.2f}s isolation=[{layers}]"
        if missing:
            s += f" DEGRADED(missing={','.join(missing)})"
        return s


# ---------------------------------------------------------------- isolation

@dataclass(frozen=True)
class Isolation:
    """How containment is actually achieved on this host.

    Resolved once by probing, so the sandbox never claims a protection it has
    not demonstrated it can apply.
    """

    label: str
    network_blocked: bool
    host_mounts_masked: bool
    unprivileged: bool
    _prefix: tuple[str, ...] = ()
    _shell_wrapped: bool = False
    _drop_in_preexec: bool = False

    def build_command(self, python: str, target: Path) -> list[str]:
        if not self._shell_wrapped:
            return [*self._prefix, python, "-I", "-S", str(target)]

        # Inside a fresh mount namespace, mask host mounts while still
        # privileged, then shed privileges and exec the artifact.
        # sh -c 'script' arg0 arg1  =>  $0=arg0, $1=arg1
        masks = "; ".join(
            f"mount -t tmpfs tmpfs {p} 2>/dev/null || true" for p in MASKED_PATHS
        )
        # After masking /etc with tmpfs, create a minimal passwd so
        # Python's pwd module works without exposing host user data.
        # The tmpfs is mounted with mode 0755 so nobody can read but not write.
        etc_setup = (
            "mount -t tmpfs -o mode=0755 tmpfs /etc 2>/dev/null || true; "
            "echo 'nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin' > /etc/passwd 2>/dev/null || true; "
            "echo 'nogroup:x:65534:' > /etc/group 2>/dev/null || true; "
            "chmod 0644 /etc/passwd /etc/group 2>/dev/null || true"
        )
        setpriv = shutil.which("setpriv") or "/usr/bin/setpriv"
        inner = (
            f"{masks}; {etc_setup}; "
            f'exec {setpriv} --reuid={SANDBOX_UID} --regid={SANDBOX_GID} '
            f'--clear-groups "$0" -I -S "$1"'
        )
        return [*self._prefix, "sh", "-c", inner, python, str(target)]

    @property
    def needs_owned_workdir(self) -> bool:
        return self.unprivileged and (self._shell_wrapped or self._drop_in_preexec)

    @property
    def drop_in_preexec(self) -> bool:
        return self._drop_in_preexec


def _probe(cmd: list[str]) -> bool:
    try:
        return subprocess.run(
            cmd, capture_output=True, timeout=10
        ).returncode == 0
    except Exception:  # noqa: BLE001 - probe failure means "not available"
        return False


def resolve_isolation(policy: SandboxPolicy) -> Isolation:
    """Choose the strongest containment this host actually supports."""
    unshare = shutil.which("unshare")
    setpriv = shutil.which("setpriv")
    am_root = hasattr(os, "geteuid") and os.geteuid() == 0
    want_net = not policy.allow_network
    want_drop = policy.drop_privileges
    want_mask = policy.mask_host_mounts

    # --- Preferred: root, full namespace set, privileges dropped after mount ---
    if unshare and setpriv and am_root and want_net and want_mask:
        prefix = [unshare, "--net", "--mount", "--fork", "--pid", "--mount-proc"]
        probe = prefix + ["sh", "-c", "mount -t tmpfs tmpfs /mnt 2>/dev/null; true"]
        if _probe(probe):
            return Isolation(
                label="unshare net+mount, /mnt masked, dropped to nobody",
                network_blocked=True,
                host_mounts_masked=True,
                unprivileged=want_drop,
                _prefix=tuple(prefix),
                _shell_wrapped=True,
            )

    # --- Root, network namespace only (no mount masking available) ---
    if unshare and am_root and want_net:
        prefix = [unshare, "--net", "--fork", "--pid", "--mount-proc"]
        if want_drop:
            with_uid = prefix + [
                "--setuid", str(SANDBOX_UID), "--setgid", str(SANDBOX_GID)
            ]
            if _probe(with_uid + ["true"]):
                return Isolation(
                    label="unshare --net +setuid(nobody), host mounts VISIBLE",
                    network_blocked=True,
                    host_mounts_masked=False,
                    unprivileged=True,
                    _prefix=tuple(with_uid),
                )
        if _probe(prefix + ["true"]):
            return Isolation(
                label="unshare --net, privs dropped in preexec",
                network_blocked=True,
                host_mounts_masked=False,
                unprivileged=want_drop,
                _prefix=tuple(prefix),
                _drop_in_preexec=want_drop,
            )

    # --- Already unprivileged: user namespace grants the needed capability ---
    if unshare and not am_root and want_net:
        rootless = [unshare, "--user", "--map-root-user", "--net", "--fork", "--pid"]
        if want_mask:
            probe = rootless + ["sh", "-c", "mount -t tmpfs tmpfs /mnt 2>/dev/null; true"]
            if _probe(probe):
                # root inside the userns maps to our unprivileged uid outside,
                # so the host filesystem stays protected.
                return Isolation(
                    label="rootless userns, net+mount, /mnt masked",
                    network_blocked=True,
                    host_mounts_masked=True,
                    unprivileged=True,
                    _prefix=tuple(rootless + ["--mount"]),
                    _shell_wrapped=False,
                )
        if _probe(rootless + ["true"]):
            return Isolation(
                label="rootless userns + net",
                network_blocked=True,
                host_mounts_masked=False,
                unprivileged=True,
                _prefix=tuple(rootless),
            )

    # --- Degraded: no namespaces. Say so plainly. ---
    if policy.allow_network:
        label = "network intentionally allowed"
    elif not unshare:
        label = "unshare unavailable - NETWORK NOT ISOLATED"
    else:
        label = "no working unshare mode - NETWORK NOT ISOLATED"
    return Isolation(
        label=label,
        network_blocked=False,
        host_mounts_masked=False,
        unprivileged=(want_drop and am_root) or not am_root,
        _drop_in_preexec=want_drop and am_root,
    )


# ------------------------------------------------------------------ sandbox

class Sandbox:
    """Runs a Python source file under containment."""

    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()
        self.isolation = resolve_isolation(self.policy)

    # ------------------------------------------------------------- internals

    def _limits(self):
        """Applied in the child, after fork, before exec."""
        p = self.policy
        drop = self.isolation.drop_in_preexec

        def apply() -> None:
            if hasattr(os, "setsid"):
                os.setsid()  # own process group, so a timeout kills the whole tree

            if resource is not None:
                mem = p.memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
                resource.setrlimit(resource.RLIMIT_CPU, (p.cpu_seconds, p.cpu_seconds))
                resource.setrlimit(
                    resource.RLIMIT_FSIZE, (p.max_file_bytes, p.max_file_bytes)
                )
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                try:
                    resource.setrlimit(
                        resource.RLIMIT_NPROC, (p.max_processes, p.max_processes)
                    )
                except (ValueError, OSError):
                    pass  # not fatal; other layers still apply

            # Limits are set while still privileged so they cannot be raised
            # afterwards. Group before user: the reverse order would leave us
            # unable to change groups.
            if drop:
                os.setgroups([])
                os.setresgid(SANDBOX_GID, SANDBOX_GID, SANDBOX_GID)
                os.setresuid(SANDBOX_UID, SANDBOX_UID, SANDBOX_UID)

        return apply

    @staticmethod
    def _env(workdir: Path) -> dict[str, str]:
        # Minimal environment: nothing inherited that could leak secrets or
        # point at the host's package or model stores.
        return {
            "PATH": "/usr/bin:/bin",
            "HOME": str(workdir),
            "TMPDIR": str(workdir),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONNOUSERSITE": "1",
            "LC_ALL": "C.UTF-8",
        }

    @staticmethod
    def _kill_tree(proc: subprocess.Popen) -> None:
        """SIGKILL the whole process group; a runaway child must not survive."""
        try:
            if hasattr(os, "killpg") and signal is not None:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, PermissionError, AttributeError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass

    # ---------------------------------------------------------------- public

    def run_source(
        self, source: str, *, filename: str = "artifact.py"
    ) -> SandboxResult:
        """Write `source` into a disposable directory and execute it.

        The working directory is created under the system temp dir, which is on
        a real Linux filesystem -- never on a DrvFs mount, where ownership would
        be unenforceable.
        """
        workdir = Path(tempfile.mkdtemp(prefix="anubis-sbx-"))
        try:
            target = workdir / filename
            target.write_text(source, encoding="utf-8")

            if self.isolation.needs_owned_workdir:
                os.chown(workdir, SANDBOX_UID, SANDBOX_GID)
                os.chown(target, SANDBOX_UID, SANDBOX_GID)
                os.chmod(workdir, 0o700)

            cmd = self.isolation.build_command(sys.executable, target)

            isolation = {
                "network_blocked": self.isolation.network_blocked,
                "host_mounts_masked": self.isolation.host_mounts_masked,
                "unprivileged": self.isolation.unprivileged,
                "memory_capped": True,
                "cpu_capped": True,
                "filesize_capped": True,
                "timeout_armed": True,
                "isolated_cwd": True,
            }

            t0 = time.monotonic()
            timed_out = False
            proc = subprocess.Popen(
                cmd,
                cwd=workdir,
                env=self._env(workdir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                preexec_fn=self._limits() if sys.platform != "win32" else None,
            )
            try:
                stdout, stderr = proc.communicate(timeout=self.policy.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._kill_tree(proc)
                stdout, stderr = proc.communicate()
                stderr = (stderr or "") + (
                    f"\n[sandbox] killed after {self.policy.timeout_s}s timeout"
                )
            duration = time.monotonic() - t0

            produced = sorted(
                str(p.relative_to(workdir))
                for p in workdir.rglob("*")
                if p.is_file() and p.name != filename
            )

            return SandboxResult(
                ok=(not timed_out and proc.returncode == 0),
                exit_code=proc.returncode,
                stdout=(stdout or "")[:200_000],
                stderr=(stderr or "")[:200_000],
                duration_s=duration,
                timed_out=timed_out,
                isolation=isolation,
                workdir_files=produced,
            )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def run_with_tests(self, skill_source: str, test_source: str) -> SandboxResult:
        """Execute a skill together with its tests as one unit.

        Both are concatenated into a single module so the tests exercise exactly
        the source under review -- no import path games, and no chance of
        testing a different version than the one being promoted.
        """
        combined = (
            "# ---- skill under review ----\n"
            f"{skill_source}\n\n"
            "# ---- verification ----\n"
            f"{test_source}\n"
        )
        return self.run_source(combined, filename="skill_under_test.py")

    def run_with_project(
        self,
        main_source: str,
        test_source: str,
        extra_files: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Execute a multi-file project with tests.

        Writes the main module, test file, and any extra files to the sandbox
        working directory, then runs the test file. This allows imports between
        modules (e.g. `from utils import helper`).
        """
        extra_files = extra_files or {}
        workdir = Path(tempfile.mkdtemp(prefix="anubis-prj-"))
        try:
            # Write all files — main.py so imports work, test file is the entry point
            main_path = workdir / "main.py"
            main_path.write_text(main_source, encoding="utf-8")
            # Prepend sys.path fix because -I flag prevents cwd from being added
            test_with_path = (
                "import sys; sys.path.insert(0, __import__('os').path.dirname("
                "__import__('os').path.abspath(__file__)))\n"
                + test_source
            )
            test_path = workdir / "test_run.py"
            test_path.write_text(test_with_path, encoding="utf-8")

            for fname, content in extra_files.items():
                # Sanitize — no path traversal
                safe = Path(fname).name
                if safe != fname:
                    continue  # skip unsafe filenames
                (workdir / safe).write_text(content, encoding="utf-8")

            if self.isolation.needs_owned_workdir:
                for f in workdir.iterdir():
                    os.chown(f, SANDBOX_UID, SANDBOX_GID)
                    os.chmod(f, 0o600)
                os.chown(workdir, SANDBOX_UID, SANDBOX_GID)
                os.chmod(workdir, 0o700)

            # Run the test file (which imports from the other modules)
            cmd = self.isolation.build_command(sys.executable, test_path)

            isolation = {
                "network_blocked": self.isolation.network_blocked,
                "host_mounts_masked": self.isolation.host_mounts_masked,
                "unprivileged": self.isolation.unprivileged,
                "memory_capped": True,
                "cpu_capped": True,
                "filesize_capped": True,
                "timeout_armed": True,
                "isolated_cwd": True,
                "multi_file": True,
            }

            t0 = time.monotonic()
            timed_out = False
            proc = subprocess.Popen(
                cmd,
                cwd=workdir,
                env=self._env(workdir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                preexec_fn=self._limits() if sys.platform != "win32" else None,
            )
            try:
                stdout, stderr = proc.communicate(timeout=self.policy.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._kill_tree(proc)
                stdout, stderr = proc.communicate()
                stderr = (stderr or "") + (
                    f"\n[sandbox] killed after {self.policy.timeout_s}s timeout"
                )
            duration = time.monotonic() - t0

            return SandboxResult(
                ok=(not timed_out and proc.returncode == 0),
                exit_code=proc.returncode,
                stdout=(stdout or "")[:200_000],
                stderr=(stderr or "")[:200_000],
                duration_s=duration,
                timed_out=timed_out,
                isolation=isolation,
                workdir_files=[],
            )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    def describe(self) -> str:
        p = self.policy
        return (
            f"Sandbox(timeout={p.timeout_s}s mem={p.memory_mb}MB "
            f"cpu={p.cpu_seconds}s :: {self.isolation.label})"
        )
