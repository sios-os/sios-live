"""Tests for the auto-git module.

Tests verify:
- Version parsing and formatting
- Version bumping (major, minor, patch)
- Change classification
- Commit message generation
- Permission check for major bumps
- Version history
- Status endpoint
- Git repo detection

Git operations use a temporary git repo for integration testing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.auto_git import AutoGit, VersionInfo, CommitResult


class TestVersionInfo(unittest.TestCase):
    """Tests for VersionInfo."""

    def test_default_version(self):
        v = VersionInfo()
        self.assertEqual(str(v), "0.1.0")

    def test_custom_version(self):
        v = VersionInfo(1, 2, 3)
        self.assertEqual(str(v), "1.2.3")

    def test_pre_release(self):
        v = VersionInfo(1, 0, 0, "alpha")
        self.assertEqual(str(v), "1.0.0-alpha")

    def test_from_string(self):
        v = VersionInfo.from_string("2.3.4")
        self.assertEqual(v.major, 2)
        self.assertEqual(v.minor, 3)
        self.assertEqual(v.patch, 4)

    def test_from_string_with_pre_release(self):
        v = VersionInfo.from_string("1.0.0-beta")
        self.assertEqual(v.pre_release, "beta")

    def test_from_string_invalid(self):
        v = VersionInfo.from_string("not-a-version")
        self.assertEqual(str(v), "0.1.0")

    def test_to_dict_and_from_dict(self):
        v = VersionInfo(1, 2, 3, "alpha")
        d = v.to_dict()
        v2 = VersionInfo.from_dict(d)
        self.assertEqual(v2.major, 1)
        self.assertEqual(v2.minor, 2)
        self.assertEqual(v2.patch, 3)
        self.assertEqual(v2.pre_release, "alpha")


class TestVersionBumping(unittest.TestCase):
    """Tests for version bumping logic."""

    def test_patch_bump(self):
        git = AutoGit(".")
        v = VersionInfo(1, 2, 3)
        new = git.bump_version(v, "patch")
        self.assertEqual(str(new), "1.2.4")

    def test_minor_bump(self):
        git = AutoGit(".")
        v = VersionInfo(1, 2, 3)
        new = git.bump_version(v, "minor")
        self.assertEqual(str(new), "1.3.0")

    def test_major_bump_with_approval(self):
        git = AutoGit(".")
        v = VersionInfo(1, 2, 3)
        new = git.bump_version(v, "major", creator_approved=True)
        self.assertEqual(str(new), "2.0.0")

    def test_major_bump_without_approval(self):
        git = AutoGit(".")
        v = VersionInfo(1, 2, 3)
        with self.assertRaises(PermissionError):
            git.bump_version(v, "major", creator_approved=False)

    def test_bump_preserves_pre_release(self):
        git = AutoGit(".")
        v = VersionInfo(1, 2, 3, "alpha")
        new = git.bump_version(v, "patch")
        self.assertEqual(new.pre_release, "alpha")


class TestChangeClassification(unittest.TestCase):
    """Tests for change classification."""

    def setUp(self):
        self.git = AutoGit(".")

    def test_major_change_constitution(self):
        self.assertEqual(
            self.git.classify_changes(["anubis/constitution.py"]),
            "major"
        )

    def test_major_change_governance(self):
        self.assertEqual(
            self.git.classify_changes(["anubis/governance.py"]),
            "major"
        )

    def test_major_change_identity(self):
        self.assertEqual(
            self.git.classify_changes(["anubis/identity.py"]),
            "major"
        )

    def test_patch_change_docs(self):
        self.assertEqual(
            self.git.classify_changes(["README.md", "docs/guide.md"]),
            "patch"
        )

    def test_patch_change_tests(self):
        self.assertEqual(
            self.git.classify_changes(["tests/test_foo.py"]),
            "patch"
        )

    def test_major_takes_priority(self):
        self.assertEqual(
            self.git.classify_changes(["README.md", "anubis/constitution.py"]),
            "major"
        )


class TestCommitMessage(unittest.TestCase):
    """Tests for commit message generation."""

    def setUp(self):
        self.git = AutoGit(".")

    def test_patch_message(self):
        msg = self.git.generate_commit_message(
            VersionInfo(1, 2, 3), "patch", ["tests/test_foo.py"]
        )
        self.assertIn("fix", msg)
        self.assertIn("v1.2.3", msg)

    def test_minor_message(self):
        msg = self.git.generate_commit_message(
            VersionInfo(1, 3, 0), "minor", ["anubis/new_module.py"]
        )
        self.assertIn("feat", msg)
        self.assertIn("v1.3.0", msg)

    def test_major_message(self):
        msg = self.git.generate_commit_message(
            VersionInfo(2, 0, 0), "major", ["anubis/constitution.py"]
        )
        self.assertIn("BREAKING", msg)
        self.assertIn("v2.0.0", msg)

    def test_message_lists_files(self):
        files = ["anubis/foo.py", "tests/test_foo.py"]
        msg = self.git.generate_commit_message(VersionInfo(1, 0, 0), "patch", files)
        self.assertIn("anubis/foo.py", msg)
        self.assertIn("tests/test_foo.py", msg)

    def test_message_truncates_long_file_list(self):
        files = [f"file_{i}.py" for i in range(30)]
        msg = self.git.generate_commit_message(VersionInfo(1, 0, 0), "patch", files)
        self.assertIn("...", msg)


class TestVersionPersistence(unittest.TestCase):
    """Tests for version save/load."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-autogit-ver-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        git = AutoGit(self.tmpdir)
        v = VersionInfo(1, 2, 3, "beta")
        git.save_version(v)
        loaded = git.load_version()
        self.assertEqual(str(loaded), "1.2.3-beta")

    def test_load_default(self):
        git = AutoGit(self.tmpdir)
        v = git.load_version()
        self.assertEqual(str(v), "0.1.0")


