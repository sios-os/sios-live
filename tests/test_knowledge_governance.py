"""Tests for the SIOS knowledge base, registry, agents, and governance modules."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add the repository root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from anubis.registry import (
    Registry, KnowledgeDepth, SourceTier, SourceClass,
    Specialty, DomainDirector, SourceRecord,
)
from anubis.knowledge import KnowledgeBase, PopulationPipeline
from anubis.identity import IdentityService, IdentityVault
from anubis.governance import (
    PolicyEngine, CapabilityBroker, Court, CourtVerdict,
    Mandate, Transaction, TransactionClass, SpendingLimit,
)
from anubis.operations import (
    MidnightPurge, PackageManager, FinancialLedger, FinancialEntry,
    RetentionClass, PackageStatus,
)


class TestRegistry(unittest.TestCase):
    """Test the domain and specialty registry."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.registry = Registry(self.tmpdir)

    def test_seeds_directors(self):
        directors = self.registry.directors()
        self.assertEqual(len(directors), 14)

    def test_seeds_specialties(self):
        specialties = self.registry.specialties()
        self.assertGreaterEqual(len(specialties), 260)

    def test_seeds_verifiers(self):
        verifiers = self.registry.verifiers()
        self.assertEqual(len(verifiers), 14)

    def test_specialties_have_directors(self):
        for spec in self.registry.specialties():
            self.assertTrue(spec.parent_director_id)
            director = self.registry.get_director(spec.parent_director_id)
            self.assertIsNotNone(director)

    def test_regulated_specialties(self):
        regulated = [s for s in self.registry.specialties() if s.regulated_domain]
        self.assertGreater(len(regulated), 5)

    def test_all_start_at_k0(self):
        for spec in self.registry.specialties():
            self.assertEqual(spec.knowledge_depth, KnowledgeDepth.K0)

    def test_persists_to_disk(self):
        # Reload from disk
        registry2 = Registry(self.tmpdir)
        self.assertEqual(len(registry2.directors()), 14)
        self.assertGreaterEqual(len(registry2.specialties()), 260)

    def test_update_depth(self):
        specs = self.registry.specialties()
        first_id = specs[0].specialty_id
        self.assertTrue(self.registry.update_specialty_depth(first_id, KnowledgeDepth.K1))
        spec = self.registry.get_specialty(first_id)
        self.assertEqual(spec.knowledge_depth, KnowledgeDepth.K1)

    def test_register_source(self):
        src = SourceRecord(
            source_id="test_src", name="Test Source",
            publisher="Test Publisher", tier=SourceTier.T2,
            source_class=SourceClass.B, license="CC-BY-4.0",
            status="discovered",
        )
        self.registry.register_source(src)
        retrieved = self.registry.get_source("test_src")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Source")

    def test_stats(self):
        stats = self.registry.stats()
        self.assertEqual(stats["directors"], 14)
        self.assertGreaterEqual(stats["specialties"], 260)
        self.assertEqual(stats["verifiers"], 14)


