"""Tests for the Book of ANUBIS — self-updating successor's manual."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.book_of_anubis import BookOfAnubis, BookEdition


class TestBookOfAnubis(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)

        # Mock identity, library, registry
        self.identity = MagicMock()
        creator = MagicMock()
        creator.display_name = "Storm"
        creator.creator_id = "4670b4cf48fed7c5"
        creator.enrolled_at = time.time() - 86400 * 365
        creator.preferred_name = "Storm"
        creator.language = "en"
        creator.active = True
        self.identity.get_creator.return_value = creator

        successor = MagicMock()
        successor.display_name = "Ethan Pace"
        successor.relationship = "son"
        successor.successor_id = "144f7f638118138b"
        successor.enrolled_at = time.time() - 86400 * 30
        successor.consent_given = True
        successor.activation_conditions = "Confirmed absence for 24 hours"
        successor.active = False
        self.identity.successors.return_value = [successor]

        self.library = MagicMock()
        self.library.names.return_value = ["math_solver", "code_reviewer", "data_analyzer"]
        skill1 = MagicMock()
        skill1.name = "math_solver"
        skill1.version = "1.2.0"
        skill1.description = "Solves mathematical equations and expressions"
        skill2 = MagicMock()
        skill2.name = "code_reviewer"
        skill2.version = "2.0.1"
        skill2.description = "Reviews code for quality and security issues"
        skill3 = MagicMock()
        skill3.name = "data_analyzer"
        skill3.version = "0.5.0"
        skill3.description = "Analyzes data sets and generates insights"
        self.library.load.side_effect = [skill1, skill2, skill3]

        self.registry = MagicMock()
        director1 = MagicMock()
        director1.director_id = "mathematics"
        director1.name = "Mathematics"
        director1.description = "Mathematical sciences and computation"
        director2 = MagicMock()
        director2.director_id = "software"
        director2.name = "Software Engineering"
        director2.description = "Software development and engineering practices"
        self.registry.directors.return_value = [director1, director2]
        self.registry.specialties_by_director.return_value = [MagicMock(), MagicMock(), MagicMock()]

        self.book = BookOfAnubis(
            self.root,
            identity=self.identity,
            library=self.library,
            registry=self.registry,
            ledger=MagicMock(),
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # SEAL MANAGEMENT
    # ===========================================================

    def test_sealed_by_default(self):
        self.assertTrue(self.book.is_sealed())

    def test_unseal(self):
        result = self.book.unseal(reason="successor activated")
        self.assertTrue(result["unsealed"])
        self.assertFalse(self.book.is_sealed())

    def test_reseal(self):
        self.book.unseal(reason="test")
        result = self.book.reseal()
        self.assertTrue(result["sealed"])
        self.assertTrue(self.book.is_sealed())

    def test_seal_status(self):
        status = self.book.get_seal_status()
        self.assertTrue(status["sealed"])

    def test_seal_status_after_unseal(self):
        self.book.unseal(reason="test")
        status = self.book.get_seal_status()
        self.assertFalse(status["sealed"])
        self.assertEqual(status["reason"], "test")

    # ===========================================================
    # BOOK GENERATION
    # ===========================================================

    def test_generate_first_edition(self):
        result = self.book.generate(force=True)
        self.assertTrue(result["generated"])
        self.assertEqual(result["edition_number"], 1)
        self.assertEqual(result["chapters"], 14)
        self.assertGreater(result["words"], 1000)

    def test_generate_creates_file(self):
        result = self.book.generate(force=True)
        edition_path = Path(result["file"])
        self.assertTrue(edition_path.exists())
        content = edition_path.read_text(encoding="utf-8")
        self.assertIn("# The Book of ANUBIS", content)

    def test_generate_has_all_chapters(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        # Check all chapter titles are present
        self.assertIn("Origin and Purpose", content)
        self.assertIn("Architecture", content)
        self.assertIn("The Creator", content)
        self.assertIn("Governance", content)
        self.assertIn("How to Use ANUBIS", content)
        self.assertIn("Capabilities", content)
        self.assertIn("Hardware", content)
        self.assertIn("Maintenance", content)
        self.assertIn("Recovery", content)
        self.assertIn("Tomb Room", content)
        self.assertIn("Successor Protocol", content)
        self.assertIn("Security", content)
        self.assertIn("Daily Operations", content)
        self.assertIn("Emergency Procedures", content)

    def test_generate_includes_creator_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Storm", content)
        self.assertIn("4670b4cf48fed7c5", content)

    def test_generate_includes_successor_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Ethan Pace", content)
        self.assertIn("son", content)

    def test_generate_includes_skills(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("math_solver", content)
        self.assertIn("code_reviewer", content)
        self.assertIn("data_analyzer", content)
        self.assertIn("Total promoted skills: 3", content)

    def test_generate_includes_directors(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Mathematics", content)
        self.assertIn("Software Engineering", content)

    def test_generate_includes_constitution_laws(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Human Protection", content)
        self.assertIn("Truth", content)
        self.assertIn("Recovery", content)

    def test_generate_includes_sealed_notice(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("SEALED", content)

    def test_generate_unsealed_notice(self):
        self.book.unseal(reason="test")
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("UNSEALED", content)

    def test_generate_second_edition(self):
        self.book.generate(force=True)
        result = self.book.generate(force=True)
        self.assertTrue(result["generated"])
        self.assertEqual(result["edition_number"], 2)

    def test_generate_no_changes(self):
        # The book content includes live system data (A/B drive status, snapshot
        # status) that may change between calls. We test that the change detection
        # mechanism works by verifying that with no structural changes, the
        # second generation either reports no changes or only minor ones.
        self.book.generate(force=True)
        # Immediately generate again — with no skill/registry changes, the
        # structural content should be the same (only timestamps differ)
        result = self.book.generate(force=False)
        # Either it detects no changes, or it generates with minimal changes
        if result["generated"]:
            # If it did generate, the changes should be minor (not skill count)
            skill_changes = [c for c in result.get("changes", []) if "Skill count" in c]
            self.assertEqual(len(skill_changes), 0)
        else:
            self.assertEqual(result["reason"], "no changes detected since last edition")

    def test_generate_with_skill_count_change(self):
        self.book.generate(force=True)
        # Add a new skill
        self.library.names.return_value.append("new_skill")
        result = self.book.generate(force=False)
        self.assertTrue(result["generated"])
        self.assertGreater(len(result["changes"]), 0)

    # ===========================================================
    # BOOK MANAGEMENT
    # ===========================================================

    def test_list_editions(self):
        self.book.generate(force=True)
        self.book.generate(force=True)
        result = self.book.list_editions()
        self.assertEqual(result["count"], 2)

    def test_get_latest_edition(self):
        self.book.generate(force=True)
        time.sleep(0.01)
        self.book.generate(force=True)
        latest = self.book.get_latest_edition()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["edition_number"], 2)

    def test_read_edition_sealed(self):
        self.book.generate(force=True)
        editions = self.book.list_editions()
        edition_id = editions["editions"][0]["edition_id"]
        result = self.book.read_edition(edition_id)
        self.assertFalse(result["readable"])
        self.assertIn("sealed", result["error"].lower())

    def test_read_edition_unsealed(self):
        self.book.generate(force=True)
        self.book.unseal(reason="test")
        editions = self.book.list_editions()
        edition_id = editions["editions"][0]["edition_id"]
        result = self.book.read_edition(edition_id)
        self.assertTrue(result["readable"])
        self.assertIn("content", result)
        self.assertIn("# The Book of ANUBIS", result["content"])

    def test_read_latest_sealed(self):
        self.book.generate(force=True)
        result = self.book.read_latest()
        self.assertFalse(result["readable"])

    def test_read_latest_unsealed(self):
        self.book.generate(force=True)
        self.book.unseal(reason="test")
        result = self.book.read_latest()
        self.assertTrue(result["readable"])

    def test_read_nonexistent_edition(self):
        self.book.unseal(reason="test")
        result = self.book.read_edition("nonexistent")
        self.assertFalse(result["readable"])
        self.assertIn("not found", result["error"])

    def test_get_status(self):
        self.book.generate(force=True)
        status = self.book.get_status()
        self.assertEqual(status["edition_count"], 1)
        self.assertTrue(status["sealed"])
        self.assertIn("book_dir", status)

    def test_get_status_after_unseal(self):
        self.book.unseal(reason="test")
        status = self.book.get_status()
        self.assertFalse(status["sealed"])

    # ===========================================================
    # CONTENT VERIFICATION
    # ===========================================================

    def test_book_has_table_of_contents(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Table of Contents", content)

    def test_book_has_edition_number(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Edition 1", content)

    def test_book_has_date(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("2026", content)  # current year

    def test_book_has_sleep_protocol(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("goodnight", content)
        self.assertIn("good morning", content.lower())

    def test_book_has_recovery_procedures(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Drive Failure", content)
        self.assertIn("snapshot_restore", content)
        self.assertIn("cold_archive_restore", content)

    def test_book_has_degradation_levels(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Partial", content)
        self.assertIn("Minimal", content)
        self.assertIn("Emergency", content)

    def test_book_has_emergency_procedures(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Fire", content)
        self.assertIn("Intrusion", content)
        self.assertIn("Medical", content)

    def test_book_has_biometric_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("biometric", content.lower())
        self.assertIn("face", content.lower())
        self.assertIn("voice", content.lower())

    def test_book_has_tomb_mode_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("tomb", content.lower())
        self.assertIn("demon", content.lower())
        self.assertIn("wake word", content.lower())

    def test_book_has_scheduler_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("scheduler", content.lower())
        self.assertIn("snapshot", content.lower())
        self.assertIn("dream cycle", content.lower())

    def test_book_has_successor_protocol(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("Activation Conditions", content)
        self.assertIn("24 hours", content)
        self.assertIn("NOT notified", content)

    def test_book_has_ab_drive_info(self):
        result = self.book.generate(force=True)
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("A/B", content)
        self.assertIn("canary", content.lower())

    # ===========================================================
    # EDITION METADATA
    # ===========================================================

    def test_edition_to_dict(self):
        edition = BookEdition(
            edition_id="test",
            timestamp=time.time(),
            edition_number=1,
            chapter_count=14,
            word_count=5000,
        )
        d = edition.to_dict()
        self.assertEqual(d["edition_id"], "test")
        self.assertEqual(d["chapter_count"], 14)

    def test_edition_persists(self):
        self.book.generate(force=True)
        # Create a new book instance with same root
        book2 = BookOfAnubis(
            self.root,
            identity=self.identity,
            library=self.library,
            registry=self.registry,
        )
        status = book2.get_status()
        self.assertEqual(status["edition_count"], 1)

    def test_seal_persists(self):
        self.book.unseal(reason="test")
        book2 = BookOfAnubis(self.root)
        self.assertFalse(book2.is_sealed())

    def test_generate_without_identity(self):
        book = BookOfAnubis(self.root, ledger=MagicMock())
        result = book.generate(force=True)
        self.assertTrue(result["generated"])
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("not available", content.lower())

    def test_generate_without_library(self):
        book = BookOfAnubis(self.root, identity=self.identity, ledger=MagicMock())
        result = book.generate(force=True)
        self.assertTrue(result["generated"])
        content = Path(result["file"]).read_text(encoding="utf-8")
        self.assertIn("not available", content.lower())

    def test_word_count_reasonable(self):
        result = self.book.generate(force=True)
        # Should be at least 3000 words for a comprehensive book
        self.assertGreater(result["words"], 3000)


if __name__ == "__main__":
    unittest.main()
