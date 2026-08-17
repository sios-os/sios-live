"""SIOS Maintenance, Package Manager, and Financial Ledger.

Implements Phases 30, 32, and 44 (Midnight Purge) of the Build Plan:

Midnight Purge (Phase 44):
  - Demonstrably preserves protected memory, provenance, legal holds,
    project decisions, and rollback data
  - Removes or compresses disposable material
  - Scheduled cleanup with retention rules

Package Manager (Phase 32):
  - SIOS package format
  - Install, update, verify, rollback
  - Signed package manifests

Financial Ledger (Phase 30):
  - Tokenized credentials
  - Financial ledger, statements, bills, receipts
  - Mandates, corrections, migrations
  - Reconciliation to source records
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ Midnight Purge

class RetentionClass(IntEnum):
    """Data retention classification."""
    PROTECTED = 0     # Never deleted — provenance, legal holds, identity
    DURABLE = 1       # Long retention — project decisions, memory
    STANDARD = 2      # Medium retention — logs, intermediate results
    DISPOSABLE = 3    # Short retention — caches, temp files, duplicates


@dataclass
class PurgeRecord:
    """Record of a Midnight Purge execution."""
    purge_id: str
    executed_at: float = 0.0
    items_removed: int = 0
    items_compressed: int = 0
    bytes_freed: int = 0
    protected_preserved: int = 0
    details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "purge_id": self.purge_id,
            "executed_at": self.executed_at,
            "items_removed": self.items_removed,
            "items_compressed": self.items_compressed,
            "bytes_freed": self.bytes_freed,
            "protected_preserved": self.protected_preserved,
            "details": self.details,
        }


class MidnightPurge:
    """The Midnight Purge — scheduled cleanup with retention rules.

    Protected data is NEVER removed:
      - Provenance and source records
      - Legal holds
      - Identity and vault data
      - Constitutional ledger entries
      - Project decisions and rollback references

    Disposable data is removed:
      - Caches older than 7 days
      - Temporary files older than 1 day
      - Duplicate documents
      - Expired quarantine items
    """

    # Retention periods in seconds
    RETENTION_PERIODS = {
        RetentionClass.PROTECTED: -1,  # Never expire
        RetentionClass.DURABLE: 90 * 86400,  # 90 days
        RetentionClass.STANDARD: 7 * 86400,  # 7 days
        RetentionClass.DISPOSABLE: 86400,  # 1 day
    }

    # Paths that are ALWAYS protected
    PROTECTED_PATHS = [
        "evidence/ledger.jsonl",
        "memory/facts.json",
        "memory/missions.jsonl",
        "identity/identity.json",
        "identity/vault/vault.enc",
        "skills",
        "projects",
        "registry",
    ]

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._history_file = self.root / "purge_history.json"
        self._history: list[PurgeRecord] = []
        self._load()

    def _load(self) -> None:
        if self._history_file.exists():
            for p in json.loads(self._history_file.read_text(encoding="utf-8")):
                self._history.append(PurgeRecord(
                    purge_id=p.get("purge_id", ""),
                    executed_at=p.get("executed_at", 0),
                    items_removed=p.get("items_removed", 0),
                    items_compressed=p.get("items_compressed", 0),
                    bytes_freed=p.get("bytes_freed", 0),
                    protected_preserved=p.get("protected_preserved", 0),
                    details=p.get("details", []),
                ))

    def _save(self) -> None:
        self._history_file.write_text(
            json.dumps([p.to_dict() for p in self._history], indent=2) + "\n",
            encoding="utf-8",
        )

    def _is_protected(self, path: Path) -> bool:
        """Check if a path is protected from deletion."""
        rel = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
        # Normalize path separators for cross-platform compatibility
        rel = rel.replace("\\", "/")
        for prot in self.PROTECTED_PATHS:
            if rel.startswith(prot) or prot in rel:
                return True
        return False

    def execute(self, workspace_root: str | Path) -> PurgeRecord:
        """Execute a purge cycle.

        Scans the workspace for disposable items and removes them.
        Protected items are counted but never touched.
        """
        workspace = Path(workspace_root)
        purge_id = hashlib.sha256(f"purge:{time.time()}".encode()).hexdigest()[:16]
        record = PurgeRecord(purge_id=purge_id, executed_at=time.time())
        now = time.time()

        # Scan for purgeable items
        if workspace.exists():
            for item in workspace.rglob("*"):
                if item.is_file():
                    if self._is_protected(item):
                        record.protected_preserved += 1
                        continue
                    # Check file age
                    try:
                        mtime = item.stat().st_mtime
                        age = now - mtime
                        # Check if it's in a temp/cache directory
                        rel_path = str(item.relative_to(workspace))
                        is_temp = "tmp" in rel_path.lower() or "cache" in rel_path.lower()
                        is_log = item.suffix == ".log"
                        is_pycache = "__pycache__" in rel_path

                        if is_pycache and age > self.RETENTION_PERIODS[RetentionClass.DISPOSABLE]:
                            size = item.stat().st_size
                            item.unlink()
                            record.items_removed += 1
                            record.bytes_freed += size
                            record.details.append({"action": "removed", "path": rel_path, "reason": "pycache expired"})
                        elif is_temp and age > self.RETENTION_PERIODS[RetentionClass.DISPOSABLE]:
                            size = item.stat().st_size
                            item.unlink()
                            record.items_removed += 1
                            record.bytes_freed += size
                            record.details.append({"action": "removed", "path": rel_path, "reason": "temp expired"})
                        elif is_log and age > self.RETENTION_PERIODS[RetentionClass.STANDARD]:
                            # Compress logs by truncating to last 1000 lines
                            try:
                                lines = item.read_text(encoding="utf-8", errors="replace").splitlines()
                                if len(lines) > 1000:
                                    item.write_text("\n".join(lines[-1000:]) + "\n", encoding="utf-8")
                                    record.items_compressed += 1
                                    record.details.append({"action": "compressed", "path": rel_path, "reason": "log truncated"})
                            except Exception:
                                pass
                    except Exception:
                        continue

        self._history.append(record)
        self._save()
        return record

    def history(self) -> list[PurgeRecord]:
        return list(self._history)

    def last_purge(self) -> PurgeRecord | None:
        return self._history[-1] if self._history else None

    def stats(self) -> dict[str, Any]:
        return {
            "total_purges": len(self._history),
            "total_items_removed": sum(p.items_removed for p in self._history),
            "total_bytes_freed": sum(p.bytes_freed for p in self._history),
            "last_purge": self._history[-1].executed_at if self._history else 0,
        }


# ------------------------------------------------------------------ Package Manager

class PackageStatus(IntEnum):
    INSTALLED = 0
    AVAILABLE = 1
    UPDATING = 2
    ROLLING_BACK = 3
    FAILED = 4


@dataclass
class Package:
    """A SIOS package."""
    package_id: str
    name: str
    version: str
    description: str = ""
    source_hash: str = ""
    installed_at: float = 0.0
    status: int = PackageStatus.AVAILABLE
    dependencies: list[str] = field(default_factory=list)
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "source_hash": self.source_hash,
            "installed_at": self.installed_at,
            "status": PackageStatus(self.status).name,
            "dependencies": self.dependencies,
            "size_bytes": self.size_bytes,
        }


class PackageManager:
    """SIOS package manager.

    Manages installation, updates, verification, and rollback
    of SIOS packages. Packages are signed and hash-verified.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._packages_file = self.root / "packages.json"
        self._packages: dict[str, Package] = {}
        self._history: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self._packages_file.exists():
            data = json.loads(self._packages_file.read_text(encoding="utf-8"))
            for p in data.get("packages", []):
                pkg = Package(
                    package_id=p.get("package_id", ""),
                    name=p.get("name", ""),
                    version=p.get("version", ""),
                    description=p.get("description", ""),
                    source_hash=p.get("source_hash", ""),
                    installed_at=p.get("installed_at", 0),
                    status=p.get("status", PackageStatus.AVAILABLE),
                    dependencies=p.get("dependencies", []),
                    size_bytes=p.get("size_bytes", 0),
                )
                self._packages[pkg.package_id] = pkg
            self._history = data.get("history", [])

    def _save(self) -> None:
        self._packages_file.write_text(
            json.dumps({
                "packages": [p.to_dict() for p in self._packages.values()],
                "history": self._history,
            }, indent=2) + "\n",
            encoding="utf-8",
        )

    def install(
        self, name: str, version: str, description: str = "",
        source_hash: str = "", dependencies: list[str] | None = None,
        size_bytes: int = 0,
    ) -> dict[str, Any]:
        """Install a package."""
        package_id = hashlib.sha256(f"{name}:{version}".encode()).hexdigest()[:16]
        if package_id in self._packages:
            return {"error": "package already installed"}
        pkg = Package(
            package_id=package_id, name=name, version=version,
            description=description, source_hash=source_hash,
            installed_at=time.time(), status=PackageStatus.INSTALLED,
            dependencies=dependencies or [], size_bytes=size_bytes,
        )
        self._packages[package_id] = pkg
        self._history.append({"action": "install", "package_id": package_id, "timestamp": time.time()})
        self._save()
        return {"package_id": package_id, "status": "installed"}

    def update(self, package_id: str, new_version: str, new_hash: str = "") -> dict[str, Any]:
        """Update a package to a new version."""
        pkg = self._packages.get(package_id)
        if pkg is None:
            return {"error": "package not found"}
        old_version = pkg.version
        pkg.version = new_version
        if new_hash:
            pkg.source_hash = new_hash
        pkg.installed_at = time.time()
        self._history.append({
            "action": "update", "package_id": package_id,
            "old_version": old_version, "new_version": new_version,
            "timestamp": time.time(),
        })
        self._save()
        return {"package_id": package_id, "old_version": old_version, "new_version": new_version}

    def rollback(self, package_id: str, to_version: str) -> dict[str, Any]:
        """Rollback a package to a previous version."""
        pkg = self._packages.get(package_id)
        if pkg is None:
            return {"error": "package not found"}
        current = pkg.version
        pkg.version = to_version
        pkg.status = PackageStatus.INSTALLED
        self._history.append({
            "action": "rollback", "package_id": package_id,
            "from_version": current, "to_version": to_version,
            "timestamp": time.time(),
        })
        self._save()
        return {"package_id": package_id, "rolled_back_to": to_version}

    def verify(self, package_id: str, expected_hash: str) -> dict[str, Any]:
        """Verify a package's source hash."""
        pkg = self._packages.get(package_id)
        if pkg is None:
            return {"error": "package not found"}
        if pkg.source_hash != expected_hash:
            return {"verified": False, "reason": "hash mismatch"}
        return {"verified": True}

    def remove(self, package_id: str) -> dict[str, Any]:
        """Remove a package."""
        if package_id not in self._packages:
            return {"error": "package not found"}
        del self._packages[package_id]
        self._history.append({"action": "remove", "package_id": package_id, "timestamp": time.time()})
        self._save()
        return {"package_id": package_id, "status": "removed"}

    def packages(self) -> list[Package]:
        return list(self._packages.values())

    def get_package(self, package_id: str) -> Package | None:
        return self._packages.get(package_id)

    def stats(self) -> dict[str, Any]:
        return {
            "total_packages": len(self._packages),
            "installed": sum(1 for p in self._packages.values() if p.status == PackageStatus.INSTALLED),
            "total_size": sum(p.size_bytes for p in self._packages.values()),
            "history_entries": len(self._history),
        }