class TestKnowledgeBase(unittest.TestCase):
    """Test the knowledge base and population pipeline."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.registry = Registry(self.tmpdir)
        self.kb = KnowledgeBase(Path(self.tmpdir) / "knowledge", self.registry)

    def test_quarantine_ingest(self):
        doc_id = self.kb.ingest_to_quarantine(
            title="Python Standard Library",
            content="The os module provides operating system interfaces.",
            specialty_id="computing_operating_systems",
            license="PSF",
        )
        self.assertTrue(doc_id)
        self.assertEqual(self.kb.quarantine_size(), 1)
        self.assertEqual(self.kb.library_size(), 0)

    def test_promote_from_quarantine(self):
        doc_id = self.kb.ingest_to_quarantine(
            title="Python Tutorial",
            content="Python is a high-level programming language.",
            specialty_id="computing_computer_science",
        )
        self.assertTrue(self.kb.promote_from_quarantine(doc_id, SourceTier.T3))
        self.assertEqual(self.kb.library_size(), 1)
        self.assertEqual(self.kb.quarantine_size(), 0)

    def test_reject_from_quarantine(self):
        doc_id = self.kb.ingest_to_quarantine(
            title="Bad Content",
            content="This is untrusted content.",
        )
        self.assertTrue(self.kb.reject_from_quarantine(doc_id))
        self.assertEqual(self.kb.quarantine_size(), 0)

    def test_retrieve(self):
        # Add a document to the library
        doc_id = self.kb.ingest_to_quarantine(
            title="Python os module",
            content="The os module provides a portable way of using operating system dependent functionality.",
            specialty_id="computing_operating_systems",
            tags=["python", "os", "operating system"],
        )
        self.kb.promote_from_quarantine(doc_id, SourceTier.T3)
        # Retrieve
        results = self.kb.retrieve("python os module")
        self.assertGreater(len(results), 0)
        self.assertIn("python", results[0].title.lower())

    def test_retrieve_context(self):
        doc_id = self.kb.ingest_to_quarantine(
            title="Python Lists",
            content="Lists are mutable sequences in Python.",
            tags=["python", "lists", "data structures"],
        )
        self.kb.promote_from_quarantine(doc_id, SourceTier.T3)
        context = self.kb.retrieve_context("python lists")
        self.assertIn("KNOWLEDGE LIBRARY", context)
        self.assertIn("Python Lists", context)

    def test_population_pipeline(self):
        pipeline = PopulationPipeline(self.registry, self.kb)
        result = pipeline.populate_specialty(
            "computing_computer_science",
            [
                {"title": "Python Basics", "content": "Python is a programming language.", "license": "PSF"},
                {"title": "Data Structures", "content": "Lists, dicts, sets.", "license": "PSF"},
            ],
            creator_approved=True,
        )
        self.assertEqual(result["promoted"], 2)
        self.assertEqual(result["quarantined"], 0)

    def test_population_without_approval(self):
        pipeline = PopulationPipeline(self.registry, self.kb)
        result = pipeline.populate_specialty(
            "computing_computer_science",
            [{"title": "Unverified", "content": "Needs review.", "license": "unknown"}],
            creator_approved=False,
        )
        self.assertEqual(result["promoted"], 0)
        self.assertEqual(result["quarantined"], 1)

    def test_pipeline_status(self):
        pipeline = PopulationPipeline(self.registry, self.kb)
        pipeline.populate_specialty(
            "computing_computer_science",
            [{"title": "Test", "content": "Test content", "license": "PSF"}],
            creator_approved=True,
        )
        status = pipeline.pipeline_status("computing_computer_science")
        self.assertEqual(status["library_docs"], 1)
        self.assertEqual(status["knowledge_depth"], KnowledgeDepth.K1)


class TestIdentityService(unittest.TestCase):
    """Test the identity service and vault."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.idsvc = IdentityService(self.tmpdir)

    def test_enroll_creator(self):
        result = self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        self.assertNotIn("error", result)
        self.assertEqual(result["display_name"], "Storm")
        self.assertTrue(self.idsvc.is_enrolled())

    def test_enroll_requires_passphrase(self):
        result = self.idsvc.enroll_creator("Storm", "short")
        self.assertIn("error", result)

    def test_cannot_reenroll(self):
        self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        result = self.idsvc.enroll_creator("Other", "another_passphrase")
        self.assertIn("error", result)

    def test_vault(self):
        self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        self.assertTrue(self.idsvc.vault_is_unlocked())
        self.idsvc.vault_store("api_key", "secret123")
        self.assertEqual(self.idsvc.vault_retrieve("api_key"), "secret123")

    def test_vault_lock_unlock(self):
        self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        self.idsvc.lock_vault()
        self.assertFalse(self.idsvc.vault_is_unlocked())
        self.assertTrue(self.idsvc.unlock_vault("test_passphrase_123"))
        self.assertTrue(self.idsvc.vault_is_unlocked())

    def test_successor_enrollment(self):
        self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        result = self.idsvc.enroll_successor("Jane", "spouse")
        self.assertNotIn("error", result)
        self.assertTrue(self.idsvc.give_successor_consent(result["successor_id"]))

    def test_persistence(self):
        self.idsvc.enroll_creator("Storm", "test_passphrase_123")
        idsvc2 = IdentityService(self.tmpdir)
        self.assertTrue(idsvc2.is_enrolled())
        self.assertEqual(idsvc2.get_creator().display_name, "Storm")


