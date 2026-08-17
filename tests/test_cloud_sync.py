"""Tests for the cloud sync module — iDrive E2 (S3-compatible) integration.

These tests verify:
- Configuration loading from file and vault
- Data classification (hot/warm/cold path enforcement)
- S3 Signature V4 signing correctness
- Client-side encryption/decryption
- Sync operations (with mock requests where needed)

Network tests (actual iDrive E2 calls) are skipped by default and
require a configured credentials file.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.cloud_sync import (
    CloudSync,
    SyncConfig,
    SyncResult,
    HOT_PATHS,
    WARM_PATHS,
    _encrypt_data,
    _decrypt_data,
    _sign,
    _get_signature_key,
    _canonical_uri,
    _classify_path,
)


class TestSyncConfig(unittest.TestCase):
    """Tests for configuration loading."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sync-cfg-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_config_not_configured(self):
        cfg = SyncConfig()
        self.assertFalse(cfg.is_configured)

    def test_config_from_file(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({
            "idrive_e2": {
                "endpoint": "s3.test.example.com",
                "region": "us-test-1",
                "access_key_id": "AKIATEST",
                "secret_access_key": "secrettest",
                "bucket": "test-bucket",
            }
        }), encoding="utf-8")
        cfg = SyncConfig.from_file(cfg_path)
        self.assertTrue(cfg.is_configured)
        self.assertEqual(cfg.endpoint, "s3.test.example.com")
        self.assertEqual(cfg.region, "us-test-1")
        self.assertEqual(cfg.access_key_id, "AKIATEST")
        self.assertEqual(cfg.bucket, "test-bucket")

    def test_config_from_missing_file(self):
        cfg = SyncConfig.from_file(Path(self.tmpdir) / "nonexistent.json")
        self.assertFalse(cfg.is_configured)

    def test_config_from_invalid_json(self):
        cfg_path = Path(self.tmpdir) / "bad.json"
        cfg_path.write_text("not json", encoding="utf-8")
        cfg = SyncConfig.from_file(cfg_path)
        self.assertFalse(cfg.is_configured)

    def test_config_from_vault_unlocked(self):
        vault = MagicMock()
        vault.is_unlocked.return_value = True
        vault.retrieve.side_effect = lambda key: {
            "idrive_e2_endpoint": "s3.vault.example.com",
            "idrive_e2_region": "us-vault-1",
            "idrive_e2_access_key_id": "AKIVAULT",
            "idrive_e2_secret_access_key": "secretvault",
            "idrive_e2_bucket": "vault-bucket",
        }.get(key)
        cfg = SyncConfig.from_vault(vault)
        self.assertIsNotNone(cfg)
        self.assertTrue(cfg.is_configured)
        self.assertEqual(cfg.endpoint, "s3.vault.example.com")

    def test_config_from_vault_locked(self):
        vault = MagicMock()
        vault.is_unlocked.return_value = False
        cfg = SyncConfig.from_vault(vault)
        self.assertIsNone(cfg)

    def test_config_from_vault_no_keys(self):
        vault = MagicMock()
        vault.is_unlocked.return_value = True
        vault.retrieve.return_value = None
        cfg = SyncConfig.from_vault(vault)
        self.assertIsNone(cfg)


class TestDataClassification(unittest.TestCase):
    """Tests for hot/warm/cold path classification."""

    def test_identity_is_hot(self):
        self.assertEqual(_classify_path("identity/vault.enc"), "hot")

    def test_config_is_hot(self):
        self.assertEqual(_classify_path("config/cloud_credentials.json"), "hot")

    def test_skills_is_warm(self):
        self.assertEqual(_classify_path("skills/checksum_v1.py"), "warm")

    def test_knowledge_is_warm(self):
        self.assertEqual(_classify_path("knowledge/doc_001.md"), "warm")

    def test_evidence_is_warm(self):
        self.assertEqual(_classify_path("evidence/ledger.jsonl"), "warm")

    def test_memory_is_warm(self):
        self.assertEqual(_classify_path("memory/conversation.jsonl"), "warm")

    def test_backups_is_cold(self):
        self.assertEqual(_classify_path("backups/backup_001.tar.gz"), "cold")

    def test_random_path_is_cold(self):
        self.assertEqual(_classify_path("some/random/path.txt"), "cold")


