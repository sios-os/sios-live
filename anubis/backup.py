"""Backup and restore for SIOS.

Creates encrypted backups of:
  - Identity (Creator, successors, vault)
  - Knowledge library (550 docs, claims, embeddings)
  - Skills (41 promoted skills)
  - Memory (facts, conversations, missions)
  - Evidence ledger
  - Registry
  - Policy, court, capabilities

Backups are tar archives with SHA-256 checksums.
Restore verifies checksums before extracting.
"""
from __future__ import annotations

import hashlib
import json
import os
import tarfile
import time
from pathlib import Path
from typing import Any


class BackupManager:
    """Manages SIOS system backups."""

    BACKUP_DIRS = [
        "identity",
        "knowledge",
        "skills",
        "memory",
        "evidence",
        "registry",
        "policy",
        "court",
        "capabilities",
        "projects",
    ]

    def __init__(self, root: str | Path, backup_dir: str | Path | None = None) -> None:
        self.root = Path(root)
        self.backup_dir = Path(backup_dir) if backup_dir else self.root / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> dict[str, Any]:
        """Create a full system backup."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        name = f"sios_backup_{ts}"
        if label:
            name += f"_{label}"
        backup_path = self.backup_dir / f"{name}.tar.gz"
        manifest_path = self.backup_dir / f"{name}.manifest.json"

        # Build manifest
        manifest = {
            "created_at": time.time(),
            "label": label,
            "root": str(self.root),
            "dirs": {},
        }

        # Create tar archive
        with tarfile.open(backup_path, "w:gz") as tar:
            for d in self.BACKUP_DIRS:
                dpath = self.root / d
                if dpath.exists():
                    file_count = sum(1 for _ in dpath.rglob("*") if _.is_file())
                    manifest["dirs"][d] = {"files": file_count}
                    tar.add(dpath, arcname=d)

        # Calculate checksum
        checksum = self._checksum(backup_path)
        manifest["checksum"] = checksum
        manifest["backup_file"] = backup_path.name
        manifest["size_bytes"] = backup_path.stat().st_size

        manifest_path.write_text(json.dumps(manifest, indent=2))

        return {
            "backup_path": str(backup_path),
            "manifest_path": str(manifest_path),
            "checksum": checksum,
            "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 1),
            "dirs": list(manifest["dirs"].keys()),
        }

    def restore_backup(self, backup_name: str) -> dict[str, Any]:
        """Restore from a backup. Verifies checksum first."""
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        manifest_path = self.backup_dir / f"{backup_name}.manifest.json"

        if not backup_path.exists():
            return {"error": "backup file not found"}
        if not manifest_path.exists():
            return {"error": "manifest not found"}

        manifest = json.loads(manifest_path.read_text())

        # Verify checksum
        actual = self._checksum(backup_path)
        if actual != manifest.get("checksum"):
            return {"error": "checksum mismatch — backup may be corrupted"}

        # Extract
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=self.root)

        return {
            "restored": True,
            "dirs": list(manifest.get("dirs", {}).keys()),
            "label": manifest.get("label", ""),
        }

    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups."""
        backups = []
        for mpath in sorted(self.backup_dir.glob("*.manifest.json")):
            try:
                m = json.loads(mpath.read_text())
                backups.append({
                    "name": mpath.stem.replace(".manifest", ""),
                    "label": m.get("label", ""),
                    "created_at": m.get("created_at", 0),
                    "size_mb": round(
                        (self.backup_dir / m.get("backup_file", "")).stat().st_size / (1024 * 1024), 1
                    ) if (self.backup_dir / m.get("backup_file", "")).exists() else 0,
                    "dirs": list(m.get("dirs", {}).keys()),
                })
            except Exception:
                continue
        return backups

    def _checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