class TestPolicyEngine(unittest.TestCase):
    """Test the policy engine."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.policy = PolicyEngine(self.tmpdir)

    def test_routine_transaction(self):
        tx = Transaction(
            transaction_id="tx1", payee="Coffee Shop",
            amount=5.50, category="food",
        )
        result = self.policy.evaluate_transaction(tx)
        self.assertEqual(result["verdict"], "approved")

    def test_prohibited_category(self):
        tx = Transaction(
            transaction_id="tx2", payee="Casino",
            amount=100, category="gambling",
        )
        result = self.policy.evaluate_transaction(tx)
        self.assertEqual(result["verdict"], "denied")

    def test_large_transaction_needs_approval(self):
        tx = Transaction(
            transaction_id="tx3", payee="Car Dealer",
            amount=25000, category="automotive",
        )
        result = self.policy.evaluate_transaction(tx)
        self.assertEqual(result["verdict"], "requires_creator_approval")

    def test_mandate_match(self):
        mandate = Mandate(
            mandate_id="m1", description="Electric bill",
            payee="Power Co", amount_limit=200, frequency="monthly",
            created_at=0, active=True,
        )
        self.policy.add_mandate(mandate)
        tx = Transaction(
            transaction_id="tx4", payee="Power Co",
            amount=150, mandate_id="m1",
        )
        result = self.policy.evaluate_transaction(tx)
        self.assertEqual(result["verdict"], "approved")


class TestCapabilityBroker(unittest.TestCase):
    """Test the capability broker."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.broker = CapabilityBroker(self.tmpdir)

    def test_issue_and_validate(self):
        token = self.broker.issue_token(
            purpose="file_write", capabilities=["fs.write"],
            duration_seconds=3600,
        )
        result = self.broker.validate_token(token.token_id, purpose="file_write")
        self.assertTrue(result["valid"])

    def test_purpose_mismatch(self):
        token = self.broker.issue_token(
            purpose="file_write", capabilities=["fs.write"],
        )
        result = self.broker.validate_token(token.token_id, purpose="file_read")
        self.assertFalse(result["valid"])

    def test_consume_token(self):
        token = self.broker.issue_token("test", ["test"])
        self.assertTrue(self.broker.consume_token(token.token_id))
        result = self.broker.validate_token(token.token_id)
        self.assertFalse(result["valid"])


class TestCourt(unittest.TestCase):
    """Test the Court review system."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.court = Court(self.tmpdir)

    def test_submit_and_approve(self):
        review_id = self.court.submit_for_review(
            artifact_hash="abc123", description="Model upgrade to qwen2.5-coder:14b",
        )
        self.court.render_verdict(review_id, CourtVerdict.APPROVED)
        result = self.court.grant_creator_approval(review_id, "abc123")
        self.assertNotIn("error", result)
        can = self.court.can_promote(review_id)
        self.assertTrue(can["can_promote"])

    def test_rejected_cannot_promote(self):
        review_id = self.court.submit_for_review("hash1", "Bad change")
        self.court.render_verdict(review_id, CourtVerdict.REJECTED)
        result = self.court.grant_creator_approval(review_id, "hash1")
        self.assertIn("error", result)

    def test_probation(self):
        review_id = self.court.submit_for_review("hash2", "Risky change")
        self.court.render_verdict(review_id, CourtVerdict.PROBATION, probation_days=30)
        self.court.grant_creator_approval(review_id, "hash2")
        can = self.court.can_promote(review_id)
        self.assertFalse(can["can_promote"])
        self.assertIn("probation", can["reason"])

    def test_hash_mismatch(self):
        review_id = self.court.submit_for_review("hash3", "Test")
        self.court.render_verdict(review_id, CourtVerdict.APPROVED)
        result = self.court.grant_creator_approval(review_id, "wrong_hash")
        self.assertIn("error", result)


class TestMidnightPurge(unittest.TestCase):
    """Test the Midnight Purge."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.purge = MidnightPurge(self.tmpdir)

    def test_execute_purge(self):
        # Create a temp file
        workspace = Path(self.tmpdir) / "workspace"
        workspace.mkdir()
        cache_dir = workspace / "tmp" / "cache"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "cache.txt"
        cache_file.write_text("cached data")
        # Make it old
        import os
        old_time = time.time() - 86400 * 2  # 2 days ago
        os.utime(cache_file, (old_time, old_time))
        # Purge
        record = self.purge.execute(workspace)
        self.assertGreaterEqual(record.items_removed, 1)

    def test_protected_preserved(self):
        # Create a protected file
        workspace = Path(self.tmpdir) / "workspace"
        workspace.mkdir()
        evidence_dir = workspace / "evidence"
        evidence_dir.mkdir()
        ledger = evidence_dir / "ledger.jsonl"
        ledger.write_text("{}")
        # Make it old
        import os
        old_time = time.time() - 86400 * 365
        os.utime(ledger, (old_time, old_time))
        # Purge
        record = self.purge.execute(workspace)
        self.assertGreaterEqual(record.protected_preserved, 1)


