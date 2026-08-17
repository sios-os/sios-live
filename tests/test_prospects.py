"""Tests for the prospects/funding system.

Tests verify:
- Prospect creation and storage
- Prospect evaluation (legitimacy, feasibility, risks)
- Approval/rejection workflow
- Listing and filtering by status
- Statistics
- Evidence ledger logging
- Status endpoint
- Persistence across restarts
"""
import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.prospects import (
    Prospect,
    ProspectsStore,
    ProspectsSystem,
    DEFAULT_SOURCES,
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
)


class TestProspect(unittest.TestCase):
    """Tests for the Prospect dataclass."""

    def test_prospect_creation(self):
        p = Prospect(
            id="test_001",
            source="grants.gov",
            title="AI Research Grant",
            feasibility_score=0.8,
            deadline="2025-12-31",
        )
        self.assertEqual(p.source, "grants.gov")
        self.assertEqual(p.status, STATUS_PENDING)
        self.assertTrue(p.is_actionable)

    def test_prospect_not_actionable_without_title(self):
        p = Prospect(id="test", source="grants.gov", feasibility_score=0.8, deadline="2025-12-31")
        self.assertFalse(p.is_actionable)

    def test_prospect_not_actionable_without_feasibility(self):
        p = Prospect(id="test", source="grants.gov", title="Test", deadline="2025-12-31")
        self.assertFalse(p.is_actionable)

    def test_prospect_not_actionable_without_deadline(self):
        p = Prospect(id="test", source="grants.gov", title="Test", feasibility_score=0.8)
        self.assertFalse(p.is_actionable)

    def test_net_estimate(self):
        p = Prospect(
            id="test", source="grants.gov", title="Test",
            estimated_cost=1000, estimated_return=5000,
        )
        self.assertEqual(p.net_estimate, 4000)

    def test_to_dict_and_from_dict_roundtrip(self):
        p = Prospect(
            id="test_001", source="grants.gov", title="Test Grant",
            description="A test grant", feasibility_score=0.7,
            risks=["low confidence"], evidence=["source page"],
        )
        d = p.to_dict()
        p2 = Prospect.from_dict(d)
        self.assertEqual(p2.id, p.id)
        self.assertEqual(p2.source, p.source)
        self.assertEqual(p2.risks, p.risks)