class TestGitRepoDetection(unittest.TestCase):
    """Tests for git repo detection."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-autogit-repo-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_not_a_git_repo(self):
        git = AutoGit(self.tmpdir)
        self.assertFalse(git.is_git_repo())

    def test_is_a_git_repo(self):
        subprocess.run(["git", "init"], cwd=self.tmpdir, capture_output=True)
        git = AutoGit(self.tmpdir)
        self.assertTrue(git.is_git_repo())


class TestAutoCommit(unittest.TestCase):
    """Integration tests for auto-commit (uses temp git repos)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-autogit-commit-")
        subprocess.run(["git", "init"], cwd=self.tmpdir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=self.tmpdir, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.tmpdir, capture_output=True
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_changes(self):
        git = AutoGit(self.tmpdir)
        result = git.auto_commit()
        self.assertFalse(result.ok)
        self.assertIn("no changes", result.error)

    def test_patch_commit(self):
        # Create a test file and commit
        (Path(self.tmpdir) / "README.md").write_text("test", encoding="utf-8")
        git = AutoGit(self.tmpdir)
        result = git.auto_commit()
        self.assertTrue(result.ok)
        self.assertIn("0.1.1", result.version)

    def test_not_a_git_repo(self):
        tmpdir2 = tempfile.mkdtemp(prefix="anubis-autogit-norepo-")
        try:
            git = AutoGit(tmpdir2)
            result = git.auto_commit()
            self.assertFalse(result.ok)
            self.assertIn("not a git", result.error)
        finally:
            shutil.rmtree(tmpdir2, ignore_errors=True)


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-autogit-status-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_status_not_git_repo(self):
        git = AutoGit(self.tmpdir)
        status = git.status()
        self.assertFalse(status["is_git_repo"])
        self.assertEqual(status["current_version"], "0.1.0")

    def test_status_git_repo(self):
        subprocess.run(["git", "init"], cwd=self.tmpdir, capture_output=True)
        git = AutoGit(self.tmpdir)
        status = git.status()
        self.assertTrue(status["is_git_repo"])
        self.assertFalse(status["has_changes"])


if __name__ == "__main__":
    unittest.main()
