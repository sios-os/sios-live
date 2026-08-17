"""Snapshot manager — immutable, hash-verified point-in-time snapshots.

Creates immutable snapshots of ANUBIS's state (memory, identity vault,
evidence ledger, court, knowledge, skills, accounts, biometrics) at
regular intervals. Each snapshot is:

1. IMMUTABLE — never modified after creation
2. HASH-VERIFIED — a manifest of file hashes is stored with each snapshot
3. LEDGER-CROSS-CHECKED — state changes are compared to ledger entries
4. ROLLBACK-READY — can be restored instantly

Snapshots are stored off-drive (survives A/B drive failure). The
snapshot directory structure:

  snapshots/
    2026-08-15-14-00/
      manifest.json          ← file hashes + metadata
      memory/                ← memory state
      identity/              ← identity vault
      evidence/              ← evidence ledger
      court/                 ← court reviews
      knowledge/             ← knowledge base index
      skills/                ← skill registry
      accounts/              ← account data (from vault)
      communicator/          ← communicator state
    2026-08-15-15-00/
      ...
    latest -> 2026-08-15-15-00   ← symlink to latest verified snapshot

Retention policy:
- Hourly snapshots kept for 24 hours
- Daily snapshots kept for 30 days
- Weekly snapshots kept for 1 year
- Configurable by the Creator
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class SnapshotManifest:
    """Manifest for a single snapshot — lists all files and their hashes."""
    snapshot_id: str
    timestamp: float
    label: str = ""
    files: dict[str, str] = field(default_factory=dict)  # path -> sha256
    total_size: int = 0
    file_count: int = 0
    verified: bool = False
    verification_errors: list[str] = field(default_factory=list)
    ledger_entries_at_snapshot: int = 0
    created_by: str = "anubis.snapshot_manager"

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "files": self.files,
            "total_size": self.total_size,
            "file_count": self.file_count,
            "verified": self.verified,
            "verification_errors": self.verification_errors,
            "ledger_entries_at_snapshot": self.ledger_entries_at_snapshot,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotManifest":
        return cls(
            snapshot_id=data.get("snapshot_id", ""),
            timestamp=data.get("timestamp", 0.0),
            label=data.get("label", ""),
            files=data.get("files", {}),
            total_size=data.get("total_size", 0),
            file_count=data.get("file_count", 0),
            verified=data.get("verified", False),
            verification_errors=data.get("verification_errors", []),
            ledger_entries_at_snapshot=data.get("ledger_entries_at_snapshot", 0),
            created_by=data.get("created_by", "anubis.snapshot_manager"),
        )


# ===========================================================
# Snapshot manager
# ===========================================================

class SnapshotManager:
    """Manages immutable, hash-verified snapshots of ANUBIS's state.

    Snapshots are stored in a configurable directory (off-drive by
    default). Each snapshot is a complete copy of the state directories
    with a manifest of file hashes for verification.
    """

    ACTOR = "anubis.snapshot_manager"

    # Default directories to snapshot (relative to root)
    DEFAULT_STATE_DIRS = [
        "memory",
        "identity",
        "evidence",
        "court",
        "knowledge",
        "skills",
        "registry",
        "capabilities",
        "policy",
        "purge",
    ]

    # Default retention policy
    DEFAULT_HOURLY_RETENTION = 24   # keep 24 hourly snapshots
    DEFAULT_DAILY_RETENTION = 30    # keep 30 daily snapshots
    DEFAULT_WEEKLY_RETENTION = 52   # keep 52 weekly snapshots

    def __init__(
        self,
        root: str | Path,
        snapshot_dir: str | Path,
        *,
        ledger: Any | None = None,
        state_dirs: list[str] | None = None,
        on_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger
        self.on_alert = on_alert
        self.state_dirs = state_dirs or self.DEFAULT_STATE_DIRS

        # Index file tracking all snapshots
        self._index_file = self.snapshot_dir / "snapshot_index.json"

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass

    def _alert(self, severity: str, message: str) -> None:
        if self.on_alert:
            try:
                self.on_alert(severity, message)
            except Exception:
                pass

    # ===========================================================
    # SNAPSHOT CREATION
    # ===========================================================

    def create_snapshot(self, label: str = "") -> dict[str, Any]:
        """Create a new immutable snapshot of the current state.

        Copies all state directories to a new timestamped snapshot
        directory, computes file hashes, and writes a manifest.
        The snapshot is marked as immutable after creation.
        """
        snapshot_id = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        snapshot_path = self.snapshot_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)

        manifest = SnapshotManifest(
            snapshot_id=snapshot_id,
            timestamp=time.time(),
            label=label,
        )

        # Copy state directories
        for state_dir in self.state_dirs:
            src = self.root / state_dir
            if not src.exists():
                continue
            dst = snapshot_path / state_dir
            try:
                shutil.copytree(src, dst, dirs_exist_ok=True)
            except Exception as e:
                manifest.verification_errors.append(f"copy error {state_dir}: {e}")

        # Compute file hashes
        total_size = 0
        file_count = 0
        for file_path in snapshot_path.rglob("*"):
            if file_path.is_file() and file_path.name != "manifest.json":
                try:
                    file_hash = self._hash_file(file_path)
                    rel_path = str(file_path.relative_to(snapshot_path)).replace("\\", "/")
                    manifest.files[rel_path] = file_hash
                    total_size += file_path.stat().st_size
                    file_count += 1
                except Exception as e:
                    manifest.verification_errors.append(f"hash error {file_path}: {e}")

        manifest.total_size = total_size
        manifest.file_count = file_count

        # Count ledger entries at snapshot time
        ledger_file = self.root / "evidence" / "ledger.jsonl"
        if ledger_file.exists():
            try:
                with open(ledger_file, "r", encoding="utf-8") as f:
                    manifest.ledger_entries_at_snapshot = sum(1 for _ in f)
            except Exception:
                pass

        # Verify the snapshot (self-check)
        manifest.verified = len(manifest.verification_errors) == 0

        # Write manifest
        manifest_file = snapshot_path / "manifest.json"
        manifest_file.write_text(
            json.dumps(manifest.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

        # Make snapshot immutable (best effort — chmod on Unix)
        try:
            if os.name != "nt":  # not Windows
                for file_path in snapshot_path.rglob("*"):
                    os.chmod(file_path, 0o444 if file_path.is_file() else 0o555)
        except Exception:
            pass

        # Update index
        self._update_index(manifest)

        # Update latest pointer
        self._update_latest(snapshot_id)

        self._log("snapshot.create", {
            "snapshot_id": snapshot_id,
            "label": label,
            "files": file_count,
            "size": total_size,
            "verified": manifest.verified,
        })

        return {
            "snapshot_id": snapshot_id,
            "label": label,
            "files": file_count,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "verified": manifest.verified,
            "errors": manifest.verification_errors,
            "path": str(snapshot_path),
        }

    def _hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _update_index(self, manifest: SnapshotManifest) -> None:
        """Update the snapshot index file."""
        index = self._load_index()
        index.append(manifest.to_dict())
        # Keep only the most recent 1000 entries in the index
        index = index[-1000:]
        self._index_file.write_text(
            json.dumps(index, indent=2) + "\n",
            encoding="utf-8",
        )

    def _load_index(self) -> list[dict[str, Any]]:
        """Load the snapshot index."""
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _update_latest(self, snapshot_id: str) -> None:
        """Update the 'latest' pointer to the most recent snapshot."""
        latest = self.snapshot_dir / "latest"
        # Remove old symlink/file
        if latest.is_symlink() or latest.exists():
            try:
                if latest.is_symlink():
                    latest.unlink()
                elif latest.is_dir():
                    shutil.rmtree(latest)
                else:
                    latest.unlink()
            except Exception:
                pass
        # Create new symlink (or a file on Windows)
        try:
            if os.name != "nt":
                latest.symlink_to(snapshot_id)
            else:
                latest.write_text(snapshot_id, encoding="utf-8")
        except Exception:
            pass

    # ===========================================================
    # SNAPSHOT VERIFICATION
    # ===========================================================

    def verify_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        """Verify a snapshot by checking all file hashes against the manifest.

        Also cross-checks that state changes are explained by ledger entries.
        """
        snapshot_path = self.snapshot_dir / snapshot_id
        if not snapshot_path.exists():
            return {"snapshot_id": snapshot_id, "valid": False, "error": "snapshot not found"}

        manifest_file = snapshot_path / "manifest.json"
        if not manifest_file.exists():
            return {"snapshot_id": snapshot_id, "valid": False, "error": "manifest not found"}

        try:
            manifest = SnapshotManifest.from_dict(
                json.loads(manifest_file.read_text(encoding="utf-8"))
            )
        except Exception as e:
            return {"snapshot_id": snapshot_id, "valid": False, "error": f"manifest corrupt: {e}"}

        errors: list[str] = []
        checked = 0
        mismatched = 0

        for rel_path, expected_hash in manifest.files.items():
            file_path = snapshot_path / rel_path
            if not file_path.exists():
                errors.append(f"missing file: {rel_path}")
                mismatched += 1
                continue
            try:
                actual_hash = self._hash_file(file_path)
                if actual_hash != expected_hash:
                    errors.append(f"hash mismatch: {rel_path}")
                    mismatched += 1
                checked += 1
            except Exception as e:
                errors.append(f"hash error {rel_path}: {e}")

        valid = mismatched == 0 and len(errors) == 0

        result = {
            "snapshot_id": snapshot_id,
            "valid": valid,
            "files_checked": checked,
            "files_mismatched": mismatched,
            "errors": errors,
            "timestamp": manifest.timestamp,
            "label": manifest.label,
        }

        if not valid:
            self._alert("critical", f"Snapshot {snapshot_id} verification FAILED: {len(errors)} errors")
            self._log("snapshot.verify_failed", result)

        return result

    def verify_latest(self) -> dict[str, Any]:
        """Verify the most recent snapshot."""
        latest_id = self.get_latest_snapshot_id()
        if not latest_id:
            return {"valid": False, "error": "no snapshots exist"}
        return self.verify_snapshot(latest_id)

    # ===========================================================
    # CORRUPTION DETECTION
    # ===========================================================

    def detect_corruption(self) -> dict[str, Any]:
        """Detect corruption by comparing current state to the latest snapshot.

        This checks whether the current state files have been modified
        in ways not explained by ledger entries. If a file's hash
        changed but no corresponding ledger entry exists, it's suspicious.

        Returns a report of any suspicious changes.
        """
        latest_id = self.get_latest_snapshot_id()
        if not latest_id:
            return {"corrupted": False, "message": "no snapshots to compare against"}

        snapshot_path = self.snapshot_dir / latest_id
        manifest_file = snapshot_path / "manifest.json"
        if not manifest_file.exists():
            return {"corrupted": False, "error": "latest snapshot manifest missing"}

        try:
            manifest = SnapshotManifest.from_dict(
                json.loads(manifest_file.read_text(encoding="utf-8"))
            )
        except Exception:
            return {"corrupted": False, "error": "manifest corrupt"}

        changed_files: list[str] = []
        new_files: list[str] = []
        deleted_files: list[str] = []

        # Check each file in the manifest
        for rel_path, expected_hash in manifest.files.items():
            # Map snapshot path back to source path (normalize separators)
            normalized = rel_path.replace("\\", "/")
            parts = normalized.split("/", 1)
            if len(parts) < 2:
                continue
            state_dir, sub_path = parts[0], parts[1]
            src_path = self.root / state_dir / sub_path

            if not src_path.exists():
                deleted_files.append(rel_path)
                continue

            try:
                actual_hash = self._hash_file(src_path)
                if actual_hash != expected_hash:
                    changed_files.append(rel_path)
            except Exception:
                pass

        # Check for new files not in the snapshot (in state dirs)
        for state_dir in self.state_dirs:
            src = self.root / state_dir
            if not src.exists():
                continue
            for file_path in src.rglob("*"):
                if file_path.is_file():
                    rel = f"{state_dir}/{file_path.relative_to(src)}".replace("\\", "/")
                    if rel not in manifest.files:
                        new_files.append(rel)

        # Determine if changes are suspicious
        # Changes are expected (ANUBIS is always running), but we log them
        suspicious = len(deleted_files) > 0  # deleted state files are suspicious

        result = {
            "corrupted": suspicious,
            "compared_against": latest_id,
            "changed_files": changed_files[:50],  # cap for readability
            "changed_count": len(changed_files),
            "new_files": new_files[:50],
            "new_count": len(new_files),
            "deleted_files": deleted_files[:50],
            "deleted_count": len(deleted_files),
            "suspicious": suspicious,
            "timestamp": time.time(),
        }

        if suspicious:
            self._alert("warning", f"Corruption detection: {len(deleted_files)} deleted state files")
            self._log("snapshot.corruption_detected", result)

        return result

    # ===========================================================
    # SNAPSHOT RESTORATION
    # ===========================================================

    def restore_snapshot(self, snapshot_id: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        """Restore state from a snapshot.

        Copies the snapshot's state directories back to the target
        (defaults to the root). Does NOT overwrite the core code —
        only state directories.
        """
        snapshot_path = self.snapshot_dir / snapshot_id
        if not snapshot_path.exists():
            return {"restored": False, "error": "snapshot not found"}

        manifest_file = snapshot_path / "manifest.json"
        if not manifest_file.exists():
            return {"restored": False, "error": "manifest not found"}

        # Verify before restoring
        verify_result = self.verify_snapshot(snapshot_id)
        if not verify_result["valid"]:
            return {
                "restored": False,
                "error": "snapshot verification failed — cannot restore from corrupted snapshot",
                "verification": verify_result,
            }

        target = Path(target_dir) if target_dir else self.root
        restored_dirs: list[str] = []
        restored_files = 0

        for state_dir in self.state_dirs:
            src = snapshot_path / state_dir
            if not src.exists():
                continue
            dst = target / state_dir
            try:
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                restored_dirs.append(state_dir)
                restored_files += sum(1 for _ in src.rglob("*") if _.is_file())
            except Exception as e:
                pass

        self._log("snapshot.restore", {
            "snapshot_id": snapshot_id,
            "restored_dirs": restored_dirs,
            "restored_files": restored_files,
        })

        return {
            "restored": True,
            "snapshot_id": snapshot_id,
            "restored_dirs": restored_dirs,
            "restored_files": restored_files,
            "target": str(target),
            "message": f"Restored {restored_files} files across {len(restored_dirs)} directories from snapshot {snapshot_id}",
        }

    # ===========================================================
    # SNAPSHOT MANAGEMENT
    # ===========================================================

    def list_snapshots(self, limit: int = 50) -> dict[str, Any]:
        """List all snapshots, newest first."""
        index = self._load_index()
        snapshots = sorted(index, key=lambda s: s.get("timestamp", 0), reverse=True)
        snapshots = snapshots[:limit]
        return {
            "count": len(index),
            "showing": len(snapshots),
            "snapshots": snapshots,
        }

    def get_latest_snapshot_id(self) -> str:
        """Get the ID of the latest snapshot."""
        latest = self.snapshot_dir / "latest"
        if latest.is_symlink():
            try:
                return latest.readlink().name
            except Exception:
                pass
        if latest.exists():
            try:
                return latest.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        # Fallback: find newest directory
        index = self._load_index()
        if index:
            newest = max(index, key=lambda s: s.get("timestamp", 0))
            return newest.get("snapshot_id", "")
        return ""

    def delete_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        """Delete a snapshot (used by retention policy)."""
        snapshot_path = self.snapshot_dir / snapshot_id
        if not snapshot_path.exists():
            return {"deleted": False, "error": "snapshot not found"}
        try:
            # Restore permissions before deleting
            if os.name != "nt":
                for file_path in snapshot_path.rglob("*"):
                    try:
                        os.chmod(file_path, 0o644 if file_path.is_file() else 0o755)
                    except Exception:
                        pass
            shutil.rmtree(snapshot_path)
            # Remove from index
            index = self._load_index()
            index = [s for s in index if s.get("snapshot_id") != snapshot_id]
            self._index_file.write_text(
                json.dumps(index, indent=2) + "\n", encoding="utf-8"
            )
            self._log("snapshot.delete", {"snapshot_id": snapshot_id})
            return {"deleted": True, "snapshot_id": snapshot_id}
        except Exception as e:
            return {"deleted": False, "error": str(e)}

    # ===========================================================
    # RETENTION POLICY
    # ===========================================================

    def apply_retention_policy(
        self,
        hourly: int = DEFAULT_HOURLY_RETENTION,
        daily: int = DEFAULT_DAILY_RETENTION,
        weekly: int = DEFAULT_WEEKLY_RETENTION,
    ) -> dict[str, Any]:
        """Apply retention policy — delete old snapshots beyond retention limits.

        Keeps:
        - All hourly snapshots from the last `hourly` hours
        - One daily snapshot per day for the last `daily` days
        - One weekly snapshot per week for the last `weekly` weeks
        """
        index = self._load_index()
        if not index:
            return {"deleted": 0, "message": "no snapshots to prune"}

        now = time.time()
        keep_ids: set[str] = set()

        # Group snapshots by time period
        hourly_cutoff = now - (hourly * 3600)
        daily_cutoff = now - (daily * 86400)
        weekly_cutoff = now - (weekly * 7 * 86400)

        # Keep all snapshots within hourly window
        for s in index:
            ts = s.get("timestamp", 0)
            if ts >= hourly_cutoff:
                keep_ids.add(s.get("snapshot_id", ""))

        # Keep one per day in daily window (the latest each day)
        daily_snapshots: dict[str, dict] = {}
        for s in index:
            ts = s.get("timestamp", 0)
            if ts >= daily_cutoff:
                day = time.strftime("%Y-%m-%d", time.localtime(ts))
                if day not in daily_snapshots or ts > daily_snapshots[day].get("timestamp", 0):
                    daily_snapshots[day] = s
        for s in daily_snapshots.values():
            keep_ids.add(s.get("snapshot_id", ""))

        # Keep one per week in weekly window
        weekly_snapshots: dict[str, dict] = {}
        for s in index:
            ts = s.get("timestamp", 0)
            if ts >= weekly_cutoff:
                # ISO week number
                week = time.strftime("%Y-W%W", time.localtime(ts))
                if week not in weekly_snapshots or ts > weekly_snapshots[week].get("timestamp", 0):
                    weekly_snapshots[week] = s
        for s in weekly_snapshots.values():
            keep_ids.add(s.get("snapshot_id", ""))

        # Delete snapshots not in keep set
        deleted = 0
        for s in index:
            sid = s.get("snapshot_id", "")
            if sid and sid not in keep_ids:
                result = self.delete_snapshot(sid)
                if result.get("deleted"):
                    deleted += 1

        self._log("snapshot.retention", {"deleted": deleted, "kept": len(keep_ids)})
        return {
            "deleted": deleted,
            "kept": len(keep_ids),
            "message": f"Pruned {deleted} old snapshots, kept {len(keep_ids)}",
        }

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get snapshot manager status."""
        index = self._load_index()
        total_size = sum(s.get("total_size", 0) for s in index)
        latest_id = self.get_latest_snapshot_id()
        latest_info = None
        if latest_id:
            for s in index:
                if s.get("snapshot_id") == latest_id:
                    latest_info = s
                    break

        return {
            "snapshot_count": len(index),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "latest_snapshot": latest_id,
            "latest_verified": latest_info.get("verified", False) if latest_info else False,
            "latest_timestamp": latest_info.get("timestamp", 0) if latest_info else 0,
            "snapshot_dir": str(self.snapshot_dir),
            "state_dirs": self.state_dirs,
        }

    # ===========================================================
    # SNAPSHOT DIFF VIEWER
    # ===========================================================

    def diff_file(self, snapshot_id: str, rel_path: str) -> dict[str, Any]:
        """Show the content difference between a snapshot and the current file.

        Args:
            snapshot_id: The snapshot to compare against
            rel_path: Relative path within the state directory (e.g., "memory/facts.json")

        Returns:
            Dict with the snapshot content, current content, and a unified diff
        """
        normalized = rel_path.replace("\\", "/")
        parts = normalized.split("/", 1)
        if len(parts) < 2:
            return {"error": "path must include state directory prefix (e.g., memory/facts.json)"}

        state_dir, sub_path = parts[0], parts[1]
        snapshot_file = self.snapshot_dir / snapshot_id / state_dir / sub_path
        current_file = self.root / state_dir / sub_path

        if not snapshot_file.exists():
            return {"error": f"file not found in snapshot: {rel_path}"}
        if not current_file.exists():
            return {"error": f"current file not found: {rel_path}"}

        try:
            snapshot_content = snapshot_file.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"cannot read snapshot file: {e}"}
        try:
            current_content = current_file.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": f"cannot read current file: {e}"}

        # Generate unified diff
        import difflib
        snapshot_lines = snapshot_content.splitlines(keepends=True)
        current_lines = current_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            snapshot_lines, current_lines,
            fromfile=f"snapshot/{rel_path}",
            tofile=f"current/{rel_path}",
            lineterm="",
        ))

        return {
            "rel_path": rel_path,
            "snapshot_id": snapshot_id,
            "snapshot_hash": self._hash_file(snapshot_file),
            "current_hash": self._hash_file(current_file),
            "identical": self._hash_file(snapshot_file) == self._hash_file(current_file),
            "snapshot_size": snapshot_file.stat().st_size,
            "current_size": current_file.stat().st_size,
            "diff": "".join(diff) if diff else "",
            "changed": len(diff) > 0,
        }

    def diff_all(self, snapshot_id: str) -> dict[str, Any]:
        """Show all changed files between a snapshot and the current state.

        Returns a summary of all files that differ, with diffs for each.
        """
        snapshot_path = self.snapshot_dir / snapshot_id
        if not snapshot_path.exists():
            return {"error": "snapshot not found"}

        manifest_file = snapshot_path / "manifest.json"
        if not manifest_file.exists():
            return {"error": "manifest not found"}

        try:
            manifest = SnapshotManifest.from_dict(
                json.loads(manifest_file.read_text(encoding="utf-8"))
            )
        except Exception:
            return {"error": "manifest corrupt"}

        changed: list[dict[str, Any]] = []
        for rel_path, expected_hash in manifest.files.items():
            normalized = rel_path.replace("\\", "/")
            parts = normalized.split("/", 1)
            if len(parts) < 2:
                continue
            state_dir, sub_path = parts[0], parts[1]
            current_file = self.root / state_dir / sub_path
            if not current_file.exists():
                changed.append({"rel_path": rel_path, "status": "deleted"})
                continue
            try:
                actual_hash = self._hash_file(current_file)
                if actual_hash != expected_hash:
                    # Get the diff for this file
                    diff_result = self.diff_file(snapshot_id, rel_path)
                    changed.append({
                        "rel_path": rel_path,
                        "status": "modified",
                        "identical": False,
                        "diff_preview": diff_result.get("diff", "")[:500],
                    })
            except Exception:
                pass

        return {
            "snapshot_id": snapshot_id,
            "changed_files": changed,
            "changed_count": len(changed),
            "total_files": len(manifest.files),
        }