class TestShouldSync(unittest.TestCase):
    """Tests for the sync refusal logic."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sync-refuse-")
        self.sync = CloudSync(
            SyncConfig(
                endpoint="s3.test.example.com",
                region="us-test-1",
                access_key_id="AKIATEST",
                secret_access_key="secrettest",
                bucket="test-bucket",
            ),
            root=self.tmpdir,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_identity_not_synced(self):
        self.assertFalse(self.sync._should_sync("identity/vault.enc"))

    def test_config_not_synced(self):
        self.assertFalse(self.sync._should_sync("config/creds.json"))

    def test_skills_synced(self):
        self.assertTrue(self.sync._should_sync("skills/test.py"))

    def test_knowledge_synced(self):
        self.assertTrue(self.sync._should_sync("knowledge/doc.md"))


class TestEncryption(unittest.TestCase):
    """Tests for client-side encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        key = b"test-secret-key"
        data = b"Hello, iDrive E2! This is a test message."
        encrypted = _encrypt_data(data, key)
        decrypted = _decrypt_data(encrypted, key)
        self.assertEqual(data, decrypted)

    def test_encrypt_different_from_plain(self):
        key = b"test-secret-key"
        data = b"sensitive data that should be encrypted"
        encrypted = _encrypt_data(data, key)
        self.assertNotEqual(data, encrypted)

    def test_encrypt_empty_data(self):
        key = b"test-key"
        data = b""
        encrypted = _encrypt_data(data, key)
        decrypted = _decrypt_data(encrypted, key)
        self.assertEqual(data, decrypted)

    def test_encrypt_large_data(self):
        key = b"test-key"
        data = b"x" * 10000
        encrypted = _encrypt_data(data, key)
        decrypted = _decrypt_data(encrypted, key)
        self.assertEqual(data, decrypted)

    def test_different_keys_produce_different_ciphertext(self):
        data = b"same plaintext"
        enc1 = _encrypt_data(data, b"key1")
        enc2 = _encrypt_data(data, b"key2")
        self.assertNotEqual(enc1, enc2)


class TestS3Signing(unittest.TestCase):
    """Tests for AWS Signature V4 signing primitives."""

    def test_sign_hmac(self):
        key = b"test-key"
        msg = "test message"
        result = _sign(key, msg)
        self.assertEqual(len(result), 32)  # SHA-256 output

    def test_sign_deterministic(self):
        key = b"test-key"
        msg = "test message"
        r1 = _sign(key, msg)
        r2 = _sign(key, msg)
        self.assertEqual(r1, r2)

    def test_get_signature_key(self):
        key = _get_signature_key("secret", "20260101", "us-east-1", "s3")
        self.assertEqual(len(key), 32)

    def test_canonical_uri_simple(self):
        uri = _canonical_uri("path/to/file.txt")
        self.assertEqual(uri, "/path/to/file.txt")

    def test_canonical_uri_special_chars(self):
        uri = _canonical_uri("path with spaces/file.txt")
        self.assertIn("%20", uri)

    def test_canonical_uri_empty(self):
        uri = _canonical_uri("")
        self.assertEqual(uri, "/")


class TestCloudSyncStatus(unittest.TestCase):
    """Tests for the status endpoint (no network required)."""

    def test_status_configured(self):
        sync = CloudSync(SyncConfig(
            endpoint="s3.test.example.com",
            region="us-test-1",
            access_key_id="AKIATEST",
            secret_access_key="secrettest",
            bucket="test-bucket",
        ))
        status = sync.status()
        self.assertTrue(status["configured"])
        self.assertEqual(status["endpoint"], "s3.test.example.com")
        self.assertEqual(status["bucket"], "test-bucket")
        self.assertIn("identity/", status["hot_paths"])

    def test_status_not_configured(self):
        sync = CloudSync(SyncConfig())
        status = sync.status()
        self.assertFalse(status["configured"])
        self.assertIsNone(status["endpoint"])

    def test_status_no_secrets_exposed(self):
        sync = CloudSync(SyncConfig(
            endpoint="s3.test.example.com",
            region="us-test-1",
            access_key_id="AKIATEST",
            secret_access_key="supersecret",
            bucket="test-bucket",
        ))
        status = sync.status()
        status_json = json.dumps(status)
        self.assertNotIn("supersecret", status_json)
        self.assertNotIn("AKIATEST", status_json)