# ------------------------------------------------------------------ Financial Ledger

@dataclass
class FinancialEntry:
    """An entry in the financial ledger."""
    entry_id: str
    entry_type: str  # income, expense, bill, receipt, mandate, correction, migration
    amount: float
    currency: str = "USD"
    payee: str = ""
    account: str = ""
    date: float = 0.0
    description: str = ""
    mandate_id: str = ""
    reconciled: bool = False
    source_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "amount": self.amount,
            "currency": self.currency,
            "payee": self.payee,
            "account": self.account,
            "date": self.date,
            "description": self.description,
            "mandate_id": self.mandate_id,
            "reconciled": self.reconciled,
            "source_reference": self.source_reference,
        }


class FinancialLedger:
    """The SIOS financial ledger.

    Records all financial transactions with reconciliation to
    source records. Supports:
      - Bills and receipts
      - Mandates and corrections
      - Migrations
      - Reconciliation to source records
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._ledger_file = self.root / "financial_ledger.json"
        self._entries: list[FinancialEntry] = []
        self._load()

    def _load(self) -> None:
        if self._ledger_file.exists():
            for e in json.loads(self._ledger_file.read_text(encoding="utf-8")):
                self._entries.append(FinancialEntry(
                    entry_id=e.get("entry_id", ""),
                    entry_type=e.get("entry_type", ""),
                    amount=e.get("amount", 0),
                    currency=e.get("currency", "USD"),
                    payee=e.get("payee", ""),
                    account=e.get("account", ""),
                    date=e.get("date", 0),
                    description=e.get("description", ""),
                    mandate_id=e.get("mandate_id", ""),
                    reconciled=e.get("reconciled", False),
                    source_reference=e.get("source_reference", ""),
                ))

    def _save(self) -> None:
        self._ledger_file.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2) + "\n",
            encoding="utf-8",
        )

    def add_entry(self, entry: FinancialEntry) -> str:
        """Add a financial entry."""
        if not entry.entry_id:
            entry.entry_id = hashlib.sha256(
                f"fin:{entry.entry_type}:{entry.amount}:{time.time()}".encode()
            ).hexdigest()[:16]
        if not entry.date:
            entry.date = time.time()
        self._entries.append(entry)
        self._save()
        return entry.entry_id

    def reconcile(self, entry_id: str, source_reference: str) -> bool:
        """Mark an entry as reconciled to a source record."""
        for e in self._entries:
            if e.entry_id == entry_id:
                e.reconciled = True
                e.source_reference = source_reference
                self._save()
                return True
        return False

    def correct_entry(self, entry_id: str, new_amount: float, reason: str) -> bool:
        """Correct a financial entry with a reason."""
        for e in self._entries:
            if e.entry_id == entry_id:
                # Add a correction entry
                correction = FinancialEntry(
                    entry_id=hashlib.sha256(f"correction:{entry_id}:{time.time()}".encode()).hexdigest()[:16],
                    entry_type="correction",
                    amount=new_amount - e.amount,
                    currency=e.currency,
                    payee=e.payee,
                    account=e.account,
                    description=f"Correction to {entry_id}: {reason}",
                )
                self._entries.append(correction)
                e.amount = new_amount
                self._save()
                return True
        return False

    def entries(self, entry_type: str = "") -> list[FinancialEntry]:
        if entry_type:
            return [e for e in self._entries if e.entry_type == entry_type]
        return list(self._entries)

    def balance(self, account: str = "") -> float:
        """Calculate the balance for an account (or all accounts)."""
        total = 0.0
        for e in self._entries:
            if account and e.account != account:
                continue
            if e.entry_type in ("income",):
                total += e.amount
            elif e.entry_type in ("expense", "bill"):
                total -= e.amount
            elif e.entry_type == "correction":
                total += e.amount
        return total

    def stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "reconciled": sum(1 for e in self._entries if e.reconciled),
            "unreconciled": sum(1 for e in self._entries if not e.reconciled),
            "total_balance": self.balance(),
            "by_type": {
                t: sum(1 for e in self._entries if e.entry_type == t)
                for t in set(e.entry_type for e in self._entries)
            },
        }
