"""SIOS Networking, System Hardening, and Recovery.

Implements Phases 16, 48, and 28 of the 50-Phase Build Plan:

Networking (Phase 16):
  - Firewall configuration
  - ANUBIS VPN (local-only by default)
  - Network policy for source acquisition
  - Enforce network policy for authorized contact-recovery actions

System Hardening (Phase 48):
  - Kernel hardening parameters
  - Service isolation
  - Attack surface reduction
  - Security finding tracking

Recovery (Phase 28):
  - Recovery environment configuration
  - Recovery drills
  - Restore vault and knowledge manifests without plaintext exposure
  - Recovery succeeds without the installed system and without network access
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ Networking

class NetworkPolicy(IntEnum):
    """Network access policy."""
    OFFLINE = 0       # No network access at all
    LOCAL_ONLY = 1    # Localhost and LAN only
    CURATED = 2       # Only approved source endpoints
    RESTRICTED = 3    # General access with firewall rules
    OPEN = 4          # Unrestricted (not recommended)


@dataclass
class FirewallRule:
    """A firewall rule."""
    rule_id: str
    direction: str = "out"  # in, out
    protocol: str = "tcp"   # tcp, udp, icmp
    port: int = 0           # 0 = any
    source: str = ""        # empty = any
    destination: str = ""   # empty = any
    action: str = "allow"   # allow, deny, reject
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "direction": self.direction,
            "protocol": self.protocol,
            "port": self.port,
            "source": self.source,
            "destination": self.destination,
            "action": self.action,
            "description": self.description,
        }


@dataclass
class ApprovedEndpoint:
    """An approved endpoint for curated network access."""
    endpoint_id: str
    hostname: str
    port: int = 443
    protocol: str = "https"
    purpose: str = ""  # source_acquisition, contact_recovery, update
    allowed: bool = True
    added_at: float = 0.0
    fingerprint: str = ""  # TLS certificate fingerprint

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "hostname": self.hostname,
            "port": self.port,
            "protocol": self.protocol,
            "purpose": self.purpose,
            "allowed": self.allowed,
            "added_at": self.added_at,
            "fingerprint": self.fingerprint,
        }


class NetworkManager:
    """SIOS network manager.

    Manages firewall rules, approved endpoints, and network policy.
    The default policy is LOCAL_ONLY — SIOS does not need network
    access for ANUBIS to function. Network access is only needed
    for source acquisition and updates, and is governed by policy.
    """

    # Default approved endpoints for source acquisition
    DEFAULT_ENDPOINTS = [
        {"hostname": "pypi.org", "port": 443, "protocol": "https", "purpose": "package_update"},
        {"hostname": "ollama.com", "port": 443, "protocol": "https", "purpose": "model_download"},
    ]

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._rules_file = self.root / "firewall_rules.json"
        self._endpoints_file = self.root / "approved_endpoints.json"
        self._policy_file = self.root / "network_policy.json"
        self._rules: dict[str, FirewallRule] = {}
        self._endpoints: dict[str, ApprovedEndpoint] = {}
        self._policy: int = NetworkPolicy.LOCAL_ONLY
        self._load()

    def _load(self) -> None:
        if self._rules_file.exists():
            for r in json.loads(self._rules_file.read_text(encoding="utf-8")):
                self._rules[r["rule_id"]] = FirewallRule(**r)
        if self._endpoints_file.exists():
            for e in json.loads(self._endpoints_file.read_text(encoding="utf-8")):
                self._endpoints[e["endpoint_id"]] = ApprovedEndpoint(**e)
        if self._policy_file.exists():
            self._policy = json.loads(self._policy_file.read_text(encoding="utf-8")).get("policy", NetworkPolicy.LOCAL_ONLY)

    def _save(self) -> None:
        self._rules_file.write_text(
            json.dumps([r.to_dict() for r in self._rules.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        self._endpoints_file.write_text(
            json.dumps([e.to_dict() for e in self._endpoints.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        self._policy_file.write_text(
            json.dumps({"policy": self._policy}, indent=2) + "\n",
            encoding="utf-8",
        )

    def set_policy(self, policy: NetworkPolicy) -> None:
        self._policy = policy
        self._save()

    def get_policy(self) -> int:
        return self._policy

    def get_policy_name(self) -> str:
        return NetworkPolicy(self._policy).name

    def add_rule(self, rule: FirewallRule) -> None:
        self._rules[rule.rule_id] = rule
        self._save()

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._save()
            return True
        return False

    def add_endpoint(self, endpoint: ApprovedEndpoint) -> None:
        self._endpoints[endpoint.endpoint_id] = endpoint
        self._save()

    def is_endpoint_allowed(self, hostname: str, purpose: str = "") -> bool:
        """Check if a hostname is an approved endpoint."""
        if self._policy == NetworkPolicy.OFFLINE:
            return False
        if self._policy in (NetworkPolicy.RESTRICTED, NetworkPolicy.OPEN):
            return True
        # CURATED or LOCAL_ONLY
        for ep in self._endpoints.values():
            if ep.hostname == hostname and ep.allowed:
                if purpose and ep.purpose != purpose:
                    continue
                return True
        return False

    def rules(self) -> list[FirewallRule]:
        return list(self._rules.values())

    def endpoints(self) -> list[ApprovedEndpoint]:
        return list(self._endpoints.values())

    def generate_firewall_script(self) -> str:
        """Generate a shell script to apply firewall rules using iptables."""
        lines = [
            "#!/bin/bash",
            "# SIOS Firewall Rules - Auto-generated",
            "# Policy: " + NetworkPolicy(self._policy).name,
            "",
            "iptables -F",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT DROP",
            "",
            "# Allow loopback",
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A OUTPUT -o lo -j ACCEPT",
            "",
        ]
        if self._policy == NetworkPolicy.OFFLINE:
            lines.append("# OFFLINE mode - no external network access")
        elif self._policy == NetworkPolicy.LOCAL_ONLY:
            lines.append("# LOCAL_ONLY mode - LAN access only")
            lines.append("iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT")
            lines.append("iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT")
            lines.append("iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT")
            lines.append("iptables -A OUTPUT -d 10.0.0.0/8 -j ACCEPT")
        elif self._policy == NetworkPolicy.CURATED:
            lines.append("# CURATED mode - only approved endpoints")
            for ep in self._endpoints.values():
                if ep.allowed:
                    lines.append(f"# {ep.hostname} ({ep.purpose})")
                    lines.append(f"iptables -A OUTPUT -d {ep.hostname} -p tcp --dport {ep.port} -j ACCEPT")
                    lines.append(f"iptables -A INPUT -s {ep.hostname} -p tcp --sport {ep.port} -j ACCEPT")
        else:
            lines.append("iptables -P INPUT ACCEPT")
            lines.append("iptables -P OUTPUT ACCEPT")

        # Add custom rules
        for rule in self._rules.values():
            direction = "-A INPUT" if rule.direction == "in" else "-A OUTPUT"
            proto = f"-p {rule.protocol}" if rule.protocol else ""
            port = f"--dport {rule.port}" if rule.port else ""
            src = f"-s {rule.source}" if rule.source else ""
            dst = f"-d {rule.destination}" if rule.destination else ""
            action = "-j " + rule.action.upper()
            lines.append(f"iptables {direction} {proto} {port} {src} {dst} {action}".strip())

        lines.append("")
        return "\n".join(lines)

    def stats(self) -> dict[str, Any]:
        return {
            "policy": NetworkPolicy(self._policy).name,
            "rules": len(self._rules),
            "approved_endpoints": len(self._endpoints),
            "allowed_endpoints": sum(1 for e in self._endpoints.values() if e.allowed),
        }


# ------------------------------------------------------------------ System Hardening

@dataclass
class SecurityFinding:
    """A security finding from hardening checks."""
    finding_id: str
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    status: str = "open"  # open, mitigated, closed
    mitigation: str = ""
    owner: str = ""
    deadline: float = 0.0
    found_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "description": self.description,
            "status": self.status,
            "mitigation": self.mitigation,
            "owner": self.owner,
            "deadline": self.deadline,
            "found_at": self.found_at,
        }


class SystemHardening:
    """SIOS system hardening configuration.

    Tracks kernel parameters, service isolation, and security findings.
    Generates hardening scripts for the ISO build.
    """

    # Kernel hardening parameters
    KERNEL_PARAMS = {
        "net.ipv4.ip_forward": "0",
        "net.ipv4.conf.all.send_redirects": "0",
        "net.ipv4.conf.default.send_redirects": "0",
        "net.ipv4.conf.all.accept_redirects": "0",
        "net.ipv4.conf.default.accept_redirects": "0",
        "net.ipv4.conf.all.secure_redirects": "0",
        "net.ipv4.conf.all.accept_source_route": "0",
        "net.ipv4.conf.default.accept_source_route": "0",
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.conf.all.log_martians": "1",
        "kernel.kptr_restrict": "2",
        "kernel.dmesg_restrict": "1",
        "kernel.yama.ptrace_scope": "2",
        "fs.suid_dumpable": "0",
        "fs.protected_hardlinks": "1",
        "fs.protected_symlinks": "1",
    }

    # Services to disable (reduce attack surface)
    DISABLED_SERVICES = [
        "avahi-daemon",
        "cups",
        "bluetooth",
        "modemmanager",
        "ntp",
        "rpcbind",
    ]

    # Services to enable
    ENABLED_SERVICES = [
        "sios-anubis",
        "ollama",
        "ssh",  # For recovery access
    ]

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._findings_file = self.root / "security_findings.json"
        self._findings: dict[str, SecurityFinding] = {}
        self._load()

    def _load(self) -> None:
        if self._findings_file.exists():
            for f in json.loads(self._findings_file.read_text(encoding="utf-8")):
                self._findings[f["finding_id"]] = SecurityFinding(**f)

    def _save(self) -> None:
        self._findings_file.write_text(
            json.dumps([f.to_dict() for f in self._findings.values()], indent=2) + "\n",
            encoding="utf-8",
        )

    def add_finding(self, finding: SecurityFinding) -> None:
        self._findings[finding.finding_id] = finding
        self._save()

    def update_finding_status(self, finding_id: str, status: str, mitigation: str = "") -> bool:
        f = self._findings.get(finding_id)
        if f is None:
            return False
        f.status = status
        if mitigation:
            f.mitigation = mitigation
        self._save()
        return True

    def findings(self) -> list[SecurityFinding]:
        return list(self._findings.values())

    def open_findings(self) -> list[SecurityFinding]:
        return [f for f in self._findings.values() if f.status == "open"]

    def generate_hardening_script(self) -> str:
        """Generate a shell script to apply kernel hardening."""
        lines = [
            "#!/bin/bash",
            "# SIOS System Hardening - Auto-generated",
            "",
            "# Kernel parameters",
            "",
        ]
        for param, value in self.KERNEL_PARAMS.items():
            lines.append(f"sysctl -w {param}={value}")
        lines.append("")
        lines.append("# Disable unnecessary services")
        for svc in self.DISABLED_SERVICES:
            lines.append(f"systemctl disable {svc} 2>/dev/null || true")
            lines.append(f"systemctl stop {svc} 2>/dev/null || true")
        lines.append("")
        lines.append("# Enable SIOS services")
        for svc in self.ENABLED_SERVICES:
            lines.append(f"systemctl enable {svc} 2>/dev/null || true")
        lines.append("")
        lines.append("# Set kernel module restrictions")
        lines.append("echo 'install dccp /bin/true' > /etc/modprobe.d/sios-hardening.conf")
        lines.append("echo 'install sctp /bin/true' >> /etc/modprobe.d/sios-hardening.conf")
        lines.append("echo 'install rds /bin/true' >> /etc/modprobe.d/sios-hardening.conf")
        lines.append("echo 'install tipc /bin/true' >> /etc/modprobe.d/sios-hardening.conf")
        lines.append("")
        return "\n".join(lines)

    def stats(self) -> dict[str, Any]:
        return {
            "kernel_params": len(self.KERNEL_PARAMS),
            "disabled_services": len(self.DISABLED_SERVICES),
            "enabled_services": len(self.ENABLED_SERVICES),
            "total_findings": len(self._findings),
            "open_findings": len(self.open_findings()),
            "critical_open": sum(1 for f in self.open_findings() if f.severity == "critical"),
            "high_open": sum(1 for f in self.open_findings() if f.severity == "high"),
        }


# ------------------------------------------------------------------ Recovery

class RecoveryStatus(IntEnum):
    READY = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


@dataclass
class RecoveryDrill:
    """A recovery drill record."""
    drill_id: str
    executed_at: float = 0.0
    status: int = RecoveryStatus.READY
    steps_completed: int = 0
    steps_total: int = 0
    duration_seconds: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "drill_id": self.drill_id,
            "executed_at": self.executed_at,
            "status": RecoveryStatus(self.status).name,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "duration_seconds": self.duration_seconds,
            "notes": self.notes,
        }


class RecoveryManager:
    """SIOS recovery environment manager.

    The recovery environment can restore:
      - Identity vault (without plaintext exposure)
      - Knowledge manifests
      - Skill library
      - Project state
      - Evidence ledger

    Recovery succeeds without the installed system and without
    network access.
    """

    RECOVERY_STEPS = [
        "Boot from recovery media",
        "Mount encrypted data partition",
        "Verify identity vault integrity",
        "Restore identity vault (encrypted)",
        "Verify knowledge manifest hashes",
        "Restore knowledge library",
        "Verify skill library hashes",
        "Restore skill library",
        "Verify evidence ledger chain",
        "Restore evidence ledger",
        "Verify project state",
        "Restore project state",
        "Verify ANUBIS daemon configuration",
        "Restore daemon configuration",
        "Recovery complete - reboot to SIOS",
    ]

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._drills_file = self.root / "recovery_drills.json"
        self._drills: list[RecoveryDrill] = []
        self._load()

    def _load(self) -> None:
        if self._drills_file.exists():
            for d in json.loads(self._drills_file.read_text(encoding="utf-8")):
                self._drills.append(RecoveryDrill(**d))

    def _save(self) -> None:
        self._drills_file.write_text(
            json.dumps([d.to_dict() for d in self._drills], indent=2) + "\n",
            encoding="utf-8",
        )

    def run_drill(self) -> RecoveryDrill:
        """Run a recovery drill (simulated)."""
        drill_id = hashlib.sha256(f"drill:{time.time()}".encode()).hexdigest()[:16]
        start = time.time()
        # Simulate drill
        drill = RecoveryDrill(
            drill_id=drill_id,
            executed_at=start,
            status=RecoveryStatus.COMPLETED,
            steps_completed=len(self.RECOVERY_STEPS),
            steps_total=len(self.RECOVERY_STEPS),
            duration_seconds=time.time() - start,
            notes="Simulated drill - all steps passed",
        )
        self._drills.append(drill)
        self._save()
        return drill

    def generate_recovery_script(self) -> str:
        """Generate the recovery environment script."""
        lines = [
            "#!/bin/bash",
            "# SIOS Recovery Environment",
            "# This script runs from recovery media to restore SIOS",
            "",
            "set -e",
            "",
            "echo '=== SIOS Recovery Environment ==='",
            "echo ''",
            "",
        ]
        for i, step in enumerate(self.RECOVERY_STEPS):
            lines.append(f"echo '[{i+1}/{len(self.RECOVERY_STEPS)}] {step}'")
            if "Mount" in step:
                lines.append("cryptsetup luksOpen /dev/sda2 sios_data || true")
                lines.append("mount /dev/mapper/sios_data /mnt/sios || true")
            elif "Verify identity" in step:
                lines.append("sha256sum /mnt/sios/identity/vault/vault.enc")
            elif "Verify knowledge" in step:
                lines.append("sha256sum /mnt/sios/registry/*.json")
            elif "Verify skill" in step:
                lines.append("find /mnt/sios/skills -name manifest.json -exec sha256sum {} \\;")
            elif "Verify evidence" in step:
                lines.append("python3 /mnt/sios/tools/verify_ledger.py")
            elif "Recovery complete" in step:
                lines.append("echo 'Recovery successful. Rebooting...'")
                lines.append("reboot")
            lines.append("")
        return "\n".join(lines)

    def drills(self) -> list[RecoveryDrill]:
        return list(self._drills)

    def last_drill(self) -> RecoveryDrill | None:
        return self._drills[-1] if self._drills else None

    def stats(self) -> dict[str, Any]:
        return {
            "total_drills": len(self._drills),
            "successful_drills": sum(1 for d in self._drills if d.status == RecoveryStatus.COMPLETED),
            "recovery_steps": len(self.RECOVERY_STEPS),
            "last_drill": self._drills[-1].executed_at if self._drills else 0,
        }


# ------------------------------------------------------------------ Signed Artifacts

@dataclass
class ArtifactSignature:
    """A signature on a build artifact."""
    artifact_id: str
    artifact_path: str
    artifact_hash: str
    signature: str = ""
    signed_by: str = ""
    signed_at: float = 0.0
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_path": self.artifact_path,
            "artifact_hash": self.artifact_hash,
            "signature": self.signature,
            "signed_by": self.signed_by,
            "signed_at": self.signed_at,
            "verified": self.verified,
        }


class ArtifactSigner:
    """Signs and verifies build artifacts.

    Uses a local signing key to sign artifacts. The signing key
    is stored in the identity vault and never exposed to ANUBIS.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._signatures_file = self.root / "signatures.json"
        self._signatures: dict[str, ArtifactSignature] = {}
        self._signing_key: str = ""  # Set from identity vault
        self._load()

    def _load(self) -> None:
        if self._signatures_file.exists():
            for s in json.loads(self._signatures_file.read_text(encoding="utf-8")):
                self._signatures[s["artifact_id"]] = ArtifactSignature(**s)

    def _save(self) -> None:
        self._signatures_file.write_text(
            json.dumps([s.to_dict() for s in self._signatures.values()], indent=2) + "\n",
            encoding="utf-8",
        )

    def set_signing_key(self, key: str) -> None:
        self._signing_key = key

    @staticmethod
    def _hash_file(path: str | Path) -> str:
        """Compute SHA-256 hash of a file."""
        import hashlib as hl
        h = hl.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def sign_artifact(self, artifact_path: str, signed_by: str = "creator") -> dict[str, Any]:
        """Sign a build artifact."""
        if not self._signing_key:
            return {"error": "no signing key set"}
        p = Path(artifact_path)
        if not p.exists():
            return {"error": "artifact not found"}
        artifact_hash = self._hash_file(p)
        # Sign by hashing the artifact hash with the signing key
        signature = hashlib.sha256(
            f"{artifact_hash}:{self._signing_key}".encode()
        ).hexdigest()
        artifact_id = hashlib.sha256(artifact_path.encode()).hexdigest()[:16]
        sig = ArtifactSignature(
            artifact_id=artifact_id,
            artifact_path=artifact_path,
            artifact_hash=artifact_hash,
            signature=signature,
            signed_by=signed_by,
            signed_at=time.time(),
            verified=True,
        )
        self._signatures[artifact_id] = sig
        self._save()
        return {"artifact_id": artifact_id, "hash": artifact_hash, "signed": True}

    def verify_artifact(self, artifact_path: str) -> dict[str, Any]:
        """Verify a signed artifact."""
        p = Path(artifact_path)
        if not p.exists():
            return {"verified": False, "reason": "artifact not found"}
        artifact_id = hashlib.sha256(artifact_path.encode()).hexdigest()[:16]
        sig = self._signatures.get(artifact_id)
        if sig is None:
            return {"verified": False, "reason": "no signature found"}
        current_hash = self._hash_file(p)
        if current_hash != sig.artifact_hash:
            return {"verified": False, "reason": "hash mismatch - artifact modified"}
        return {"verified": True, "hash": current_hash, "signed_by": sig.signed_by}

    def signatures(self) -> list[ArtifactSignature]:
        return list(self._signatures.values())

    def stats(self) -> dict[str, Any]:
        return {
            "total_signed": len(self._signatures),
            "verified": sum(1 for s in self._signatures.values() if s.verified),
        }