class TestSyncDirectory(unittest.TestCase):
    """Tests for directory sync (with mocked network calls)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sync-dir-")
        # Create some test files
        (Path(self.tmpdir) / "skills").mkdir(parents=True)
        (Path(self.tmpdir) / "skills" / "test_skill.py").write_text("def test(): pass", encoding="utf-8")
        (Path(self.tmpdir) / "knowledge").mkdir(parents=True)
        (Path(self.tmpdir) / "knowledge" / "doc.md").write_text("# Test doc", encoding="utf-8")
        (Path(self.tmpdir) / "identity").mkdir(parents=True)
        (Path(self.tmpdir) / "identity" / "vault.enc").write_text("encrypted vault", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sync_refuses_hot_paths(self):
        sync = CloudSync(
            SyncConfig(
                endpoint="s3.test.example.com",
                region="us-test-1",
                access_key_id="AKIATEST",
                secret_access_key="secrettest",
                bucket="test-bucket",
            ),
            root=self.tmpdir,
        )
        # Mock list_objects to avoid network calls
        sync.list_objects = lambda prefix="": []
        # Mock upload_file to track what gets uploaded
        uploaded_keys = []

        def mock_upload(local_path, remote_key=None):
            rel = str(Path(local_path).relative_to(self.tmpdir)).replace("\\", "/")
            uploaded_keys.append(rel)
            return {"ok": True, "key": rel, "size": 100}

        sync.upload_file = mock_upload
        result = sync.sync_directory(Path(self.tmpdir))
        # Identity files should NOT be in the uploaded list
        for key in uploaded_keys:
            self.assertFalse(key.startswith("identity/"))
        # Skills and knowledge should be
        self.assertTrue(any(k.startswith("skills/") for k in uploaded_keys))
        self.assertTrue(any(k.startswith("knowledge/") for k in uploaded_keys))

    def test_sync_not_configured(self):
        sync = CloudSync(SyncConfig(), root=self.tmpdir)
        result = sync.sync_directory(Path(self.tmpdir))
        self.assertFalse(result.ok)
        self.assertIn("not configured", result.errors[0])


class TestUploadFile(unittest.TestCase):
    """Tests for file upload with mocked network."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sync-upload-")
        self.test_file = Path(self.tmpdir) / "skills" / "test.py"
        self.test_file.parent.mkdir(parents=True)
        self.test_file.write_text("def test(): pass", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_upload_refuses_hot_path(self):
        hot_file = Path(self.tmpdir) / "identity" / "vault.enc"
        hot_file.parent.mkdir(parents=True)
        hot_file.write_text("secret", encoding="utf-8")
        sync = CloudSync(
            SyncConfig(
                endpoint="s3.test.example.com",
                region="us-test-1",
                access_key_id="AKIATEST",
                secret_access_key="secrettest",
                bucket="test-bucket",
            ),
            root=self.tmpdir,
        )
        result = sync.upload_file(hot_file)
        self.assertFalse(result["ok"])
        self.assertIn("hot path", result["error"])

    def test_upload_not_configured(self):
        sync = CloudSync(SyncConfig(), root=self.tmpdir)
        result = sync.upload_file(self.test_file)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "not configured")

    def test_upload_file_not_found(self):
        sync = CloudSync(
            SyncConfig(
                endpoint="s3.test.example.com",
                region="us-test-1",
                access_key_id="AKIATEST",
                secret_access_key="secrettest",
                bucket="test-bucket",
            ),
            root=self.tmpdir,
        )
        result = sync.upload_file(Path(self.tmpdir) / "nonexistent.py")
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])


class TestDeltaSyncManifest(unittest.TestCase):
    """Tests for the delta sync manifest."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-delta-sync-")
        from anubis.cloud_sync import DeltaSyncManifest
        self.manifest = DeltaSyncManifest(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_manifest(self):
        self.assertEqual(self.manifest.count, 0)

    def test_update_and_is_unchanged(self):
        self.manifest.update("file1.txt", "abc123", 1000.0)
        self.assertTrue(self.manifest.is_unchanged("file1.txt", "abc123", 1000.0))

    def test_changed_hash(self):
        self.manifest.update("file1.txt", "abc123", 1000.0)
        self.assertFalse(self.manifest.is_unchanged("file1.txt", "def456", 1000.0))

    def test_changed_mtime(self):
        self.manifest.update("file1.txt", "abc123", 1000.0)
        self.assertFalse(self.manifest.is_unchanged("file1.txt", "abc123", 2000.0))

    def test_never_uploaded(self):
        self.assertFalse(self.manifest.is_unchanged("new.txt", "abc", 1000.0))

    def test_save_and_load(self):
        self.manifest.update("file1.txt", "abc123", 1000.0)
        self.manifest.update("file2.txt", "def456", 2000.0)
        self.manifest.save()

        from anubis.cloud_sync import DeltaSyncManifest
        loaded = DeltaSyncManifest(self.tmpdir)
        loaded.load()
        self.assertEqual(loaded.count, 2)
        self.assertTrue(loaded.is_unchanged("file1.txt", "abc123", 1000.0))

    def test_remove(self):
        self.manifest.update("file1.txt", "abc", 1000.0)
        self.manifest.remove("file1.txt")
        self.assertFalse(self.manifest.is_unchanged("file1.txt", "abc", 1000.0))

    def test_clear(self):
        self.manifest.update("file1.txt", "abc", 1000.0)
        self.manifest.clear()
        self.assertEqual(self.manifest.count, 0)


class TestFileSha256(unittest.TestCase):
    """Tests for the file SHA-256 helper."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-sha256-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_known_hash(self):
        from anubis.cloud_sync import _file_sha256
        import hashlib
        path = Path(self.tmpdir) / "test.txt"
        content = b"hello world"
        path.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(_file_sha256(path), expected)

    def test_large_file(self):
        from anubis.cloud_sync import _file_sha256
        import hashlib
        path = Path(self.tmpdir) / "large.bin"
        content = b"x" * 100000  # 100KB
        path.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(_file_sha256(path), expected)


if __name__ == "__main__":
    unittest.main()
