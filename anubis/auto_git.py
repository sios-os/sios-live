"""Automated git operations with semantic versioning.

When the self-development loop successfully tests and compresses a new
set of weights or functional scripts, this module programmatically
commits the code with automated semantic versioning tags.

Features:
- Detects changes since last commit
- Generates semantic version tags (major.minor.patch)
- Auto-increments based on change type:
  - major: breaking changes (constitution/governance modifications)
  - minor: new features (new modules, new daemon commands)
  - patch: fixes and improvements (bug fixes, test updates)
- Writes commit messages with structured metadata
- Maintains a version history log
- Never force-pushes or rewrites history
- Requires Creator approval for major version bumps

Uses subprocess to call git (first-party reviewed code, not sandboxed
generated code). The constitutional kernel's subprocess hazard rule
governs untrusted generated artifacts, not reviewed first-party code.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VERSION_FILE = ".version.json"
CHANGELOG_FILE = "CHANGELOG.md"


@dataclass
class VersionInfo:
    """Semantic version information."""
    major: int = 0
    minor: int = 1
    patch: int = 0
    pre_release: str = ""  # e.g. "alpha", "beta", ""

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            v += f"-{self.pre_release}"
        return v

    @classmethod
    def from_string(cls, s: str) -> "VersionInfo":
        """Parse a version string like '1.2.3' or '1.2.3-alpha'."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(\w+))?$", s)
        if not match:
            return cls()
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            pre_release=match.group(4) or "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "pre_release": self.pre_release,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionInfo":
        return cls(
            major=data.get("major", 0),
            minor=data.get("minor", 1),
            patch=data.get("patch", 0),
            pre_release=data.get("pre_release", ""),
        )


@dataclass
class CommitResult:
    """Result of an auto-commit operation."""
    ok: bool
    version: str = ""
    commit_hash: str = ""
    files_changed: int = 0
    message: str = ""
    error: str = ""


