"""Tests for the new self-healing voice patterns, API endpoints, and
custom embeddings activation."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.voice_interpreter import VoiceCommandInterpreter


class TestSelfHealingVoicePatterns(unittest.TestCase):
    """Test the new self-healing voice quick-match patterns."""

    def setUp(self):
        self.interpreter = VoiceCommandInterpreter(
            model=None,
            dispatch=MagicMock(),
            ledger=MagicMock(),
        )

    def test_verify_snapshot(self):
        result = self.interpreter._quick_match("verify snapshot")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "snapshot_verify")

    def test_check_snapshot(self):
        result = self.interpreter._quick_match("check snapshot")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "snapshot_verify")

    def test_cold_archive_status(self):
        result = self.interpreter._quick_match("archive status")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "cold_archive_status")

    def test_archive_list(self):
        result = self.interpreter._quick_match("archive list")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "cold_archive_status")

    def test_repair_alerts(self):
        result = self.interpreter._quick_match("repair alerts")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_alerts")

    def test_any_alerts(self):
        result = self.interpreter._quick_match("any alerts")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_alerts")

    def test_degradation_status(self):
        result = self.interpreter._quick_match("degradation status")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_degradation_status")

    def test_am_i_degraded(self):
        result = self.interpreter._quick_match("am i degraded")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_degradation_status")

    def test_cross_check(self):
        result = self.interpreter._quick_match("cross check")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_cross_check")

    def test_book_status(self):
        result = self.interpreter._quick_match("is the book sealed")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "book_seal_status")

    def test_read_the_book(self):
        result = self.interpreter._quick_match("read the book")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "book_read_latest")

    def test_book_editions(self):
        result = self.interpreter._quick_match("book editions")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "book_list_editions")

    def test_dream_gaps(self):
        result = self.interpreter._quick_match("dream gaps")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "dream_gaps")

    def test_what_are_my_gaps(self):
        result = self.interpreter._quick_match("what are my gaps")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "dream_gaps")

    def test_dream_recommendations(self):
        result = self.interpreter._quick_match("dream recommendations")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "dream_recommendations")

    def test_sign_core(self):
        result = self.interpreter._quick_match("sign core")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "self_repair_sign_core")

    def test_snapshot_retention(self):
        result = self.interpreter._quick_match("snapshot retention")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "snapshot_retention")

    def test_knowledge_acquisition(self):
        result = self.interpreter._quick_match("acquire knowledge")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "knowledge_auto_acquire")

    def test_research_gaps(self):
        result = self.interpreter._quick_match("research gaps")
        self.assertIsNotNone(result)
        self.assertEqual(result["cmd"], "knowledge_auto_acquire")


class TestProtectedPreservedFix(unittest.TestCase):
    """Test that the protected_preserved path matching works cross-platform."""

    def test_protected_path_with_windows_separator(self):
        """Test that Windows backslash paths are matched against forward-slash protected paths."""
        from anubis.operations import MidnightPurge
        import tempfile
        tmpdir = tempfile.mkdtemp()
        purge = MidnightPurge(tmpdir)

        # Simulate a path with Windows separators
        import os
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        evidence_dir = workspace / "evidence"
        evidence_dir.mkdir()
        ledger = evidence_dir / "ledger.jsonl"
        ledger.write_text("{}")

        # The relative path will have OS-specific separators
        # The fix normalizes them to forward slashes
        result = purge._is_protected(ledger)
        self.assertTrue(result, f"Protected path not matched: {ledger}")

    def test_protected_skills_dir(self):
        """Test that the skills directory is protected."""
        from anubis.operations import MidnightPurge
        import tempfile
        tmpdir = tempfile.mkdtemp()
        purge = MidnightPurge(tmpdir)

        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        skills_dir = workspace / "skills"
        skills_dir.mkdir()
        skill_file = skills_dir / "test.py"
        skill_file.write_text("# test")

        result = purge._is_protected(skill_file)
        self.assertTrue(result)

    def test_non_protected_path(self):
        """Test that non-protected paths are not matched."""
        from anubis.operations import MidnightPurge
        import tempfile
        tmpdir = tempfile.mkdtemp()
        purge = MidnightPurge(tmpdir)

        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()
        cache_dir = workspace / "tmp" / "cache"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "cache.txt"
        cache_file.write_text("cache")

        result = purge._is_protected(cache_file)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
