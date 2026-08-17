"""Persistent, versioned skill library.

A skill is a capability ANUBIS wrote for himself: source code plus the tests
that prove it works, plus provenance recording which model produced it and what
evidence justified its promotion.

Two rules shape the storage layout:

  * Recovery law -- nothing is ever overwritten. Promotion always creates a new
    version, so rollback is always possible without recovering from backup.
  * Audit law -- every promoted version records its provenance and the ledger
    sequence that justified it, so any live capability can be traced back to the
    evidence that admitted it.

Layout:

    skills/
      <name>/
        v1/  skill.py  tests.py  manifest.json
        v2/  skill.py  tests.py  manifest.json
        CURRENT            -> text file naming the active version
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

VALID_NAME = re.compile(r"^[a-z][a-z0-9_]{1,48}$")


class SkillError(Exception):
    pass


@dataclass(frozen=True)
class Provenance:
    model: str
    created_at: float
    attempt: int
    ledger_seq: int | None = None
    task: str = ""
    reasoning: str = ""


@dataclass(frozen=True)
class Skill:
    name: str
    version: int
    description: str
    code: str
    tests: str
    provenance: Provenance
    evidence: dict[str, object] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)

    @property
    def artifact_hash(self) -> str:
        """Hash binding all code and tests together.

        Both are included because promoting code without the tests that proved
        it would break the link between capability and evidence. Additional
        files (for multi-file projects) are also included.
        """
        h = hashlib.sha256()
        h.update(self.code.encode("utf-8"))
        h.update(b"\x00")
        h.update(self.tests.encode("utf-8"))
        for fname in sorted(self.files.keys()):
            h.update(b"\x00")
            h.update(fname.encode("utf-8"))
            h.update(b"\x00")
            h.update(self.files[fname].encode("utf-8"))
        return h.hexdigest()

    def manifest(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "artifact_hash": self.artifact_hash,
            "provenance": asdict(self.provenance),
            "evidence": self.evidence,
            "files": self.files,
        }

    @property
    def is_multi_file(self) -> bool:
        """True if this skill has additional files beyond the main module."""
        return bool(self.files)


class SkillLibrary:
    """Versioned on-disk store of promoted skills."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- paths

    def _skill_dir(self, name: str) -> Path:
        return self.root / name

    def _version_dir(self, name: str, version: int) -> Path:
        return self._skill_dir(name) / f"v{version}"

    def _current_file(self, name: str) -> Path:
        return self._skill_dir(name) / "CURRENT"

    # ------------------------------------------------------------ validation

    @staticmethod
    def validate_name(name: str) -> None:
        if not VALID_NAME.match(name):
            raise SkillError(
                f"invalid skill name {name!r}: must be lower_snake_case, "
                "2-49 chars, starting with a letter"
            )

    # --------------------------------------------------------------- queries

    def exists(self, name: str) -> bool:
        return self._current_file(name).exists()

    def versions(self, name: str) -> list[int]:
        d = self._skill_dir(name)
        if not d.is_dir():
            return []
        out = []
        for child in d.iterdir():
            if child.is_dir() and child.name.startswith("v"):
                try:
                    out.append(int(child.name[1:]))
                except ValueError:
                    continue
        return sorted(out)

    def next_version(self, name: str) -> int:
        v = self.versions(name)
        return (v[-1] + 1) if v else 1

    def current_version(self, name: str) -> int | None:
        f = self._current_file(name)
        if not f.exists():
            return None
        try:
            return int(f.read_text(encoding="utf-8").strip())
        except ValueError:
            return None

    def names(self) -> list[str]:
        return sorted(
            d.name for d in self.root.iterdir()
            if d.is_dir() and (d / "CURRENT").exists()
        )

    # ------------------------------------------------------------- retrieval

    def load(self, name: str, version: int | None = None) -> Skill:
        if version is None:
            version = self.current_version(name)
            if version is None:
                raise SkillError(f"skill {name!r} has no promoted version")
        vd = self._version_dir(name, version)
        manifest_path = vd / "manifest.json"
        if not manifest_path.exists():
            raise SkillError(f"skill {name!r} v{version} not found")

        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        code = (vd / "skill.py").read_text(encoding="utf-8")
        tests = (vd / "tests.py").read_text(encoding="utf-8")
        prov = m.get("provenance", {})

        # Load additional files for multi-file projects
        files: dict[str, str] = {}
        files_meta = m.get("files", {})
        for fname in files_meta:
            fpath = vd / fname
            if fpath.exists():
                files[fname] = fpath.read_text(encoding="utf-8")

        skill = Skill(
            name=m["name"],
            version=m["version"],
            description=m.get("description", ""),
            code=code,
            tests=tests,
            provenance=Provenance(
                model=prov.get("model", "unknown"),
                created_at=prov.get("created_at", 0.0),
                attempt=prov.get("attempt", 0),
                ledger_seq=prov.get("ledger_seq"),
                task=prov.get("task", ""),
                reasoning=prov.get("reasoning", ""),
            ),
            evidence=m.get("evidence", {}),
            files=files,
        )

        # Integrity check: stored hash must match the files on disk. Catches
        # out-of-band edits to a promoted skill.
        if m.get("artifact_hash") != skill.artifact_hash:
            raise SkillError(
                f"skill {name!r} v{version} failed integrity check: "
                f"manifest={m.get('artifact_hash', '')[:12]} "
                f"actual={skill.artifact_hash[:12]}"
            )
        return skill

    def iter_current(self) -> Iterator[Skill]:
        for name in self.names():
            try:
                yield self.load(name)
            except SkillError:
                continue

    # ------------------------------------------------------------- promotion

    def promote(self, skill: Skill) -> Skill:
        """Write a new version and make it current.

        Callers must obtain an ALLOW ruling for ChangeClass.PROMOTION before
        calling this. The library stores; the Constitution decides.
        """
        self.validate_name(skill.name)
        version = self.next_version(skill.name)
        stored = Skill(
            name=skill.name,
            version=version,
            description=skill.description,
            code=skill.code,
            tests=skill.tests,
            provenance=skill.provenance,
            evidence=skill.evidence,
            files=skill.files,
        )

        vd = self._version_dir(stored.name, version)
        if vd.exists():
            raise SkillError(f"refusing to overwrite existing {stored.name} v{version}")
        vd.mkdir(parents=True)

        (vd / "skill.py").write_text(stored.code, encoding="utf-8")
        (vd / "tests.py").write_text(stored.tests, encoding="utf-8")
        # Write additional files for multi-file projects
        for fname, content in stored.files.items():
            # Sanitize filename — no path traversal
            safe = Path(fname).name
            if safe != fname:
                raise SkillError(f"unsafe filename in skill: {fname!r}")
            (vd / safe).write_text(content, encoding="utf-8")
        (vd / "manifest.json").write_text(
            json.dumps(stored.manifest(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._current_file(stored.name).write_text(str(version), encoding="utf-8")
        return stored

    def rollback(self, name: str) -> int:
        """Point CURRENT at the previous version.

        Old versions are never deleted, so this is always available -- the
        recovery law in practice.
        """
        vs = self.versions(name)
        cur = self.current_version(name)
        if cur is None or len(vs) < 2:
            raise SkillError(f"skill {name!r} has no earlier version to roll back to")
        earlier = [v for v in vs if v < cur]
        if not earlier:
            raise SkillError(f"skill {name!r} is already at its earliest version")
        target = earlier[-1]
        self._current_file(name).write_text(str(target), encoding="utf-8")
        return target

    def retire(self, name: str) -> None:
        """Deactivate a skill without destroying its history."""
        f = self._current_file(name)
        if not f.exists():
            raise SkillError(f"skill {name!r} is not active")
        f.unlink()

    # ------------------------------------------------------------- rendering

    def build_context(self, limit: int = 12) -> str:
        """Summarize existing skills for the model's prompt.

        Lets ANUBIS see what he already built so he extends his library instead
        of repeatedly rewriting the same capability.
        """
        skills = list(self.iter_current())[:limit]
        if not skills:
            return "(no skills promoted yet)"
        lines = []
        for s in skills:
            sig = s.code.strip().splitlines()
            first_def = next(
                (l.strip() for l in sig if l.strip().startswith("def ")), "?"
            )
            lines.append(f"- {s.name} v{s.version}: {first_def}  # {s.description}")
        return "\n".join(lines)


# ------------------------------------------------------------------- parsing

SKILL_MARK = "<<<SKILL>>>"
TESTS_MARK = "<<<TESTS>>>"
END_MARK = "<<<END>>>"


def strip_fences(text: str) -> str:
    """Remove markdown code fences that models add despite instructions."""
    text = re.sub(r"^\s*```[a-zA-Z0-9_+-]*\s*\n", "", text)
    text = re.sub(r"\n\s*```\s*$", "", text)
    return text.strip()


def parse_proposal(raw: str) -> tuple[str, str]:
    """Extract (code, tests) from a model response.

    Small local models are inconsistent about output format, so this accepts the
    marker format first and falls back to fenced blocks. It raises rather than
    guessing when neither is present -- silently accepting malformed output
    would let an unverifiable artifact reach the sandbox.
    """
    if SKILL_MARK in raw and TESTS_MARK in raw:
        head, rest = raw.split(SKILL_MARK, 1)
        code_part, tests_part = rest.split(TESTS_MARK, 1)
        if END_MARK in tests_part:
            tests_part = tests_part.split(END_MARK, 1)[0]
        code, tests = strip_fences(code_part), strip_fences(tests_part)
        if code and tests:
            return code, tests

    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    if len(blocks) >= 2:
        return blocks[0].strip(), blocks[1].strip()

    raise SkillError(
        "could not parse a skill and a test block from the model response. "
        f"Response began: {raw[:200]!r}"
    )


# Multi-file project parser
FILE_MARK = re.compile(r"<<<FILE:\s*([^>]+)\s*>>>")
FILE_HEADER = re.compile(r"^###\s+FILE:\s*(\S+)\s*$", re.MULTILINE)


def parse_project_proposal(raw: str) -> tuple[str, str, dict[str, str]]:
    """Extract (main_code, tests, extra_files) from a multi-file model response.

    Handles the messy reality of small model outputs:
    1. Markers inside a single code fence (as Python comments)
    2. Markers outside code fences
    3. Markdown ### FILE: headers
    4. Mixed formats with preamble text
    """
    files: dict[str, str] = {}
    tests = ""

    # Step 1: Extract content from code fences if present.
    # Models often wrap everything in a single ```python block.
    fence_blocks = re.findall(r"```[a-zA-Z]*\s*\n(.*?)```", raw, re.DOTALL)
    if fence_blocks:
        # Use the largest code block (likely contains everything)
        raw = max(fence_blocks, key=len)

    # Step 2: Normalize — remove "# " prefix from markers
    raw = re.sub(
        r"^#\s*(<<<(?:FILE|TESTS|END)[^>]*>>>)",
        r"\1",
        raw,
        flags=re.MULTILINE,
    )

    # Step 2b: Also normalize plain "# FILE: name.py" to "<<<FILE: name.py>>>"
    raw = re.sub(
        r"^#\s*FILE:\s*(\S+)\s*$",
        r"<<<FILE: \1>>>",
        raw,
        flags=re.MULTILINE,
    )
    # Normalize "# TESTS" to "<<<TESTS>>>"
    raw = re.sub(
        r"^#\s*TESTS\s*$",
        TESTS_MARK,
        raw,
        flags=re.MULTILINE,
    )

    # Step 3: Try FILE markers
    if FILE_MARK.search(raw):
        parts = FILE_MARK.split(raw)
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break
            fname = parts[i].strip()
            content = parts[i + 1]
            if TESTS_MARK in content:
                file_content, rest = content.split(TESTS_MARK, 1)
                if END_MARK in rest:
                    rest = rest.split(END_MARK, 1)[0]
                tests = strip_fences(rest)
                content = strip_fences(file_content)
            else:
                content = strip_fences(content)
            if content:
                files[fname] = content

    # Step 4: Try TESTS marker without FILE markers
    if not files and TESTS_MARK in raw:
        pre, post = raw.split(TESTS_MARK, 1)
        if END_MARK in post:
            post = post.split(END_MARK, 1)[0]
        tests = strip_fences(post)
        pre_stripped = strip_fences(pre)
        if pre_stripped:
            files["main.py"] = pre_stripped

    # Step 5: Try markdown ### FILE: headers
    if not files and FILE_HEADER.search(raw):
        sections = FILE_HEADER.split(raw)
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                break
            fname = sections[i].strip()
            content = sections[i + 1]
            tests_match = re.search(r"###\s+TESTS\s*\n", content)
            if tests_match:
                file_content = content[:tests_match.start()]
                tests_content = content[tests_match.end():]
                next_header = re.search(r"^###\s+", tests_content, re.MULTILINE)
                if next_header:
                    tests_content = tests_content[:next_header.start()]
                tests = strip_fences(tests_content)
                content = strip_fences(file_content)
            else:
                content = strip_fences(content)
            if content:
                files[fname] = content

    # Step 6: Fallback to single-file parser
    if not files:
        code, tests = parse_proposal(raw)
        return code, tests, {}

    if not tests:
        raise SkillError(
            "multi-file proposal parsed but no tests section found. "
            f"Files found: {list(files.keys())}"
        )

    # Determine main code: prefer main.py, __main__.py, or first file
    main_names = ["main.py", "__main__.py", "skill.py"]
    main_code = ""
    for mn in main_names:
        if mn in files:
            main_code = files.pop(mn)
            break
    if not main_code:
        first_name = next(iter(files))
        main_code = files.pop(first_name)

    return main_code, tests, files


def validate_syntax(code: str, label: str) -> None:
    """Reject non-parsing source before it reaches the sandbox."""
    import ast

    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise SkillError(f"{label} is not valid Python: {exc}") from exc
