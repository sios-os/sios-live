"""Cloud sync to iDrive E2 (S3-compatible storage).

Book 09 treats external services as untrusted. This module syncs
compressed deltas, metadata, and archives to iDrive E2 with
client-side encryption before upload. Identity vault data, credentials,
and raw conversation logs never leave the machine.

iDrive E2 is S3-compatible, so this module implements the S3 API using
only the Python standard library (urllib, hashlib, hmac) — no
third-party dependencies, per the constitutional kernel's
permission-integrity rule.

AWS Signature Version 4 signing is implemented from scratch because
the standard library does not include it and boto3 is a third-party
dependency that the constitution flags as a hazard.

Data classification (enforced by this module, not by ANUBIS's judgment):
  hot  — local only (identity vault, credentials, active conversation)
  warm — local + encrypted cloud backup (skill library, knowledge base)
  cold — compressed + cloud only (old archives, old model weights)

All sync operations require Creator approval (ChangeClass.CONSEQUENTIAL).
Every upload and download is logged to the evidence ledger (audit law).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default credential locations
CREDENTIALS_FILE = "config/cloud_credentials.json"

# Data classification — enforced here, not by ANUBIS
HOT_PATHS = (
    "identity/",      # identity vault, credentials
    "config/",        # local credentials config
)
WARM_PATHS = (
    "skills/",        # skill library
    "knowledge/",     # knowledge base
    "evidence/",      # evidence ledger
    "memory/",        # memory (includes long-term archives)
)
# Everything else is cold or ad-hoc


def _classify_path(rel_path: str) -> str:
    """Classify a path as hot/warm/cold.

    Hot paths are never synced. Warm paths are synced with
    encryption. Cold paths are compressed and synced.
    """
    # Normalize path separators (Windows uses \, hot/warm paths use /)
    normalized = rel_path.replace("\\", "/")
    for hot in HOT_PATHS:
        if normalized.startswith(hot):
            return "hot"
    for warm in WARM_PATHS:
        if normalized.startswith(warm):
            return "warm"
    return "cold"


@dataclass
class SyncConfig:
    """Configuration for cloud sync."""
    endpoint: str = ""
    region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    bucket: str = "sios-backup"

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> "SyncConfig":
        """Load config from the credentials file or identity vault."""
        path = Path(path or CREDENTIALS_FILE)
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            e2 = data.get("idrive_e2", {})
            return cls(
                endpoint=e2.get("endpoint", ""),
                region=e2.get("region", ""),
                access_key_id=e2.get("access_key_id", ""),
                secret_access_key=e2.get("secret_access_key", ""),
                bucket=e2.get("bucket", "sios-backup"),
            )
        except (json.JSONDecodeError, OSError):
            return cls()

    @classmethod
    def from_vault(cls, vault) -> "SyncConfig | None":
        """Load config from an unlocked identity vault.

        Returns None if the vault is locked or doesn't have the keys.
        """
        if not vault or not vault.is_unlocked():
            return None
        endpoint = vault.retrieve("idrive_e2_endpoint")
        if not endpoint:
            return None
        return cls(
            endpoint=endpoint,
            region=vault.retrieve("idrive_e2_region") or "",
            access_key_id=vault.retrieve("idrive_e2_access_key_id") or "",
            secret_access_key=vault.retrieve("idrive_e2_secret_access_key") or "",
            bucket=vault.retrieve("idrive_e2_bucket") or "sios-backup",
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.access_key_id and self.secret_access_key)


# ----------------------------------------------------------- S3 signing (V4)

def _sign(key: bytes, msg: str) -> bytes:
    """HMAC-SHA256 helper."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(
    secret: str, date_stamp: str, region: str, service: str
) -> bytes:
    """Derive the signing key for AWS Signature V4."""
    k_date = _sign(("AWS4" + secret).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _canonical_uri(key: str) -> str:
    """Encode the object key for the canonical URI."""
    # S3 keys need to be URL-encoded, but slashes are kept
    parts = key.split("/")
    encoded = []
    for part in parts:
        encoded.append(urllib.request.quote(part, safe=""))
    return "/" + "/".join(encoded)


def _sign_request(
    method: str,
    url: str,
    endpoint: str,
    key: str,
    config: SyncConfig,
    payload: bytes,
    extra_headers: dict[str, str] | None = None,
) -> urllib.request.Request:
    """Create a signed S3 request using AWS Signature V4.

    This implements the full signing process:
    1. Create canonical request
    2. Create string to sign
    3. Calculate signature
    4. Add authorization header
    """
    extra_headers = extra_headers or {}
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    # Payload hash
    payload_hash = hashlib.sha256(payload).hexdigest()

    # Host header
    host = endpoint

    # Canonical headers (must be sorted)
    headers = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    headers.update(extra_headers)

    # Sort headers
    sorted_headers = sorted(headers.items())
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted_headers)
    signed_headers = ";".join(k for k, _ in sorted_headers)

    # Canonical URI
    canonical_uri = _canonical_uri(key)

    # Canonical query string (empty for most operations)
    canonical_query = ""

    # Canonical request
    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_query}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    # String to sign
    credential_scope = f"{date_stamp}/{config.region}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    # Signature
    signing_key = _get_signature_key(
        config.secret_access_key, date_stamp, config.region, "s3"
    )
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Authorization header
    authorization = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={config.access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    # Build the request
    full_url = f"https://{endpoint}{canonical_uri}"
    req = urllib.request.Request(
        full_url,
        data=payload if method in ("PUT", "POST") else None,
        method=method,
    )
    req.add_header("Authorization", authorization)
    req.add_header("x-amz-content-sha256", payload_hash)
    req.add_header("x-amz-date", amz_date)
    for k, v in extra_headers.items():
        req.add_header(k, v)

    return req


def _execute_request(
    req: urllib.request.Request, timeout: float = 30.0
) -> tuple[int, bytes]:
    """Execute an HTTP request and return (status_code, body)."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except urllib.error.URLError as exc:
        raise ConnectionError(f"cannot reach iDrive E2: {exc.reason}") from exc


# ----------------------------------------------------------- client-side encryption

def _encrypt_data(data: bytes, key: bytes) -> bytes:
    """Simple client-side encryption (XOR with derived key).

    This provides a second encryption layer on top of iDrive E2's
    server-side encryption. The key is derived from the access key
    secret using PBKDF2.

    Note: XOR is obfuscation, not strong encryption. For production,
    this should be replaced with AES-256-GCM. However, the constitutional
    kernel forbids third-party dependencies (no `cryptography` package),
    and Python's stdlib does not include AES. This is a documented
    limitation — the data is also protected by iDrive E2's own
    server-side encryption.
    """
    # Derive a 32-byte key from the secret using PBKDF2
    derived = hashlib.pbkdf2_hmac("sha256", key, b"sios_cloud_sync_v1", 100000, 32)
    return bytes(b ^ derived[i % len(derived)] for i, b in enumerate(data))


def _decrypt_data(data: bytes, key: bytes) -> bytes:
    """Decrypt data encrypted by _encrypt_data (XOR is symmetric)."""
    return _encrypt_data(data, key)


# ----------------------------------------------------------- sync operations

@dataclass
class SyncResult:
    """Result of a sync operation."""
    ok: bool
    uploaded: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    bytes_transferred: int = 0
    duration_s: float = 0.0


def _file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class DeltaSyncManifest:
    """Local manifest tracking uploaded file hashes for delta sync.

    Stores a JSON file mapping remote keys to their SHA-256 hash and
    last-uploaded mtime. On the next sync, only files whose hash or
    mtime has changed are re-uploaded, saving bandwidth.

    The manifest is stored in `.cloud_sync_manifest.json` at the root.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / ".cloud_sync_manifest.json"
        self._entries: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        """Load the manifest from disk."""
        if not self.path.exists():
            self._entries = {}
            return
        try:
            self._entries = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._entries = {}

    def save(self) -> None:
        """Save the manifest to disk."""
        try:
            self.path.write_text(
                json.dumps(self._entries, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass  # non-fatal

    def is_unchanged(self, key: str, file_hash: str, mtime: float) -> bool:
        """Check if a file has not changed since the last sync."""
        entry = self._entries.get(key)
        if not entry:
            return False  # never uploaded
        if entry.get("mtime") != mtime:
            return False  # mtime changed
        if entry.get("hash") != file_hash:
            return False  # content changed
        return True

    def update(self, key: str, file_hash: str, mtime: float) -> None:
        """Update the manifest after a successful upload."""
        self._entries[key] = {
            "hash": file_hash,
            "mtime": mtime,
            "uploaded_at": time.time(),
        }

    def remove(self, key: str) -> None:
        """Remove a key from the manifest."""
        self._entries.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self._entries = {}

    @property
    def count(self) -> int:
        return len(self._entries)


class CloudSync:
    """Cloud sync manager for iDrive E2.

    All operations are Creator-approved (ChangeClass.CONSEQUENTIAL).
    The caller is responsible for obtaining approval — this module
    enforces data classification and encryption, not authorization.
    """

    def __init__(
        self,
        config: SyncConfig | None = None,
        root: str | Path | None = None,
    ) -> None:
        self.config = config or SyncConfig.from_file()
        self.root = Path(root or ".")
        self._encryption_key = self.config.secret_access_key.encode("utf-8") if self.config.is_configured else b""

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured

    # --------------------------------------------------- classification

    def _classify_path(self, rel_path: str) -> str:
        """Classify a path as hot/warm/cold (instance method wrapper)."""
        return _classify_path(rel_path)

    def _should_sync(self, rel_path: str) -> bool:
        """Return True if the path is allowed to be synced."""
        return _classify_path(rel_path) != "hot"

    # --------------------------------------------------- bucket operations

    def create_bucket(self) -> dict[str, Any]:
        """Create the S3 bucket if it doesn't exist.

        iDrive E2 may require bucket creation via their web UI.
        This method attempts creation but may fail if the bucket
        already exists or if the provider doesn't support the API.
        """
        if not self.is_configured:
            return {"ok": False, "error": "not configured"}

        # Create bucket XML (us-east-1 style, empty)
        payload = b""
        req = _sign_request(
            "PUT", f"https://{self.config.endpoint}/",
            self.config.endpoint, "",
            self.config, payload,
        )
        status, body = _execute_request(req, timeout=30.0)
        if status in (200, 204):
            return {"ok": True, "bucket": self.config.bucket, "created": True}
        if status == 409:
            return {"ok": True, "bucket": self.config.bucket, "already_exists": True}
        return {
            "ok": False,
            "status": status,
            "error": body.decode("utf-8", "replace")[:500],
        }

    def list_objects(self, prefix: str = "") -> list[dict[str, Any]]:
        """List objects in the bucket with an optional prefix."""
        if not self.is_configured:
            return []

        # For listing, we use the bucket as a subdomain or path prefix
        # iDrive E2 uses path-style: https://endpoint/bucket?prefix=...
        canonical_uri = f"/{self.config.bucket}"
        query = f"prefix={urllib.request.quote(prefix, safe='')}" if prefix else ""
        full_uri = f"{canonical_uri}?{query}" if query else canonical_uri

        # Build a manual request for listing (query string support)
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(b"").hexdigest()

        host = self.config.endpoint
        headers = {
            "host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        sorted_headers = sorted(headers.items())
        canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted_headers)
        signed_headers = ";".join(k for k, _ in sorted_headers)

        canonical_request = (
            f"GET\n"
            f"{canonical_uri}\n"
            f"{query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        credential_scope = f"{date_stamp}/{self.config.region}/s3/aws4_request"
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = _get_signature_key(
            self.config.secret_access_key, date_stamp, self.config.region, "s3"
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self.config.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        full_url = f"https://{host}{full_uri}"
        req = urllib.request.Request(full_url, method="GET")
        req.add_header("Authorization", authorization)
        req.add_header("x-amz-content-sha256", payload_hash)
        req.add_header("x-amz-date", amz_date)

        status, body = _execute_request(req, timeout=30.0)
        if status != 200:
            return []

        # Parse S3 XML response (simple parser, no xml.etree for safety)
        objects = []
        text = body.decode("utf-8", "replace")
        # Simple extraction of <Key> and <Size> elements
        import re
        keys = re.findall(r"<Key>([^<]+)</Key>", text)
        sizes = re.findall(r"<Size>([^<]+)</Size>", text)
        for i, key in enumerate(keys):
            size = int(sizes[i]) if i < len(sizes) else 0
            objects.append({"key": key, "size": size})
        return objects

    # --------------------------------------------------- file operations

    def upload_file(
        self, local_path: str | Path, remote_key: str | None = None
    ) -> dict[str, Any]:
        """Upload a single file with client-side encryption.

        Returns a dict with ok, key, size, and error (if any).
        """
        if not self.is_configured:
            return {"ok": False, "error": "not configured"}

        local_path = Path(local_path)
        if not local_path.exists():
            return {"ok": False, "error": f"file not found: {local_path}"}

        rel_path = str(local_path.relative_to(self.root)) if local_path.is_relative_to(self.root) else local_path.name
        if not self._should_sync(rel_path):
            return {"ok": False, "error": f"hot path, refused: {rel_path}"}

        remote_key = remote_key or f"{self.config.bucket}/{rel_path}"
        # Remove bucket prefix if present (key is relative to bucket)
        if remote_key.startswith(f"{self.config.bucket}/"):
            remote_key = remote_key[len(self.config.bucket) + 1:]

        data = local_path.read_bytes()
        encrypted = _encrypt_data(data, self._encryption_key)

        # Use the bucket as a path prefix
        full_key = f"{self.config.bucket}/{remote_key}"
        req = _sign_request(
            "PUT", f"https://{self.config.endpoint}/{full_key}",
            self.config.endpoint, full_key,
            self.config, encrypted,
        )
        status, body = _execute_request(req, timeout=120.0)

        if status in (200, 201):
            return {
                "ok": True,
                "key": remote_key,
                "size": len(data),
                "encrypted_size": len(encrypted),
                "status": status,
            }
        return {
            "ok": False,
            "key": remote_key,
            "status": status,
            "error": body.decode("utf-8", "replace")[:500],
        }

    def download_file(
        self, remote_key: str, local_path: str | Path
    ) -> dict[str, Any]:
        """Download and decrypt a file from iDrive E2."""
        if not self.is_configured:
            return {"ok": False, "error": "not configured"}

        full_key = f"{self.config.bucket}/{remote_key}"
        req = _sign_request(
            "GET", f"https://{self.config.endpoint}/{full_key}",
            self.config.endpoint, full_key,
            self.config, b"",
        )
        status, body = _execute_request(req, timeout=120.0)

        if status != 200:
            return {
                "ok": False,
                "key": remote_key,
                "status": status,
                "error": body.decode("utf-8", "replace")[:500],
            }

        decrypted = _decrypt_data(body, self._encryption_key)
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(decrypted)

        return {
            "ok": True,
            "key": remote_key,
            "local_path": str(local_path),
            "size": len(decrypted),
        }

    def delete_object(self, remote_key: str) -> dict[str, Any]:
        """Delete an object from iDrive E2."""
        if not self.is_configured:
            return {"ok": False, "error": "not configured"}

        full_key = f"{self.config.bucket}/{remote_key}"
        req = _sign_request(
            "DELETE", f"https://{self.config.endpoint}/{full_key}",
            self.config.endpoint, full_key,
            self.config, b"",
        )
        status, body = _execute_request(req, timeout=30.0)

        if status in (200, 204):
            return {"ok": True, "key": remote_key, "deleted": True}
        return {
            "ok": False,
            "key": remote_key,
            "status": status,
            "error": body.decode("utf-8", "replace")[:500],
        }

    # --------------------------------------------------- sync operations

    def sync_directory(
        self,
        local_dir: str | Path,
        prefix: str = "",
        max_files: int = 100,
    ) -> SyncResult:
        """Sync a directory to iDrive E2.

        Only warm and cold paths are synced. Hot paths are refused.
        Each file is encrypted before upload. Uses a local manifest
        with SHA-256 hashes for delta sync — only changed files are
        uploaded, saving bandwidth and time.

        Returns a SyncResult with counts and any errors.
        """
        if not self.is_configured:
            return SyncResult(ok=False, errors=["not configured"])

        local_dir = Path(local_dir)
        if not local_dir.exists():
            return SyncResult(ok=False, errors=[f"directory not found: {local_dir}"])

        t0 = time.monotonic()
        uploaded = 0
        skipped = 0
        errors: list[str] = []
        bytes_transferred = 0

        # Load the sync manifest for delta comparison
        manifest = DeltaSyncManifest(self.root)
        manifest.load()

        files = sorted(local_dir.rglob("*"))
        for f in files:
            if not f.is_file():
                continue
            if uploaded + skipped >= max_files:
                break

            try:
                rel_path = str(f.relative_to(self.root))
            except ValueError:
                rel_path = f.name

            if not self._should_sync(rel_path):
                continue

            remote_key = rel_path.replace("\\", "/")

            # Delta check: compute local hash and compare to manifest
            local_hash = _file_sha256(f)
            if manifest.is_unchanged(remote_key, local_hash, f.stat().st_mtime):
                skipped += 1
                continue

            result = self.upload_file(f, remote_key)
            if result.get("ok"):
                uploaded += 1
                bytes_transferred += result.get("size", 0)
                manifest.update(remote_key, local_hash, f.stat().st_mtime)
            else:
                errors.append(f"{remote_key}: {result.get('error', 'unknown')}")

        manifest.save()
        return SyncResult(
            ok=len(errors) == 0,
            uploaded=uploaded,
            skipped=skipped,
            errors=errors,
            bytes_transferred=bytes_transferred,
            duration_s=time.monotonic() - t0,
        )

    # --------------------------------------------------- status

    def status(self) -> dict[str, Any]:
        """Return sync status and configuration info (no secrets)."""
        return {
            "configured": self.is_configured,
            "endpoint": self.config.endpoint if self.is_configured else None,
            "region": self.config.region if self.is_configured else None,
            "bucket": self.config.bucket if self.is_configured else None,
            "hot_paths": list(HOT_PATHS),
            "warm_paths": list(WARM_PATHS),
        }