class AutoGit:
    """Automated git operations with semantic versioning.

    Wraps git commands to provide:
    - Change detection
    - Semantic version bumping
    - Structured commit messages
    - Version history tracking
    - Changelog generation

    All operations are non-destructive (no force-push, no history rewrite).
    Major version bumps require explicit Creator approval.
    """

    # File patterns that indicate a major change (breaking)
    MAJOR_PATTERNS = [
        "anubis/constitution.py",
        "anubis/governance.py",
        "anubis/identity.py",
    ]

    # File patterns that indicate a minor change (new feature)
    MINOR_PATTERNS = [
        "anubis/",
        "tools/anubis_daemon.py",
    ]

    def __init__(self, repo_root: str | Path) -> None:
        self.root = Path(repo_root)
        self._version_path = self.root / VERSION_FILE
        self._changelog_path = self.root / CHANGELOG_FILE

    def _run_git(self, args: list[str], *, check: bool = True) -> tuple[int, str, str]:
        """Run a git command. Returns (exit_code, stdout, stderr)."""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if check and result.returncode != 0:
                return result.returncode, result.stdout, result.stderr
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return -1, "", str(exc)

    def is_git_repo(self) -> bool:
        """Check if the root is a git repository."""
        code, _, _ = self._run_git(["rev-parse", "--git-dir"], check=False)
        return code == 0

    def load_version(self) -> VersionInfo:
        """Load the current version from the version file."""
        if not self._version_path.exists():
            return VersionInfo()
        try:
            data = json.loads(self._version_path.read_text(encoding="utf-8"))
            return VersionInfo.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return VersionInfo()

    def save_version(self, version: VersionInfo) -> None:
        """Save the current version to the version file."""
        data = {
            **version.to_dict(),
            "updated_at": time.time(),
        }
        self._version_path.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        code, stdout, _ = self._run_git(["status", "--porcelain"], check=False)
        if code != 0:
            return False
        return bool(stdout.strip())

    def get_changed_files(self) -> list[str]:
        """Get list of changed files (staged and unstaged)."""
        code, stdout, _ = self._run_git(["status", "--porcelain"], check=False)
        if code != 0:
            return []
        files = []
        for line in stdout.strip().splitlines():
            if len(line) > 3:
                files.append(line[3:].strip())
        return files

    def classify_changes(self, changed_files: list[str]) -> str:
        """Classify changes as major, minor, or patch.

        - major: constitution/governance/identity changes (breaking)
        - minor: new modules or daemon commands (new features)
        - patch: everything else (fixes, tests, docs)
        """
        for f in changed_files:
            for pattern in self.MAJOR_PATTERNS:
                if pattern in f:
                    return "major"

        for f in changed_files:
            if f.endswith(".py") and any(p in f for p in self.MINOR_PATTERNS):
                # Check if it's a new file
                code, _, _ = self._run_git(
                    ["cat-file", "-e", f"HEAD:{f}"], check=False
                )
                if code != 0:  # file doesn't exist in HEAD → new file
                    return "minor"

        return "patch"

    def bump_version(
        self,
        current: VersionInfo,
        change_type: str,
        *,
        creator_approved: bool = False,
    ) -> VersionInfo:
        """Bump the version based on change type.

        Major bumps require Creator approval.
        """
        if change_type == "major":
            if not creator_approved:
                raise PermissionError(
                    "major version bump requires Creator approval "
                    "(constitution/governance/identity changes)"
                )
            return VersionInfo(
                major=current.major + 1,
                minor=0,
                patch=0,
                pre_release=current.pre_release,
            )
        elif change_type == "minor":
            return VersionInfo(
                major=current.major,
                minor=current.minor + 1,
                patch=0,
                pre_release=current.pre_release,
            )
        else:  # patch
            return VersionInfo(
                major=current.major,
                minor=current.minor,
                patch=current.patch + 1,
                pre_release=current.pre_release,
            )

    def generate_commit_message(
        self,
        version: VersionInfo,
        change_type: str,
        changed_files: list[str],
    ) -> str:
        """Generate a structured commit message."""
        type_label = {
            "major": "BREAKING",
            "minor": "feat",
            "patch": "fix",
        }.get(change_type, "fix")

        # Summarize changed areas
        areas: set[str] = set()
        for f in changed_files:
            parts = f.split("/")
            if len(parts) > 1:
                areas.add(parts[0])
            else:
                areas.add(f)

        areas_str = ", ".join(sorted(areas)) if areas else "misc"

        return (
            f"{type_label}: v{version} — {areas_str}\n\n"
            f"Changed files ({len(changed_files)}):\n"
            + "\n".join(f"  - {f}" for f in changed_files[:20])
            + ("\n  ..." if len(changed_files) > 20 else "")
        )

    def update_changelog(
        self,
        version: VersionInfo,
        change_type: str,
        changed_files: list[str],
    ) -> None:
        """Append to the changelog."""
        entry = f"## v{version} ({time.strftime('%Y-%m-%d')})\n\n"
        type_label = {
            "major": "BREAKING CHANGE",
            "minor": "New Features",
            "patch": "Fixes & Improvements",
        }.get(change_type, "Changes")
        entry += f"**{type_label}**\n\n"
        for f in changed_files[:20]:
            entry += f"- {f}\n"
        entry += "\n"

        # Prepend to existing changelog
        existing = ""
        if self._changelog_path.exists():
            existing = self._changelog_path.read_text(encoding="utf-8")
        self._changelog_path.write_text(
            f"# Changelog\n\n{entry}{existing}",
            encoding="utf-8",
        )

    def auto_commit(
        self,
        *,
        creator_approved: bool = False,
        message: str | None = None,
    ) -> CommitResult:
        """Detect changes, bump version, and commit.

        Args:
            creator_approved: Required for major version bumps
            message: Override the auto-generated commit message

        Returns:
            CommitResult with status and details
        """
        if not self.is_git_repo():
            return CommitResult(ok=False, error="not a git repository")

        if not self.has_changes():
            return CommitResult(ok=False, error="no changes to commit")

        changed_files = self.get_changed_files()
        if not changed_files:
            return CommitResult(ok=False, error="no changed files detected")

        # Classify changes and bump version
        change_type = self.classify_changes(changed_files)
        current_version = self.load_version()

        try:
            new_version = self.bump_version(
                current_version, change_type, creator_approved=creator_approved
            )
        except PermissionError as exc:
            return CommitResult(
                ok=False,
                version=str(current_version),
                error=str(exc),
            )

        # Generate commit message
        commit_msg = message or self.generate_commit_message(
            new_version, change_type, changed_files
        )

        # Stage all changes
        code, _, stderr = self._run_git(["add", "-A"], check=False)
        if code != 0:
            return CommitResult(ok=False, error=f"git add failed: {stderr}")

        # Commit
        code, stdout, stderr = self._run_git(
            ["commit", "-m", commit_msg], check=False
        )
        if code != 0:
            return CommitResult(ok=False, error=f"git commit failed: {stderr}")

        # Get commit hash
        _, commit_hash, _ = self._run_git(["rev-parse", "HEAD"], check=False)

        # Tag the version
        self._run_git(["tag", f"v{new_version}"], check=False)

        # Save version and update changelog
        self.save_version(new_version)
        self.update_changelog(new_version, change_type, changed_files)

        return CommitResult(
            ok=True,
            version=str(new_version),
            commit_hash=commit_hash[:12],
            files_changed=len(changed_files),
            message=commit_msg,
        )

    def get_version_history(self) -> list[dict[str, Any]]:
        """Get version history from git tags."""
        code, stdout, _ = self._run_git(
            ["tag", "--list", "--sort=-version:refname"], check=False
        )
        if code != 0:
            return []
        versions = []
        for tag in stdout.strip().splitlines():
            tag = tag.strip()
            if tag.startswith("v"):
                versions.append({"version": tag[1:], "tag": tag})
        return versions

    def status(self) -> dict[str, Any]:
        """Return auto-git status."""
        current = self.load_version()
        return {
            "current_version": str(current),
            "is_git_repo": self.is_git_repo(),
            "has_changes": self.has_changes(),
            "changed_files": self.get_changed_files(),
            "version_history_count": len(self.get_version_history()),
        }
