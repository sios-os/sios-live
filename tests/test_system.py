"""Tests for SIOS networking, hardening, recovery, A/B images, and Egyptology."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from anubis.system import (
    NetworkManager, NetworkPolicy, FirewallRule, ApprovedEndpoint,
    SystemHardening, SecurityFinding,
    RecoveryManager, RecoveryStatus,
    ArtifactSigner,
)
from anubis.system2 import (
    ABImageManager, SlotStatus,
    EgyptologySupport,
)


class TestNetworkManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.net = NetworkManager(self.tmpdir)

    def test_default_policy(self):
        self.assertEqual(self.net.get_policy(), NetworkPolicy.LOCAL_ONLY)

    def test_set_policy(self):
        self.net.set_policy(NetworkPolicy.CURATED)
        self.assertEqual(self.net.get_policy(), NetworkPolicy.CURATED)

    def test_offline_blocks_all(self):
        self.net.set_policy(NetworkPolicy.OFFLINE)
        self.assertFalse(self.net.is_endpoint_allowed("anything.com"))

    def test_curated_allows_approved(self):
        self.net.set_policy(NetworkPolicy.CURATED)
        ep = ApprovedEndpoint(
            endpoint_id="ep1", hostname="example.com",
            port=443, purpose="test", allowed=True,
        )
        self.net.add_endpoint(ep)
        self.assertTrue(self.net.is_endpoint_allowed("example.com"))
        self.assertFalse(self.net.is_endpoint_allowed("bad.com"))

    def test_firewall_script(self):
        script = self.net.generate_firewall_script()
        self.assertIn("iptables", script)
        self.assertIn("LOCAL_ONLY", script)


class TestSystemHardening(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.hardening = SystemHardening(self.tmpdir)

    def test_kernel_params(self):
        self.assertGreater(len(SystemHardening.KERNEL_PARAMS), 10)

    def test_hardening_script(self):
        script = self.hardening.generate_hardening_script()
        self.assertIn("sysctl", script)
        self.assertIn("systemctl", script)

    def test_findings(self):
        finding = SecurityFinding(
            finding_id="f1", severity="high",
            description="Test vulnerability", status="open",
        )
        self.hardening.add_finding(finding)
        self.assertEqual(len(self.hardening.open_findings()), 1)
        self.hardening.update_finding_status("f1", "mitigated", "patched")
        self.assertEqual(len(self.hardening.open_findings()), 0)


class TestRecoveryManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.recovery = RecoveryManager(self.tmpdir)

    def test_steps_defined(self):
        self.assertGreater(len(RecoveryManager.RECOVERY_STEPS), 10)

    def test_run_drill(self):
        drill = self.recovery.run_drill()
        self.assertEqual(drill.status, RecoveryStatus.COMPLETED)
        self.assertEqual(drill.steps_completed, drill.steps_total)

    def test_recovery_script(self):
        script = self.recovery.generate_recovery_script()
        self.assertIn("SIOS Recovery", script)
        self.assertIn("cryptsetup", script)


class TestArtifactSigner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.signer = ArtifactSigner(self.tmpdir)
        self.signer.set_signing_key("test_key_123")

    def test_sign_and_verify(self):
        # Create a test file
        test_file = Path(self.tmpdir) / "test.bin"
        test_file.write_bytes(b"test artifact content")
        result = self.signer.sign_artifact(str(test_file))
        self.assertTrue(result["signed"])
        # Verify
        verify = self.signer.verify_artifact(str(test_file))
        self.assertTrue(verify["verified"])

    def test_verify_modified(self):
        test_file = Path(self.tmpdir) / "test2.bin"
        test_file.write_bytes(b"original content")
        self.signer.sign_artifact(str(test_file))
        # Modify
        test_file.write_bytes(b"modified content")
        result = self.signer.verify_artifact(str(test_file))
        self.assertFalse(result["verified"])


class TestABImageManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ab = ABImageManager(self.tmpdir)

    def test_initial_slots(self):
        slots = self.ab.slots()
        self.assertEqual(len(slots), 2)
        active = self.ab.get_active_slot()
        self.assertEqual(active.slot_id, "A")

    def test_update_and_promote(self):
        result = self.ab.update_inactive_slot("2.0.0", "hash123")
        self.assertEqual(result["slot"], "B")
        result = self.ab.promote(probation_days=7)
        self.assertEqual(result["new_active"], "B")
        active = self.ab.get_active_slot()
        self.assertEqual(active.status, SlotStatus.PROBATION)

    def test_commit(self):
        self.ab.update_inactive_slot("2.0.0", "hash123")
        self.ab.promote()
        result = self.ab.commit()
        self.assertEqual(result["status"], "active")

    def test_rollback(self):
        self.ab.update_inactive_slot("2.0.0", "hash123")
        self.ab.promote()
        result = self.ab.rollback()
        self.assertEqual(result["rolled_back_to"], "A")


class TestEgyptologySupport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.egypt = EgyptologySupport(self.tmpdir)

    def test_lookup_sign(self):
        result = self.egypt.lookup_sign("A1")
        self.assertNotIn("error", result)
        self.assertEqual(result["description"], "seated man")

    def test_lookup_unknown_sign(self):
        result = self.egypt.lookup_sign("ZZ99")
        self.assertIn("error", result)

    def test_lookup_word(self):
        result = self.egypt.lookup_word("nsw")
        self.assertNotIn("error", result)
        self.assertEqual(result["translation"], "king")

    def test_signs_by_category(self):
        signs = self.egypt.signs_by_category("A")
        self.assertGreater(len(signs), 0)
        for s in signs:
            self.assertEqual(s["category"], "A")

    def test_categories(self):
        cats = self.egypt.categories()
        self.assertIn("A", cats)
        self.assertIn("D", cats)

    def test_search_dictionary(self):
        results = self.egypt.search_dictionary("king")
        self.assertGreater(len(results), 0)

    def test_stats(self):
        stats = self.egypt.stats()
        self.assertGreater(stats["total_signs"], 20)
        self.assertGreater(stats["total_words"], 15)


if __name__ == "__main__":
    unittest.main()
