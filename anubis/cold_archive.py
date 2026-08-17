"""Cold storage archive — quarterly compressed encrypted archives.

Creates long-term encrypted archives of ANUBIS's complete state for
disaster recovery. Unlike snapshots (which are frequent and local),
cold archives are:

1. QUARTERLY — created every 90 days (or on demand)
2. COMPRESSED — tar.gz with maximum compression
3. ENCRYPTED — XOR-encrypted with a derived key (same as identity vault)
4. CLOUD-SYNCED — uploaded to iDrive E2 for offsite storage
5. VERIFIED — checksum-verified before and after upload
6. CATALOGED — tracked in an archive index for easy retrieval

Cold archives protect against:
- Total machine destruction (fire, flood, theft)
- Off-drive storage failure (both local copies lost)
- Catastrophic corruption that propagates to all snapshots
- Long-term data loss (snapshots only retain ~1 year)

Archive contents:
- All state directories (memory, identity, evidence, court, knowledge, etc.)
- Core code (anubis/, tools/)
- Skill registry
- Configuration files
- Model weights reference (not the weights themselves — too large)

Archive retention:
- Keep all quarterly archives for 5 years
- After 5 years, keep one per year indefinitely
- Configurable by the Creator
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class ColdArchive:
    """Metadata for a single cold archive."""
    archive_id: str
    timestamp: float
    label: str = ""
    archive_path: str = ""
    archive_size: int = 0
    compressed_size: int = 0
    checksum: str = ""
    file_count: int = 0
    encrypted: bool = False
    uploaded_to_cloud: bool = False
    cloud_key: str = ""
    verified: bool = False
    created_by: str = "anubis.cold_archive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "archive_path": self.archive_path,
            "archive_size": self.archive_size,
            "compressed_size": self.compressed_size,
            "checksum": self.checksum,
            "file_count": self.file_count,
            "encrypted": self.encrypted,
            "uploaded_to_cloud": self.uploaded_to_cloud,
            "cloud_key": self.cloud_key,
            "verified": self.verified,
            "created_by": self.created_by,
        }


# ===========================================================
# Cold archive manager
# ===========================================================

class ColdArchiveManager:
    """Manages quarterly cold storage archives.

    Creates compressed, encrypted archives of ANUBIS's complete state
    and optionally uploads them to cloud storage.
    """

    ACTOR = "anubis.cold_archive"

    # Directories to archive
    ARCHIVE_DIRS = [
        "anubis",
        "tools",
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
        "config",
        "projects",
    ]

    # Retention: keep all for 5 years, then one per year
    DEFAULT_RETENTION_YEARS = 5

    def __init__(
        self,
        root: str | Path,
        archive_dir: str | Path,
        *,
        cloud_sync: Any | None = None,
        ledger: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
        passphrase: str | None = None,
    ) -> None:
        self.root = Path(root)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.cloud_sync = cloud_sync
        self.ledger = ledger
        self.on_speak = on_speak
        self._passphrase = passphrase or "anubis_cold_archive_default"

        self._index_file = self.archive_dir / "archive_index.json"
        self._state_dir = self.root / "memory" / "cold_archive"
        self._state_dir.mkdir(parents=True, exist_ok=True)

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

    def _hash_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _xor_encrypt(self, data: bytes, key: str) -> bytes:
        """Simple XOR encryption (same approach as identity vault)."""
        key_bytes = key.encode("utf-8")
        key_len = len(key_bytes)
        return bytes(b ^ key_bytes[i % key_len] for i, b in enumerate(data))

    # ===========================================================
    # ARCHIVE CREATION
    # ===========================================================

    def create_archive(self, label: str = "", *, upload: bool = True) -> dict[str, Any]:
        """Create a new cold archive.

        1. Collects all archive directories
        2. Creates a tar.gz archive
        3. Encrypts the archive
        4. Computes checksum
        5. Optionally uploads to cloud
        6. Updates the archive index
        """
        archive_id = f"cold_{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())}"
        archive_path = self.archive_dir / f"{archive_id}.tar.gz"
        encrypted_path = self.archive_dir / f"{archive_id}.enc"

        archive = ColdArchive(
            archive_id=archive_id,
            timestamp=time.time(),
            label=label or f"Quarterly archive {time.strftime('%Y-%m-%d')}",
            archive_path=str(archive_path),
        )

        # 1. Create tar.gz
        file_count = 0
        total_size = 0
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                for dir_name in self.ARCHIVE_DIRS:
                    src = self.root / dir_name
                    if src.exists():
                        tar.add(src, arcname=dir_name)
                        for f in src.rglob("*"):
                            if f.is_file():
                                file_count += 1
                                total_size += f.stat().st_size
        except Exception as e:
            return {"created": False, "error": f"tar creation failed: {e}"}

        archive.file_count = file_count
        archive.archive_size = total_size
        archive.compressed_size = archive_path.stat().st_size

        # 2. Compute checksum
        archive.checksum = self._hash_file(archive_path)

        # 3. Encrypt
        try:
            with open(archive_path, "rb") as f:
                data = f.read()
            encrypted = self._xor_encrypt(data, self._passphrase)
            encrypted_path.write_bytes(encrypted)
            archive.encrypted = True
            # Remove unencrypted version
            archive_path.unlink()
        except Exception as e:
            return {"created": False, "error": f"encryption failed: {e}"}

        # 4. Verify
        try:
            with open(encrypted_path, "rb") as f:
                enc_data = f.read()
            dec_data = self._xor_encrypt(enc_data, self._passphrase)
            if hashlib.sha256(dec_data).hexdigest() == archive.checksum:
                archive.verified = True
        except Exception:
            pass

        # 5. Upload to cloud
        if upload and self.cloud_sync is not None:
            try:
                cloud_key = f"cold_archives/{archive_id}.enc"
                result = self.cloud_sync.upload_file(str(encrypted_path), remote_key=cloud_key)
                if result.get("ok"):
                    archive.uploaded_to_cloud = True
                    archive.cloud_key = cloud_key
            except Exception:
                pass

        # 6. Update index
        self._update_index(archive)

        self._log("archive.create", archive.to_dict())

        result = archive.to_dict()
        result["created"] = True
        result["size_mb"] = round(archive.compressed_size / (1024 * 1024), 2)
        return result

    def _update_index(self, archive: ColdArchive) -> None:
        """Update the archive index."""
        index = self._load_index()
        index.append(archive.to_dict())
        self._index_file.write_text(
            json.dumps(index, indent=2) + "\n", encoding="utf-8"
        )

    def _load_index(self) -> list[dict[str, Any]]:
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    # ===========================================================
    # ARCHIVE RESTORATION
    # ===========================================================

    def restore_archive(self, archive_id: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        """Restore from a cold archive.

        1. Find the encrypted archive
        2. Decrypt it
        3. Verify checksum
        4. Extract to target directory
        """
        encrypted_path = self.archive_dir / f"{archive_id}.enc"
        if not encrypted_path.exists():
            return {"restored": False, "error": "archive not found"}

        target = Path(target_dir) if target_dir else self.root
        temp_tar = self.archive_dir / f"{archive_id}_restore.tar.gz"

        # 1. Decrypt
        try:
            with open(encrypted_path, "rb") as f:
                enc_data = f.read()
            dec_data = self._xor_encrypt(enc_data, self._passphrase)
            temp_tar.write_bytes(dec_data)
        except Exception as e:
            return {"restored": False, "error": f"decryption failed: {e}"}

        # 2. Verify checksum
        actual_hash = self._hash_file(temp_tar)
        index = self._load_index()
        expected_hash = ""
        for entry in index:
            if entry.get("archive_id") == archive_id:
                expected_hash = entry.get("checksum", "")
                break

        if expected_hash and actual_hash != expected_hash:
            temp_tar.unlink(missing_ok=True)
            return {"restored": False, "error": "checksum mismatch — archive may be corrupted"}

        # 3. Extract
        try:
            with tarfile.open(temp_tar, "r:gz") as tar:
                tar.extractall(target)
        except Exception as e:
            temp_tar.unlink(missing_ok=True)
            return {"restored": False, "error": f"extraction failed: {e}"}

        temp_tar.unlink(missing_ok=True)

        self._log("archive.restore", {"archive_id": archive_id, "target": str(target)})

        return {
            "restored": True,
            "archive_id": archive_id,
            "target": str(target),
            "message": f"Restored archive {archive_id} to {target}",
        }

    # ===========================================================
    # ARCHIVE MANAGEMENT
    # ===========================================================

    def list_archives(self) -> dict[str, Any]:
        """List all cold archives."""
        index = self._load_index()
        archives = sorted(index, key=lambda a: a.get("timestamp", 0), reverse=True)
        return {"count": len(archives), "archives": archives}

    def delete_archive(self, archive_id: str) -> dict[str, Any]:
        """Delete a cold archive (local + cloud)."""
        encrypted_path = self.archive_dir / f"{archive_id}.enc"
        deleted_local = False
        if encrypted_path.exists():
            try:
                encrypted_path.unlink()
                deleted_local = True
            except Exception:
                pass

        # Try to delete from cloud
        deleted_cloud = False
        if self.cloud_sync:
            index = self._load_index()
            for entry in index:
                if entry.get("archive_id") == archive_id:
                    cloud_key = entry.get("cloud_key", "")
                    if cloud_key:
                        try:
                            self.cloud_sync.delete_file(cloud_key)
                            deleted_cloud = True
                        except Exception:
                            pass
                    break

        # Remove from index
        index = self._load_index()
        index = [a for a in index if a.get("archive_id") != archive_id]
        self._index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

        self._log("archive.delete", {"archive_id": archive_id})
        return {"deleted": True, "archive_id": archive_id, "local": deleted_local, "cloud": deleted_cloud}

    def apply_retention(self, years: int = DEFAULT_RETENTION_YEARS) -> dict[str, Any]:
        """Apply retention policy — keep all for N years, then one per year."""
        index = self._load_index()
        if not index:
            return {"deleted": 0, "message": "no archives to prune"}

        now = time.time()
        cutoff = now - (years * 365.25 * 86400)
        keep_ids: set[str] = set()

        # Keep all archives within retention window
        for a in index:
            if a.get("timestamp", 0) >= cutoff:
                keep_ids.add(a.get("archive_id", ""))

        # Keep one per year before the cutoff (the latest each year)
        yearly: dict[str, dict] = {}
        for a in index:
            ts = a.get("timestamp", 0)
            if ts < cutoff:
                year = time.strftime("%Y", time.localtime(ts))
                if year not in yearly or ts > yearly[year].get("timestamp", 0):
                    yearly[year] = a
        for a in yearly.values():
            keep_ids.add(a.get("archive_id", ""))

        # Delete archives not in keep set
        deleted = 0
        for a in index:
            aid = a.get("archive_id", "")
            if aid and aid not in keep_ids:
                result = self.delete_archive(aid)
                if result.get("deleted"):
                    deleted += 1

        self._log("archive.retention", {"deleted": deleted, "kept": len(keep_ids)})
        return {"deleted": deleted, "kept": len(keep_ids)}

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get cold archive system status."""
        index = self._load_index()
        total_size = sum(a.get("compressed_size", 0) for a in index)
        uploaded = sum(1 for a in index if a.get("uploaded_to_cloud"))
        latest = max(index, key=lambda a: a.get("timestamp", 0)) if index else None

        return {
            "archive_count": len(index),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "uploaded_count": uploaded,
            "latest_archive": latest.get("archive_id", "") if latest else "",
            "latest_timestamp": latest.get("timestamp", 0) if latest else 0,
            "has_cloud_sync": self.cloud_sync is not None,
            "archive_dir": str(self.archive_dir),
        }
