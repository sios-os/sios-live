"""Tests for the funding executor module."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.funding_executor import (
    FundingExecutor, FundingApplication,
    STAGE_DRAFTING, STAGE_REVIEW, STAGE_APPROVED, STAGE_SUBMITTING,
    STAGE_SUBMITTED, STAGE_REJECTED, STAGE_FAILED,
)
from anubis.prospects import Prospect, ProspectsStore, ProspectsSystem


class TestFundingExecutor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)

        # Create a prospects system with an approved prospect
        self.prospects_store = ProspectsStore(self.root / "prospects" / "prospects.json")
        self.prospect = Prospect(
            id="prospect_test1",
            source="grants.gov",
            title="AI Research Grant",
            description="Grant for AI research",
            opportunity_type="grant",
            eligibility="Open",
            estimated_effort_hours=100,
            estimated_cost=500,
            estimated_return=50000,
            deadline="2026-12-31",
            feasibility_score=0.8,
            confidence_score=0.7,
            status="approved",
        )
        self.prospects_store.add(self.prospect)
        self.prospects = ProspectsSystem(store=self.prospects_store)

        # Mock email system
        self.email = MagicMock()
        self.email.send_email.return_value = {"success": True}

        # Mock cloud model
        self.cloud_model = MagicMock()
        self.cloud_model.chat.return_value = MagicMock(text="Generated application content")

        self.executor = FundingExecutor(
            self.root,
            prospects=self.prospects,
            email_system=self.email,
            cloud_model=self.cloud_model,
            ledger=MagicMock(),
            on_speak=MagicMock(),
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # GENERATE APPLICATION
    # ===========================================================

    def test_generate_application_success(self):
        result = self.executor.generate_application("prospect_test1")
        self.assertTrue(result["ok"])
        self.assertIn("application_id", result)
        self.assertEqual(result["stage"], STAGE_REVIEW)
        self.assertIn("document_path", result)

    def test_generate_application_prospect_not_found(self):
        result = self.executor.generate_application("nonexistent")
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])

    def test_generate_application_not_approved(self):
        # Create a pending prospect
        p = Prospect(id="prospect_pending", source="grants.gov", title="Test", status="pending")
        self.prospects_store.add(p)
        result = self.executor.generate_application("prospect_pending")
        self.assertFalse(result["ok"])
        self.assertIn("approved", result["error"])

    def test_generate_application_no_prospects(self):
        executor = FundingExecutor(self.root, prospects=None)
        result = executor.generate_application("prospect_test1")
        self.assertFalse(result["ok"])

    def test_generate_application_uses_cloud_model(self):
        result = self.executor.generate_application("prospect_test1")
        self.assertTrue(result["ok"])
        self.cloud_model.chat.assert_called()

    def test_generate_application_fallback_template(self):
        # Remove cloud model so it falls back to template
        self.executor.cloud_model = None
        result = self.executor.generate_application("prospect_test1")
        self.assertTrue(result["ok"])
        # Check document was generated
        doc = self.executor.get_document(result["application_id"])
        self.assertTrue(doc["ok"])
        self.assertIn("FUNDING APPLICATION", doc["content"])

    def test_generate_application_document_saved(self):
        result = self.executor.generate_application("prospect_test1")
        doc_path = Path(result["document_path"])
        self.assertTrue(doc_path.exists())
        content = doc_path.read_text()
        # Cloud model mock returns "Generated application content"
        self.assertTrue(len(content) > 0)

    # ===========================================================
    # REVIEW AND APPROVE
    # ===========================================================

    def test_get_application(self):
        gen = self.executor.generate_application("prospect_test1")
        app_id = gen["application_id"]
        result = self.executor.get_application(app_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["application"]["id"], app_id)

    def test_get_application_not_found(self):
        result = self.executor.get_application("nonexistent")
        self.assertFalse(result["ok"])

    def test_get_document(self):
        gen = self.executor.generate_application("prospect_test1")
        result = self.executor.get_document(gen["application_id"])
        self.assertTrue(result["ok"])
        self.assertIn("content", result)

    def test_list_applications(self):
        self.executor.generate_application("prospect_test1")
        result = self.executor.list_applications()
        self.assertEqual(result["count"], 1)

    def test_list_applications_by_stage(self):
        self.executor.generate_application("prospect_test1")
        result = self.executor.list_applications(stage=STAGE_REVIEW)
        self.assertEqual(result["count"], 1)
        result = self.executor.list_applications(stage=STAGE_SUBMITTED)
        self.assertEqual(result["count"], 0)

    def test_approve_document(self):
        gen = self.executor.generate_application("prospect_test1")
        result = self.executor.approve_document(gen["application_id"], email_to="test@example.com")
        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], STAGE_APPROVED)

    def test_approve_document_wrong_stage(self):
        gen = self.executor.generate_application("prospect_test1")
        # Approve first
        self.executor.approve_document(gen["application_id"])
        # Try to approve again
        result = self.executor.approve_document(gen["application_id"])
        self.assertFalse(result["ok"])

    def test_reject_document(self):
        gen = self.executor.generate_application("prospect_test1")
        result = self.executor.reject_document(gen["application_id"], reason="Not good enough")
        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], STAGE_REJECTED)

    def test_update_email(self):
        gen = self.executor.generate_application("prospect_test1")
        result = self.executor.update_email(
            gen["application_id"],
            email_to="new@example.com",
            email_subject="New Subject",
        )
        self.assertTrue(result["ok"])

    # ===========================================================
    # SUBMIT
    # ===========================================================

    def test_submit_application_success(self):
        gen = self.executor.generate_application("prospect_test1")
        self.executor.approve_document(gen["application_id"], email_to="grant@example.com")
        result = self.executor.submit_application(
            gen["application_id"], approval_token="creator-approved",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], STAGE_SUBMITTED)

    def test_submit_application_no_approval(self):
        gen = self.executor.generate_application("prospect_test1")
        self.executor.approve_document(gen["application_id"], email_to="grant@example.com")
        result = self.executor.submit_application(
            gen["application_id"], approval_token="",
        )
        self.assertFalse(result["ok"])
        self.assertIn("approval", result["error"])

    def test_submit_application_wrong_stage(self):
        gen = self.executor.generate_application("prospect_test1")
        # Don't approve first
        result = self.executor.submit_application(
            gen["application_id"], approval_token="creator-approved",
        )
        self.assertFalse(result["ok"])

    def test_submit_application_email_failure(self):
        self.email.send_email.return_value = {"success": False, "error": "SMTP error"}
        gen = self.executor.generate_application("prospect_test1")
        self.executor.approve_document(gen["application_id"], email_to="grant@example.com")
        result = self.executor.submit_application(
            gen["application_id"], approval_token="creator-approved",
        )
        self.assertFalse(result["ok"])
        self.assertIn("SMTP", result["error"])

    def test_submit_application_no_email_system(self):
        self.executor.email_system = None
        gen = self.executor.generate_application("prospect_test1")
        self.executor.approve_document(gen["application_id"], email_to="grant@example.com")
        result = self.executor.submit_application(
            gen["application_id"], approval_token="creator-approved",
        )
        self.assertFalse(result["ok"])

    def test_submit_updates_prospect_status(self):
        gen = self.executor.generate_application("prospect_test1")
        self.executor.approve_document(gen["application_id"], email_to="grant@example.com")
        self.executor.submit_application(
            gen["application_id"], approval_token="creator-approved",
        )
        # Check prospect was updated
        p = self.prospects_store.get("prospect_test1")
        self.assertEqual(p.status, "submitted")

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_get_status(self):
        status = self.executor.get_status()
        self.assertTrue(status["prospects_connected"])
        self.assertTrue(status["email_connected"])
        self.assertTrue(status["cloud_model_connected"])
        self.assertEqual(status["total_applications"], 0)

    def test_list_pending_reviews(self):
        self.executor.generate_application("prospect_test1")
        result = self.executor.list_pending_reviews()
        self.assertEqual(result["count"], 1)

    def test_list_pending_submission(self):
        self.executor.generate_application("prospect_test1")
        self.executor.approve_document(
            self.executor.list_pending_reviews()["applications"][0]["id"],
            email_to="test@example.com",
        )
        result = self.executor.list_pending_submission()
        self.assertEqual(result["count"], 1)

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def test_applications_persisted(self):
        self.executor.generate_application("prospect_test1")
        # Create a new executor to test persistence
        executor2 = FundingExecutor(
            self.root,
            prospects=self.prospects,
            email_system=self.email,
        )
        result = executor2.list_applications()
        self.assertEqual(result["count"], 1)

    # ===========================================================
    # DATA STRUCTURES
    # ===========================================================

    def test_funding_application_to_dict(self):
        app = FundingApplication(
            id="test", prospect_id="p1", title="Test",
            document_content="Some content",
        )
        d = app.to_dict()
        self.assertEqual(d["id"], "test")
        self.assertNotIn("document_content", d)  # should be excluded
        self.assertEqual(d["document_content_length"], len("Some content"))

    def test_funding_application_from_dict(self):
        data = {
            "id": "test", "prospect_id": "p1", "title": "Test",
            "stage": STAGE_REVIEW,
        }
        app = FundingApplication.from_dict(data)
        self.assertEqual(app.id, "test")
        self.assertEqual(app.stage, STAGE_REVIEW)


if __name__ == "__main__":
    unittest.main()
