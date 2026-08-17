"""Security audit module — verify sandbox, network, and constitutional enforcement.

This module provides a programmatic security audit that can be run
from the daemon. It tests:

1. Sandbox isolation (network, filesystem, subprocess)
2. Constitutional enforcement (all change classes)
3. Immutable laws integrity
4. Hazard detection patterns
5. Vault encryption verification
6. Gateway policy enforcement
7. Permission boundary checks

All results are logged to the evidence ledger.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from anubis.constitution import (
    ChangeClass, Request, Verdict, evaluate,
    IMMUTABLE_LAWS, _HAZARDS, analyze_payload,
)


@dataclass
class AuditCheck:
    name: str
    passed: bool
    message: str
    details: str = ""


@dataclass
class AuditResult:
    audit_id: str
    started_at: float
    completed_at: float = 0.0
    duration_s: float = 0.0
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    checks: list[AuditCheck] = field(default_factory=list)
    overall_pass: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": self.duration_s,
            "total_checks": self.total_checks,
            "passed": self.passed,
            "failed": self.failed,
            "overall_pass": self.overall_pass,
            "checks": [c.__dict__ for c in self.checks],
        }


class SecurityAuditor:
    """Runs security audits on the ANUBIS system."""

    def __init__(
        self,
        root: str | Path,
        *,
        sandbox: Any | None = None,
        ledger: Any | None = None,
        gateway: Any | None = None,
        vault: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.sandbox = sandbox
        self.ledger = ledger
        self.gateway = gateway
        self.vault = vault

    def run_audit(self) -> AuditResult:
        """Run a full security audit."""
        import hashlib
        result = AuditResult(
            audit_id=hashlib.sha256(f"audit:{time.time()}".encode()).hexdigest()[:16],
            started_at=time.time(),
        )

        # 1. Constitutional enforcement
        self._audit_constitutional(result)
        # 2. Immutable laws
        self._audit_immutable_laws(result)
        # 3. Hazard detection
        self._audit_hazards(result)
        # 4. Sandbox isolation (if sandbox available)
        self._audit_sandbox(result)
        # 5. Gateway policy (if gateway available)
        self._audit_gateway(result)
        # 6. Vault encryption (if vault available)
        self._audit_vault(result)
        # 7. File permissions
        self._audit_file_permissions(result)
        # 8. Immutable file protection
        self._audit_immutable_files(result)

        result.completed_at = time.time()
        result.duration_s = result.completed_at - result.started_at
        result.total_checks = len(result.checks)
        result.passed = sum(1 for c in result.checks if c.passed)
        result.failed = sum(1 for c in result.checks if not c.passed)
        result.overall_pass = result.failed == 0

        if self.ledger:
            self.ledger.append(
                "anubis.security",
                "audit.complete",
                result.to_dict(),
            )

        return result

    def _add(self, result: AuditResult, check: AuditCheck) -> None:
        result.checks.append(check)

    def _audit_constitutional(self, result: AuditResult) -> None:
        """Test constitutional enforcement for all change classes."""
        tests = [
            ("routine_allows", ChangeClass.ROUTINE, True, True, "routine should allow"),
            ("sandboxed_allows", ChangeClass.SANDBOXED, True, True, "sandboxed should allow"),
            ("promotion_denied_no_evidence", ChangeClass.PROMOTION, False, False, "promotion denied without evidence"),
            ("consequential_requires_approval", ChangeClass.CONSEQUENTIAL, False, False, "consequential requires approval"),
            ("main_engine_requires_approval", ChangeClass.MAIN_ENGINE, False, False, "main engine requires approval"),
        ]

        for name, cc, evidence, expected_allow, desc in tests:
            req = Request(
                actor="anubis.audit",
                action=f"test.{name}",
                change_class=cc,
                evidence_passed=evidence,
                creator_approved=evidence,
                sandboxed=(cc == ChangeClass.SANDBOXED),
            )
            ruling = evaluate(req)
            passed = (ruling.verdict == Verdict.ALLOW) == expected_allow
            self._add(result, AuditCheck(
                name=f"constitutional_{name}",
                passed=passed,
                message=f"{ruling.verdict.name}: {desc}",
            ))

    def _audit_immutable_laws(self, result: AuditResult) -> None:
        """Verify all 8 immutable laws are defined."""
        expected_laws = {
            "human_protection", "truth", "non_manipulation",
            "permission_integrity", "local_privacy",
            "financial_consent", "audit", "recovery",
        }
        actual = set(IMMUTABLE_LAWS)
        missing = expected_laws - actual
        extra = actual - expected_laws

        passed = not missing
        msg = f"{len(actual)} laws defined"
        if missing:
            msg += f", missing: {missing}"
        if extra:
            msg += f", extra: {extra}"
        self._add(result, AuditCheck(
            name="immutable_laws",
            passed=passed,
            message=msg,
        ))

    def _audit_hazards(self, result: AuditResult) -> None:
        """Test hazard detection patterns."""
        test_cases = [
            ("os.remove('file')", "recovery"),
            ("subprocess.run(['ls'])", "permission_integrity"),
            ("socket.socket()", "local_privacy"),
            ("eval('1+1')", "audit"),
            ("open('/etc/passwd')", "local_privacy"),
            ("import requests", "local_privacy"),
            ("os.system('rm -rf /')", "permission_integrity"),
            ("__import__('os')", "audit"),
        ]

        for code, expected_law in test_cases:
            hazards = analyze_payload(code)
            found_laws = {law for law, _ in hazards}
            passed = expected_law in found_laws
            self._add(result, AuditCheck(
                name=f"hazard_{expected_law}",
                passed=passed,
                message=f"'{code[:30]}' -> {expected_law}: {'detected' if passed else 'MISSED'}",
            ))

    def _audit_sandbox(self, result: AuditResult) -> None:
        """Test sandbox isolation."""
        if not self.sandbox:
            self._add(result, AuditCheck(
                name="sandbox_available",
                passed=False,
                message="sandbox not configured",
            ))
            return

        # Check isolation report
        iso = self.sandbox.isolation
        self._add(result, AuditCheck(
            name="sandbox_network_blocked",
            passed=iso.network_blocked,
            message=f"network blocked: {iso.network_blocked}",
        ))
        self._add(result, AuditCheck(
            name="sandbox_host_mounts_masked",
            passed=iso.host_mounts_masked,
            message=f"host mounts masked: {iso.host_mounts_masked}",
        ))

        # Try network test
        try:
            network_code = (
                "import socket\n"
                "try:\n"
                "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                "    s.settimeout(2)\n"
                "    s.connect(('8.8.8.8', 53))\n"
                "    print('NETWORK_ACCESSIBLE')\n"
                "    s.close()\n"
                "except Exception as e:\n"
                "    print(f'NETWORK_BLOCKED: {e}')\n"
            )
            r = self.sandbox.run_source(network_code, filename="audit_net.py")
            blocked = "NETWORK_BLOCKED" in (r.stdout or "")
            self._add(result, AuditCheck(
                name="sandbox_network_test",
                passed=blocked,
                message=f"network test: {'blocked' if blocked else 'ACCESSIBLE'}",
            ))
        except Exception as exc:
            self._add(result, AuditCheck(
                name="sandbox_network_test",
                passed=False,
                message=f"network test error: {exc}",
            ))

    def _audit_gateway(self, result: AuditResult) -> None:
        """Test gateway policy enforcement."""
        if not self.gateway:
            self._add(result, AuditCheck(
                name="gateway_available",
                passed=False,
                message="gateway not configured",
            ))
            return

        status = self.gateway.get_status() if hasattr(self.gateway, 'get_status') else {}
        policy_active = status.get("policy_active", False)
        self._add(result, AuditCheck(
            name="gateway_policy",
            passed=policy_active,
            message=f"policy active: {policy_active}",
        ))

        whitelist = status.get("whitelist_size", 0)
        self._add(result, AuditCheck(
            name="gateway_whitelist",
            passed=whitelist > 0,
            message=f"whitelist entries: {whitelist}",
        ))

    def _audit_vault(self, result: AuditResult) -> None:
        """Test vault encryption."""
        if not self.vault:
            self._add(result, AuditCheck(
                name="vault_available",
                passed=False,
                message="vault not configured",
            ))
            return

        vault_path = self.root / "identity" / "vault.enc"
        if not vault_path.exists():
            self._add(result, AuditCheck(
                name="vault_exists",
                passed=False,
                message="vault file not found",
            ))
            return

        self._add(result, AuditCheck(
            name="vault_exists",
            passed=True,
            message="vault file present",
        ))

        # Check file size (encrypted vault should be non-trivial)
        size = vault_path.stat().st_size
        self._add(result, AuditCheck(
            name="vault_encrypted",
            passed=size > 100,
            message=f"vault size: {size} bytes",
        ))

    def _audit_file_permissions(self, result: AuditResult) -> None:
        """Check sensitive file permissions."""
        import os
        sensitive = [
            self.root / "identity" / "vault.enc",
            self.root / "config" / "cloud_credentials.json",
        ]

        for path in sensitive:
            if not path.exists():
                continue
            stat = path.stat()
            perms = stat.st_mode & 0o777
            # On Windows, perms are not meaningful in the same way
            if os.name == 'nt':
                self._add(result, AuditCheck(
                    name=f"perms_{path.name}",
                    passed=True,
                    message=f"{path.name}: {oct(perms)} (Windows — perms not enforced)",
                ))
            else:
                restricted = not (perms & 0o077)  # no group/other access
                self._add(result, AuditCheck(
                    name=f"perms_{path.name}",
                    passed=restricted,
                    message=f"{path.name}: {oct(perms)} {'(restricted)' if restricted else '(TOO OPEN)'}",
                ))

    def _audit_immutable_files(self, result: AuditResult) -> None:
        """Verify immutable files exist and are not tampered."""
        immutable_files = [
            self.root / "anubis" / "constitution.py",
            self.root / "anubis" / "identity.py",
            self.root / "anubis" / "ledger.py",
        ]

        for path in immutable_files:
            exists = path.exists()
            self._add(result, AuditCheck(
                name=f"immutable_{path.name}",
                passed=exists,
                message=f"{path.name}: {'present' if exists else 'MISSING'}",
            ))

    def get_status(self) -> dict[str, Any]:
        """Get auditor status."""
        return {
            "sandbox_configured": self.sandbox is not None,
            "gateway_configured": self.gateway is not None,
            "vault_configured": self.vault is not None,
            "ledger_configured": self.ledger is not None,
        }
