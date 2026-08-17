"""Tests for the self-modification framework."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.self_modify import (
    SelfModificationFramework,
    ModificationProposal,
    IMMUTABLE_FILES,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = ""):
        self.response = response
        self.model = "mock:test"

    def chat(self, messages, *, temperature=0.2, max_tokens=None, timeout=180.0):
        return Completion(
            text=self.response,
            thinking="",
            tool_calls=[],
            model="mock:test",
            prompt_tokens=10,
            completion_tokens=20,
            duration_s=0.01,
        )


class TestImmutableFiles(unittest.TestCase):
    def test_constitution_immutable(self):
        self.assertIn("anubis/constitution.py", IMMUTABLE_FILES)

    def test_identity_immutable(self):
        self.assertIn("anubis/identity.py", IMMUTABLE_FILES)

    def test_ledger_immutable(self):
        self.assertIn("anubis/ledger.py", IMMUTABLE_FILES)

    def test_self_modify_immutable(self):
        self.assertIn("anubis/self_modify.py", IMMUTABLE_FILES)


class TestModificationProposal(unittest.TestCase):
    def test_to_dict(self):
        p = ModificationProposal(
            proposal_id="p1",
            target_file="anubis/loop.py",
            change_description="test",
            rationale="r",
            current_hash="abc",
            proposed_diff="diff",
        )
        d = p.to_dict()
        self.assertEqual(d["proposal_id"], "p1")
        self.assertEqual(d["status"], "proposed")

    def test_from_dict(self):
        p = ModificationProposal.from_dict({
            "proposal_id": "p2",
            "target_file": "anubis/memory.py",
            "change_description": "d",
            "rationale": "r",
            "current_hash": "h",
            "proposed_diff": "d",
            "status": "approved",
        })
        self.assertEqual(p.proposal_id, "p2")
        self.assertEqual(p.status, "approved")


class TestSelfModificationFramework(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Create a test file to modify
        (self.root / "anubis").mkdir(parents=True, exist_ok=True)
        (self.root / "anubis" / "test_module.py").write_text(
            "def hello():\n    return 'world'\n", encoding="utf-8"
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_modifiable_anubis(self):
        fw = SelfModificationFramework(self.root)
        self.assertTrue(fw._is_modifiable("anubis/loop.py"))
        self.assertTrue(fw._is_modifiable("anubis/test_module.py"))

    def test_is_modifiable_tools(self):
        fw = SelfModificationFramework(self.root)
        self.assertTrue(fw._is_modifiable("tools/anubis_daemon.py"))

    def test_is_not_modifiable_constitution(self):
        fw = SelfModificationFramework(self.root)
        self.assertFalse(fw._is_modifiable("anubis/constitution.py"))

    def test_is_not_modifiable_self_modify(self):
        fw = SelfModificationFramework(self.root)
        self.assertFalse(fw._is_modifiable("anubis/self_modify.py"))

    def test_is_not_modifiable_random(self):
        fw = SelfModificationFramework(self.root)
        self.assertFalse(fw._is_modifiable("random/file.py"))

    def test_propose_modification(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        proposal = fw.propose_modification(
            model, "anubis/test_module.py", "change return value"
        )
        self.assertEqual(proposal.target_file, "anubis/test_module.py")
        self.assertEqual(proposal.status, "proposed")
        self.assertNotEqual(proposal.proposed_diff, "")
        self.assertNotEqual(proposal.current_hash, "")

    def test_propose_immutable_fails(self):
        model = MockModel("test")
        fw = SelfModificationFramework(self.root)
        with self.assertRaises(ValueError):
            fw.propose_modification(
                model, "anubis/constitution.py", "change constitution"
            )

    def test_propose_nonexistent_fails(self):
        model = MockModel("test")
        fw = SelfModificationFramework(self.root)
        with self.assertRaises(FileNotFoundError):
            fw.propose_modification(
                model, "anubis/nonexistent.py", "create new"
            )

    def test_assess_risk_low(self):
        fw = SelfModificationFramework(self.root)
        risk = fw._assess_risk("anubis/test_module.py", "+1 line\n-1 line\n")
        self.assertEqual(risk, "low")

    def test_assess_risk_high_core(self):
        fw = SelfModificationFramework(self.root)
        risk = fw._assess_risk("anubis/loop.py", "+5 lines\n-3 lines\n")
        self.assertEqual(risk, "high")

    def test_assess_risk_critical(self):
        fw = SelfModificationFramework(self.root)
        risk = fw._assess_risk("anubis/governance.py", "+1\n-1\n")
        self.assertEqual(risk, "critical")

    def test_generate_diff(self):
        fw = SelfModificationFramework(self.root)
        diff = fw._generate_diff("line1\nline2\n", "line1\nline3\n", "test.py")
        self.assertIn("test.py", diff)
        self.assertIn("-line2", diff)
        self.assertIn("+line3", diff)

    def test_list_proposals(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        fw.propose_modification(model, "anubis/test_module.py", "test")
        proposals = fw.list_proposals()
        self.assertEqual(len(proposals), 1)

    def test_list_proposals_by_status(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        fw.propose_modification(model, "anubis/test_module.py", "test")
        proposed = fw.list_proposals(status="proposed")
        self.assertEqual(len(proposed), 1)
        approved = fw.list_proposals(status="approved")
        self.assertEqual(len(approved), 0)

    def test_get_proposal(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        proposal = fw.propose_modification(model, "anubis/test_module.py", "test")
        loaded = fw.get_proposal(proposal.proposal_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["proposal_id"], proposal.proposal_id)

    def test_review_proposal_no_court(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        proposal = fw.propose_modification(model, "anubis/test_module.py", "test")
        result = fw.review_proposal(proposal.proposal_id)
        self.assertEqual(result["status"], "court_reviewed")

    def test_status(self):
        fw = SelfModificationFramework(self.root)
        status = fw.get_status()
        self.assertEqual(status["total_proposals"], 0)
        self.assertIn("immutable_files", status)

    def test_apply_diff(self):
        fw = SelfModificationFramework(self.root)
        original = "line1\nline2\nline3\n"
        diff = fw._generate_diff(original, "line1\nchanged\nline3\n", "test.py")
        result = fw._apply_diff(original, diff)
        self.assertIsNotNone(result)
        self.assertIn("changed", result)

    def test_staging(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        proposal = fw.propose_modification(model, "anubis/test_module.py", "test")
        # Review and approve
        fw.review_proposal(proposal.proposal_id)
        result = fw.approve_proposal(proposal.proposal_id, "creator1")
        # Should pass syntax check
        self.assertIn(result.get("status"), ["tested", "rejected"])

    def test_reject_unauthorized_creator(self):
        model = MockModel("def hello():\n    return 'universe'\n")
        fw = SelfModificationFramework(self.root, creator_id="creator1")
        proposal = fw.propose_modification(model, "anubis/test_module.py", "test")
        fw.review_proposal(proposal.proposal_id)
        result = fw.approve_proposal(proposal.proposal_id, "wrong_creator")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