class TestProspectsStore(unittest.TestCase):
    """Tests for the prospects storage layer."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-prospects-store-")
        self.store = ProspectsStore(Path(self.tmpdir) / "prospects.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_and_get(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test")
        self.store.add(p)
        retrieved = self.store.get("test_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test")

    def test_get_not_found(self):
        self.assertIsNone(self.store.get("nonexistent"))

    def test_update(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test")
        self.store.add(p)
        self.assertTrue(self.store.update("test_001", {"title": "Updated"}))
        self.assertEqual(self.store.get("test_001").title, "Updated")

    def test_update_not_found(self):
        self.assertFalse(self.store.update("nonexistent", {"title": "X"}))

    def test_approve(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test")
        self.store.add(p)
        self.assertTrue(self.store.approve("test_001"))
        self.assertEqual(self.store.get("test_001").status, STATUS_APPROVED)
        self.assertGreater(self.store.get("test_001").approved_at, 0)

    def test_reject(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test")
        self.store.add(p)
        self.assertTrue(self.store.reject("test_001"))
        self.assertEqual(self.store.get("test_001").status, STATUS_REJECTED)

    def test_list_all(self):
        self.store.add(Prospect(id="p1", source="grants.gov", title="A"))
        self.store.add(Prospect(id="p2", source="upwork.com", title="B"))
        self.assertEqual(len(self.store.list_all()), 2)

    def test_list_by_status(self):
        self.store.add(Prospect(id="p1", source="s", title="A", status=STATUS_PENDING))
        self.store.add(Prospect(id="p2", source="s", title="B", status=STATUS_APPROVED))
        self.assertEqual(len(self.store.list_pending()), 1)
        self.assertEqual(len(self.store.list_approved()), 1)

    def test_delete(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test")
        self.store.add(p)
        self.assertTrue(self.store.delete("test_001"))
        self.assertIsNone(self.store.get("test_001"))

    def test_delete_not_found(self):
        self.assertFalse(self.store.delete("nonexistent"))

    def test_persistence(self):
        p = Prospect(id="test_001", source="grants.gov", title="Test", feasibility_score=0.8)
        self.store.add(p)
        # Create a new store pointing to the same file
        store2 = ProspectsStore(Path(self.tmpdir) / "prospects.json")
        retrieved = store2.get("test_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test")
        self.assertEqual(retrieved.feasibility_score, 0.8)

    def test_stats(self):
        self.store.add(Prospect(id="p1", source="s", title="A",
                                status=STATUS_PENDING, feasibility_score=0.8,
                                estimated_return=5000))
        self.store.add(Prospect(id="p2", source="s", title="B",
                                status=STATUS_APPROVED, feasibility_score=0.6,
                                estimated_return=3000))
        stats = self.store.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["approved"], 1)
        self.assertEqual(stats["total_estimated_return"], 8000)
        self.assertAlmostEqual(stats["avg_feasibility"], 0.7)


class TestProspectsSystem(unittest.TestCase):
    """Tests for the prospects system."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-prospects-sys-")
        self.store = ProspectsStore(Path(self.tmpdir) / "prospects.json")
        self.ledger = MagicMock()
        self.system = ProspectsSystem(store=self.store, ledger=self.ledger)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_prospect(self):
        result = self.system.create_prospect(
            source="grants.gov",
            title="AI Research Grant",
            description="Grant for AI research",
            estimated_return=50000,
            deadline="2025-12-31",
            feasibility_score=0.7,
            confidence_score=0.6,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], STATUS_PENDING)
        self.assertIn("prospect_id", result)

    def test_create_prospect_logs_to_ledger(self):
        self.system.create_prospect(source="grants.gov", title="Test")
        self.ledger.append.assert_called_once()
        entry = self.ledger.append.call_args[0][0]
        self.assertEqual(entry["type"], "prospect")
        self.assertEqual(entry["action"], "created")

    def test_evaluate_prospect_legitimate(self):
        result = self.system.create_prospect(
            source="grants.gov", title="Test Grant",
            feasibility_score=0.8, confidence_score=0.7,
            deadline="2025-12-31",
            evidence=["grant page"], citations=["source URL"],
        )
        pid = result["prospect_id"]
        evaluation = self.system.evaluate_prospect(pid)
        self.assertTrue(evaluation["ok"])
        self.assertTrue(evaluation["source_legitimate"])
        self.assertTrue(evaluation["actionable"])
        self.assertEqual(evaluation["recommendation"], "proceed")

    def test_evaluate_prospect_not_whitelisted(self):
        result = self.system.create_prospect(
            source="evil.example.com", title="Test",
            feasibility_score=0.8, deadline="2025-12-31",
            evidence=["x"], citations=["x"],
        )
        pid = result["prospect_id"]
        evaluation = self.system.evaluate_prospect(pid)
        self.assertFalse(evaluation["source_legitimate"])
        self.assertEqual(evaluation["recommendation"], "reject")

    def test_evaluate_prospect_low_feasibility(self):
        result = self.system.create_prospect(
            source="grants.gov", title="Test",
            feasibility_score=0.1, confidence_score=0.7,
            deadline="2025-12-31", evidence=["x"], citations=["x"],
        )
        pid = result["prospect_id"]
        evaluation = self.system.evaluate_prospect(pid)
        self.assertIn("low feasibility score", evaluation["risk_factors"])

    def test_evaluate_prospect_no_evidence(self):
        result = self.system.create_prospect(
            source="grants.gov", title="Test",
            feasibility_score=0.8, confidence_score=0.7,
            deadline="2025-12-31",
        )
        pid = result["prospect_id"]
        evaluation = self.system.evaluate_prospect(pid)
        self.assertIn("no supporting evidence", evaluation["risk_factors"])

    def test_evaluate_prospect_cost_exceeds_return(self):
        result = self.system.create_prospect(
            source="grants.gov", title="Test",
            feasibility_score=0.8, confidence_score=0.7,
            deadline="2025-12-31", evidence=["x"], citations=["x"],
            estimated_cost=10000, estimated_return=5000,
        )
        pid = result["prospect_id"]
        evaluation = self.system.evaluate_prospect(pid)
        self.assertIn("estimated cost exceeds return", evaluation["risk_factors"])

    def test_evaluate_not_found(self):
        result = self.system.evaluate_prospect("nonexistent")
        self.assertFalse(result["ok"])

    def test_approve_prospect(self):
        result = self.system.create_prospect(source="grants.gov", title="Test")
        pid = result["prospect_id"]
        approval = self.system.approve_prospect(pid)
        self.assertTrue(approval["ok"])
        self.assertEqual(approval["status"], STATUS_APPROVED)

    def test_approve_logs_to_ledger(self):
        result = self.system.create_prospect(source="grants.gov", title="Test")
        pid = result["prospect_id"]
        self.system.approve_prospect(pid)
        # Should have been called twice: create + approve
        self.assertEqual(self.ledger.append.call_count, 2)

    def test_reject_prospect(self):
        result = self.system.create_prospect(source="grants.gov", title="Test")
        pid = result["prospect_id"]
        rejection = self.system.reject_prospect(pid)
        self.assertTrue(rejection["ok"])
        self.assertEqual(rejection["status"], STATUS_REJECTED)

    def test_approve_not_found(self):
        result = self.system.approve_prospect("nonexistent")
        self.assertFalse(result["ok"])

    def test_list_pending(self):
        self.system.create_prospect(source="grants.gov", title="A")
        self.system.create_prospect(source="grants.gov", title="B")
        result = self.system.list_pending()
        self.assertEqual(result["count"], 2)

    def test_list_approved(self):
        r1 = self.system.create_prospect(source="grants.gov", title="A")
        self.system.approve_prospect(r1["prospect_id"])
        result = self.system.list_approved()
        self.assertEqual(result["count"], 1)

    def test_stats(self):
        self.system.create_prospect(source="grants.gov", title="A", estimated_return=5000)
        stats = self.system.stats()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["pending"], 1)

    def test_status(self):
        status = self.system.status()
        self.assertIn("store_path", status)
        self.assertIn("default_sources", status)
        self.assertIn("grants.gov", status["default_sources"])
        self.assertFalse(status["gateway_connected"])
        self.assertTrue(status["ledger_connected"])


class TestSearchOpportunities(unittest.TestCase):
    """Tests for the search functionality."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-prospects-search-")
        self.store = ProspectsStore(Path(self.tmpdir) / "prospects.json")
        self.gateway = MagicMock()
        self.system = ProspectsSystem(store=self.store, gateway=self.gateway)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_search_no_gateway(self):
        system = ProspectsSystem(store=self.store)
        result = system.search_opportunities("AI grants")
        self.assertFalse(result["ok"])
        self.assertIn("no gateway", result["error"])

    def test_search_gateway_refused(self):
        from anubis.external_gateway import GatewayResponse
        self.gateway.search.return_value = GatewayResponse(
            ok=False, error="requires Creator approval",
            refused_reason="requires Creator approval",
        )
        result = self.system.search_opportunities("AI grants", creator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("approval", result["error"])

    def test_search_success(self):
        from anubis.external_gateway import GatewayResponse
        self.gateway.search.return_value = GatewayResponse(
            ok=True, status_code=200, body='{"results": ["grant1", "grant2"]}',
        )
        result = self.system.search_opportunities("AI grants", creator_approved=True)
        self.assertTrue(result["ok"])
        self.assertIn("grant1", result["results"])


if __name__ == "__main__":
    unittest.main()
