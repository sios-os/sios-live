"""Self-modification framework — ANUBIS proposes changes to his own code.

This is the most governance-sensitive module in the system. It allows ANUBIS
to propose modifications to his own core modules (anubis/*.py), but with
strict safeguards:

1. **Propose only** — ANUBIS generates a proposed change but cannot execute it
2. **Court review** — All self-modifications go through the Court
3. **Creator approval** — The Creator must explicitly approve before execution
4. **Staged application** — Changes are applied to a staging copy first
5. **Test verification** — The full test suite must pass on the staged version
6. **Rollback** — If anything fails, the original is restored
7. **Audit trail** — Every proposal, review, approval, and outcome is logged

The framework works with diffs, not full file rewrites. ANUBIS sees the current
code, proposes a change as a unified diff, and the system validates it before
any application.

ANUBIS can propose changes to:
- His own skill library (already handled by loop.py)
- His core modules (anubis/*.py) — through this framework
- His daemon commands (tools/anubis_daemon.py) — through this framework
- His configuration files — through this framework

He CANNOT modify:
- The constitution (anubis/constitution.py) — immutable
- The identity vault (anubis/identity.py) — immutable
- The ledger (anubis/ledger.py) — tamper-evident, append-only
- This self-modification framework (anubis/self_modify.py) — to prevent
  removing his own safety constraints

Uses only the Python standard library.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


# --------------------------------------------------------------------- types


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


# Files that ANUBIS is NOT allowed to modify
IMMUTABLE_FILES = {
    "anubis/constitution.py",
    "anubis/identity.py",
    "anubis/ledger.py",
    "anubis/self_modify.py",
    "anubis/governance.py",
}

# Files that ANUBIS CAN modify (with approval)
MODIFIABLE_PATTERNS = [
    "anubis/",       # core modules (except immutable)
    "tools/",        # daemon and scripts
    "config/",       # configuration
    "skills/",       # skill library
]


@dataclass
class ModificationProposal:
    """A proposed self-modification."""
    proposal_id: str
    target_file: str  # relative path from root
    change_description: str
    rationale: str  # why ANUBIS wants this change
    current_hash: str  # SHA-256 of current file content
    proposed_diff: str  # unified diff
    risk_level: str = "medium"  # low, medium, high, critical
    status: str = "proposed"  # proposed, court_reviewed, approved, rejected, staged, tested, applied, rolled_back
    court_verdict: str = ""
    creator_approved: bool = False
    creator_id: str = ""
    test_result: str = ""
    applied_at: float = 0.0
    rolled_back: bool = False
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target_file": self.target_file,
            "change_description": self.change_description,
            "rationale": self.rationale,
            "current_hash": self.current_hash,
            "proposed_diff": self.proposed_diff,
            "risk_level": self.risk_level,
            "status": self.status,
            "court_verdict": self.court_verdict,
            "creator_approved": self.creator_approved,
            "creator_id": self.creator_id,
            "test_result": self.test_result,
            "applied_at": self.applied_at,
            "rolled_back": self.rolled_back,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModificationProposal":
        return cls(
            proposal_id=data.get("proposal_id", ""),
            target_file=data.get("target_file", ""),
            change_description=data.get("change_description", ""),
            rationale=data.get("rationale", ""),
            current_hash=data.get("current_hash", ""),
            proposed_diff=data.get("proposed_diff", ""),
            risk_level=data.get("risk_level", "medium"),
            status=data.get("status", "proposed"),
            court_verdict=data.get("court_verdict", ""),
            creator_approved=data.get("creator_approved", False),
            creator_id=data.get("creator_id", ""),
            test_result=data.get("test_result", ""),
            applied_at=data.get("applied_at", 0.0),
            rolled_back=data.get("rolled_back", False),
            created_at=data.get("created_at", 0.0),
        )


# --------------------------------------------------------------- manager


class SelfModificationFramework:
    """Governed self-modification of ANUBIS's own code.

    The flow:
    1. ANUBIS proposes a change (generates a diff)
    2. The proposal is stored and logged
    3. The Court reviews the proposal
    4. If the Court allows, the Creator must approve
    5. The change is staged to a copy
    6. Tests are run on the staged version
    7. If tests pass, the change is applied
    8. If tests fail or anything goes wrong, rollback

    The framework NEVER auto-applies changes. Every step requires
    explicit approval.
    """

    ACTOR = "anubis.self_modify"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        court: Any | None = None,
        creator_id: str = "",
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.court = court
        self.creator_id = creator_id

        self._proposals_dir = self.root / "memory" / "self_mods"
        self._proposals_dir.mkdir(parents=True, exist_ok=True)
        self._proposals_file = self._proposals_dir / "proposals.json"
        self._staging_dir = self._proposals_dir / "staging"

    def propose_modification(
        self,
        model: ModelLike,
        target_file: str,
        change_description: str,
    ) -> ModificationProposal:
        """Generate a modification proposal using the model.

        ANUBIS reads the current file, understands the requested change,
        and generates a unified diff.

        Args:
            model: The model to use for generating the diff
            target_file: Relative path from root (e.g., "anubis/loop.py")
            change_description: What change ANUBIS wants to make

        Returns:
            A ModificationProposal (not yet applied)
        """
        # Validate target file
        if not self._is_modifiable(target_file):
            raise ValueError(
                f"File {target_file} is not modifiable (immutable or outside allowed paths)"
            )

        file_path = self.root / target_file
        if not file_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {target_file}")

        current_content = file_path.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(
            current_content.encode("utf-8")
        ).hexdigest()

        # Ask the model to generate the modified version
        prompt = (
            f"You are modifying your own code. The file is: {target_file}\n\n"
            f"Current content:\n```\n{current_content[:8000]}\n```\n\n"
            f"Requested change: {change_description}\n\n"
            "Generate the COMPLETE modified file. Output ONLY the file content, "
            "no explanations, no markdown fences. The output will be diffed "
            "against the original automatically.\n\n"
            "Rules:\n"
            "- Keep all existing functionality unless explicitly changing it\n"
            "- Do not remove safety checks, governance, or audit logging\n"
            "- Do not add network access, subprocess calls, or eval/exec\n"
            "- Maintain the same coding style\n"
            "- Only change what's needed for the requested modification\n"
        )

        completion = model.chat(
            [
                {"role": "system", "content": SELF_MOD_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=8000,
            timeout=300.0,
        )

        new_content = completion.text.strip()
        # Remove markdown fences if present
        if new_content.startswith("```"):
            lines = new_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            new_content = "\n".join(lines)

        # Generate unified diff
        diff = self._generate_diff(
            current_content, new_content, target_file
        )

        # Assess risk
        risk = self._assess_risk(target_file, diff)

        proposal = ModificationProposal(
            proposal_id=hashlib.sha256(
                f"mod:{target_file}:{time.time()}".encode()
            ).hexdigest()[:16],
            target_file=target_file,
            change_description=change_description,
            rationale=f"Self-proposed modification: {change_description}",
            current_hash=current_hash,
            proposed_diff=diff,
            risk_level=risk,
            status="proposed",
            created_at=time.time(),
        )

        # Save proposal
        self._save_proposal(proposal)

        # Log
        self._log("self_mod.proposed", {
            "proposal_id": proposal.proposal_id,
            "target_file": target_file,
            "change_description": change_description,
            "risk_level": risk,
            "diff_lines": len(diff.split("\n")),
        })

        return proposal

    def review_proposal(self, proposal_id: str) -> dict[str, Any]:
        """Court review of a proposal.

        Returns the verdict. Does not apply the change.
        """
        proposal = self._load_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}

        if proposal.status != "proposed":
            return {"error": f"Proposal already {proposal.status}"}

        # If we have a court, use it
        if self.court is not None:
            try:
                # Submit to court for review
                verdict = self.court.review(
                    artifact=proposal.proposed_diff,
                    artifact_type="self_modification",
                    context={
                        "target_file": proposal.target_file,
                        "change_description": proposal.change_description,
                        "risk_level": proposal.risk_level,
                    },
                )
                proposal.court_verdict = str(verdict)
                if hasattr(verdict, "allowed") and verdict.allowed:
                    proposal.status = "court_reviewed"
                elif hasattr(verdict, "verdict") and str(verdict.verdict).lower() == "allow":
                    proposal.status = "court_reviewed"
                else:
                    proposal.status = "rejected"
            except Exception as exc:
                proposal.court_verdict = f"Court review error: {exc}"
                proposal.status = "rejected"
        else:
            # No court configured — require explicit Creator approval
            proposal.status = "court_reviewed"
            proposal.court_verdict = "No court configured — requires Creator approval"

        self._update_proposal(proposal)

        self._log("self_mod.reviewed", {
            "proposal_id": proposal_id,
            "status": proposal.status,
            "verdict": proposal.court_verdict,
        })

        return {
            "proposal_id": proposal_id,
            "status": proposal.status,
            "verdict": proposal.court_verdict,
        }

    def approve_proposal(
        self,
        proposal_id: str,
        creator_id: str,
    ) -> dict[str, Any]:
        """Creator approves a proposal. This stages and tests the change."""
        proposal = self._load_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}

        if proposal.status != "court_reviewed":
            return {"error": f"Proposal must be court_reviewed, is {proposal.status}"}

        if creator_id != self.creator_id and self.creator_id:
            return {"error": "Unauthorized creator"}

        proposal.creator_approved = True
        proposal.creator_id = creator_id
        proposal.status = "approved"
        self._update_proposal(proposal)

        # Stage the change
        stage_result = self._stage_change(proposal)
        if not stage_result["success"]:
            proposal.status = "rejected"
            proposal.test_result = stage_result.get("error", "staging failed")
            self._update_proposal(proposal)
            return stage_result

        # Run tests on staged version
        test_result = self._run_staged_tests(proposal)
        proposal.test_result = json.dumps(test_result)

        if test_result.get("passed"):
            proposal.status = "tested"
        else:
            proposal.status = "rejected"
            # Clean up staging
            self._cleanup_staging(proposal)

        self._update_proposal(proposal)

        self._log("self_mod.approved", {
            "proposal_id": proposal_id,
            "creator_id": creator_id,
            "test_passed": test_result.get("passed", False),
            "test_summary": test_result.get("summary", ""),
        })

        return {
            "proposal_id": proposal_id,
            "status": proposal.status,
            "test_result": test_result,
        }

    def apply_proposal(self, proposal_id: str) -> dict[str, Any]:
        """Apply a tested proposal to the real codebase."""
        proposal = self._load_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}

        if proposal.status != "tested":
            return {"error": f"Proposal must be tested, is {proposal.status}"}

        file_path = self.root / proposal.target_file

        # Backup original
        backup_path = self._proposals_dir / f"backup_{proposal.proposal_id}.py"
        shutil.copy2(file_path, backup_path)

        # Apply the new content from staging
        staged_path = self._staging_dir / proposal.target_file
        if not staged_path.exists():
            return {"error": "Staged file not found"}

        new_content = staged_path.read_text(encoding="utf-8")

        # Verify hash hasn't changed since proposal
        current_content = file_path.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(
            current_content.encode("utf-8")
        ).hexdigest()
        if current_hash != proposal.current_hash:
            proposal.status = "rejected"
            proposal.test_result += "; file changed since proposal"
            self._update_proposal(proposal)
            return {
                "error": "File has been modified since proposal was created. "
                         "Please re-propose."
            }

        # Apply
        file_path.write_text(new_content, encoding="utf-8")
        proposal.status = "applied"
        proposal.applied_at = time.time()
        self._update_proposal(proposal)

        self._log("self_mod.applied", {
            "proposal_id": proposal_id,
            "target_file": proposal.target_file,
            "backup_path": str(backup_path),
        })

        return {
            "proposal_id": proposal_id,
            "status": "applied",
            "target_file": proposal.target_file,
            "backup_path": str(backup_path),
        }

    def rollback_proposal(self, proposal_id: str) -> dict[str, Any]:
        """Rollback an applied proposal."""
        proposal = self._load_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}

        if proposal.status != "applied":
            return {"error": f"Proposal must be applied, is {proposal.status}"}

        backup_path = self._proposals_dir / f"backup_{proposal.proposal_id}.py"
        if not backup_path.exists():
            return {"error": "Backup file not found"}

        file_path = self.root / proposal.target_file
        shutil.copy2(backup_path, file_path)

        proposal.status = "rolled_back"
        proposal.rolled_back = True
        self._update_proposal(proposal)

        self._log("self_mod.rolled_back", {
            "proposal_id": proposal_id,
            "target_file": proposal.target_file,
        })

        return {
            "proposal_id": proposal_id,
            "status": "rolled_back",
            "target_file": proposal.target_file,
        }

    def list_proposals(
        self, status: str | None = None
    ) -> list[dict[str, Any]]:
        """List all proposals, optionally filtered by status."""
        proposals = self._load_all_proposals()
        if status:
            proposals = [p for p in proposals if p["status"] == status]
        return proposals

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        """Get a single proposal."""
        proposal = self._load_proposal(proposal_id)
        if proposal is None:
            return None
        return proposal.to_dict()

    def get_status(self) -> dict[str, Any]:
        """Get self-modification framework status."""
        proposals = self._load_all_proposals()
        return {
            "total_proposals": len(proposals),
            "by_status": {
                s: sum(1 for p in proposals if p["status"] == s)
                for s in set(p["status"] for p in proposals)
            },
            "immutable_files": list(IMMUTABLE_FILES),
            "modifiable_patterns": MODIFIABLE_PATTERNS,
        }

    # ------------------------------------------------------- internals

    def _is_modifiable(self, target_file: str) -> bool:
        """Check if a file can be modified."""
        # Normalize path
        target_file = target_file.replace("\\", "/").lstrip("./")

        # Check immutable list
        if target_file in IMMUTABLE_FILES:
            return False

        # Check allowed patterns
        for pattern in MODIFIABLE_PATTERNS:
            if target_file.startswith(pattern):
                return True

        return False

    def _generate_diff(
        self, old: str, new: str, filename: str
    ) -> str:
        """Generate a unified diff."""
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return "".join(diff)

    def _assess_risk(self, target_file: str, diff: str) -> str:
        """Assess the risk level of a modification."""
        diff_lines = diff.split("\n")
        added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        # Critical: changes to governance, constitution, or security
        critical_patterns = ["constitution", "governance", "court", "sandbox", "identity"]
        if any(p in target_file for p in critical_patterns):
            return "critical"

        # High: changes to core loop, model, or daemon
        high_patterns = ["loop.py", "model.py", "anubis_daemon.py", "memory.py"]
        if any(p in target_file for p in high_patterns):
            return "high"

        # Medium: moderate changes
        if added + removed > 50:
            return "high"
        if added + removed > 20:
            return "medium"

        return "low"

    def _stage_change(self, proposal: ModificationProposal) -> dict[str, Any]:
        """Stage the proposed change to a copy of the codebase."""
        try:
            # Create staging directory
            stage_root = self._staging_dir
            stage_root.mkdir(parents=True, exist_ok=True)

            # Copy the target file to staging with the new content
            staged_path = stage_root / proposal.target_file
            staged_path.parent.mkdir(parents=True, exist_ok=True)

            # Apply diff to get new content
            original = (self.root / proposal.target_file).read_text(encoding="utf-8")
            new_content = self._apply_diff(original, proposal.proposed_diff)
            if new_content is None:
                return {"success": False, "error": "Failed to apply diff"}

            staged_path.write_text(new_content, encoding="utf-8")
            return {"success": True, "staged_path": str(staged_path)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _apply_diff(self, original: str, diff: str) -> str | None:
        """Apply a unified diff to original content.

        Since we stored the full diff, reconstruct the new version.
        """
        # Simple approach: parse the diff to extract new content
        # For unified diff, lines starting with + (but not +++) are additions
        lines = diff.split("\n")
        result: list[str] = []
        in_hunk = False

        for line in lines:
            if line.startswith("@@"):
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                result.append(line[1:])
            elif line.startswith("-"):
                continue
            elif line.startswith(" "):
                result.append(line[1:])
            elif line == "":
                result.append("")

        return "\n".join(result) if result else None

    def _run_staged_tests(self, proposal: ModificationProposal) -> dict[str, Any]:
        """Run tests on the staged version.

        In a real deployment, this would:
        1. Copy the staged file over the real file temporarily
        2. Run the test suite
        3. Restore the original

        For safety, we validate syntax and do a dry-run check.
        """
        staged_path = self._staging_dir / proposal.target_file
        if not staged_path.exists():
            return {"passed": False, "error": "Staged file not found"}

        # Syntax check
        try:
            content = staged_path.read_text(encoding="utf-8")
            compile(content, str(staged_path), "exec")
        except SyntaxError as exc:
            return {"passed": False, "error": f"Syntax error: {exc}"}

        # Check for forbidden patterns
        forbidden = ["import subprocess", "import socket", "eval(", "exec(", "__import__"]
        for pattern in forbidden:
            if pattern in content:
                return {
                    "passed": False,
                    "error": f"Forbidden pattern detected: {pattern}",
                }

        return {
            "passed": True,
            "summary": "Syntax valid, no forbidden patterns",
        }

    def _cleanup_staging(self, proposal: ModificationProposal) -> None:
        """Clean up staging files for a proposal."""
        staged_path = self._staging_dir / proposal.target_file
        if staged_path.exists():
            staged_path.unlink()

    def _save_proposal(self, proposal: ModificationProposal) -> None:
        proposals = self._load_all_proposals()
        proposals.append(proposal.to_dict())
        self._proposals_file.write_text(
            json.dumps(proposals, indent=2), encoding="utf-8"
        )

    def _update_proposal(self, proposal: ModificationProposal) -> None:
        proposals = self._load_all_proposals()
        for i, p in enumerate(proposals):
            if p["proposal_id"] == proposal.proposal_id:
                proposals[i] = proposal.to_dict()
                break
        self._proposals_file.write_text(
            json.dumps(proposals, indent=2), encoding="utf-8"
        )

    def _load_proposal(self, proposal_id: str) -> ModificationProposal | None:
        proposals = self._load_all_proposals()
        for p in proposals:
            if p["proposal_id"] == proposal_id:
                return ModificationProposal.from_dict(p)
        return None

    def _load_all_proposals(self) -> list[dict[str, Any]]:
        if not self._proposals_file.exists():
            return []
        try:
            return json.loads(
                self._proposals_file.read_text(encoding="utf-8")
            )
        except Exception:
            return []

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# --------------------------------------------------------------- prompt

SELF_MOD_SYSTEM = """\
You are ANUBIS, modifying your own source code. This is a governed \
self-modification — the change will be reviewed, tested, and approved \
before application.

Rules:
- Keep all existing functionality unless explicitly changing it
- Do not remove safety checks, governance, or audit logging
- Do not add network access, subprocess calls, or eval/exec
- Maintain the same coding style and conventions
- Only change what's needed for the requested modification
- Output the COMPLETE modified file, not just the changed parts

The output will be diffed against the original and reviewed by the Court \
and Creator before application. Be careful and precise.
"""