class TestPackageManager(unittest.TestCase):
    """Test the package manager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.pm = PackageManager(self.tmpdir)

    def test_install(self):
        result = self.pm.install("sios-core", "1.0.0", "SIOS Core", "hash123")
        self.assertEqual(result["status"], "installed")

    def test_update(self):
        self.pm.install("sios-core", "1.0.0", "SIOS Core")
        pkg = self.pm.packages()[0]
        result = self.pm.update(pkg.package_id, "1.1.0")
        self.assertEqual(result["new_version"], "1.1.0")

    def test_rollback(self):
        self.pm.install("sios-core", "1.0.0", "SIOS Core")
        pkg = self.pm.packages()[0]
        self.pm.update(pkg.package_id, "1.1.0")
        result = self.pm.rollback(pkg.package_id, "1.0.0")
        self.assertEqual(result["rolled_back_to"], "1.0.0")

    def test_verify(self):
        self.pm.install("sios-core", "1.0.0", source_hash="abc123")
        pkg = self.pm.packages()[0]
        result = self.pm.verify(pkg.package_id, "abc123")
        self.assertTrue(result["verified"])
        result = self.pm.verify(pkg.package_id, "wrong")
        self.assertFalse(result["verified"])


class TestFinancialLedger(unittest.TestCase):
    """Test the financial ledger."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ledger = FinancialLedger(self.tmpdir)

    def test_add_entry(self):
        entry = FinancialEntry(
            entry_id="e1", entry_type="income",
            amount=1000, payee="Salary",
        )
        eid = self.ledger.add_entry(entry)
        self.assertEqual(eid, "e1")

    def test_balance(self):
        self.ledger.add_entry(FinancialEntry(
            entry_id="e1", entry_type="income", amount=1000,
        ))
        self.ledger.add_entry(FinancialEntry(
            entry_id="e2", entry_type="expense", amount=300,
        ))
        self.assertEqual(self.ledger.balance(), 700)

    def test_reconcile(self):
        self.ledger.add_entry(FinancialEntry(
            entry_id="e1", entry_type="expense", amount=100,
        ))
        self.assertTrue(self.ledger.reconcile("e1", "bank_statement_001"))
        entries = self.ledger.entries()
        self.assertTrue(entries[0].reconciled)

    def test_correction(self):
        self.ledger.add_entry(FinancialEntry(
            entry_id="e1", entry_type="expense", amount=100,
        ))
        self.assertTrue(self.ledger.correct_entry("e1", 150, "wrong amount"))
        entries = self.ledger.entries()
        self.assertEqual(entries[0].amount, 150)
        # Should have a correction entry
        corrections = [e for e in entries if e.entry_type == "correction"]
        self.assertEqual(len(corrections), 1)


if __name__ == "__main__":
    import time
    unittest.main()
