"""Documentation generator — ANUBIS writes docs for his own system.

Generates documentation for:
  - Skills (auto-docstrings from function signatures)
  - The SIOS system architecture
  - The knowledge library structure
  - The governance system
  - The evidence ledger summary

Output is Markdown, suitable for reading in the desktop or exporting.
"""
from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Any

from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry


class DocGenerator:
    """Generates documentation for the SIOS system."""

    def __init__(
        self,
        library: SkillLibrary,
        ledger: Ledger,
        kb: KnowledgeBase,
        registry: Registry,
    ) -> None:
        self.library = library
        self.ledger = ledger
        self.kb = kb
        self.registry = registry

    def generate_skill_docs(self) -> str:
        """Generate documentation for all promoted skills."""
        lines = ["# ANUBIS Skill Library", ""]
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Total skills: {len(list(self.library.iter_current()))}")
        lines.append("")

        for skill in sorted(self.library.iter_current(), key=lambda s: s.name):
            lines.append(f"## {skill.name} v{skill.version}")
            lines.append("")
            # Parse the code to extract function signatures and docstrings
            try:
                tree = ast.parse(skill.code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        lines.append(f"### `{node.name}()`")
                        # Get docstring
                        if (node.body and isinstance(node.body[0], ast.Expr)
                                and isinstance(node.body[0].value, ast.Constant)
                                and isinstance(node.body[0].value.value, str)):
                            lines.append(f"  {node.body[0].value.value}")
                        # Get args
                        args = [a.arg for a in node.args.args]
                        if args:
                            lines.append(f"  Parameters: {', '.join(args)}")
                        lines.append("")
            except SyntaxError:
                lines.append(f"  (source parse error)")
                lines.append("")

            lines.append(f"  Model: {skill.provenance.model}")
            lines.append(f"  Attempt: {skill.provenance.attempt}")
            lines.append(f"  Hash: `{skill.artifact_hash[:32]}...`")
            lines.append("")

        return "\n".join(lines)

    def generate_system_doc(self) -> str:
        """Generate system architecture documentation."""
        lines = ["# SIOS System Architecture", ""]
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        lines.append("## Overview")
        lines.append("")
        lines.append("SIOS (Sovereign Interactive Operating System) is a local-first")
        lines.append("Linux environment with ANUBIS as its intelligence. Everything")
        lines.append("runs locally — no cloud, no external services.")
        lines.append("")

        lines.append("## Components")
        lines.append("")
        lines.append("### Knowledge Library")
        lines.append(f"- Documents: {self.kb.library_size()}")
        lines.append(f"- Directors: {len(list(self.registry.directors()))}")
        specs = sum(len(self.registry.specialties_by_director(d.director_id)) for d in self.registry.directors())
        lines.append(f"- Specialties: {specs}")
        lines.append("")

        lines.append("### Skill Library")
        skills = list(self.library.iter_current())
        lines.append(f"- Promoted skills: {len(skills)}")
        lines.append(f"- Skills: {', '.join(sorted(s.name for s in skills))}")
        lines.append("")

        lines.append("### Evidence Ledger")
        lines.append(f"- Entries: {self.ledger.length}")
        ok, _ = self.ledger.verify()
        lines.append(f"- Integrity: {'verified' if ok else 'FAILED'}")
        lines.append("")

        lines.append("### Governance")
        lines.append("- 8 immutable laws")
        lines.append("- 5 change classes (routine, sandboxed, promotion, consequential, main engine)")
        lines.append("- Court reviews main engine changes")
        lines.append("- Policy engine enforces spending limits")
        lines.append("")

        lines.append("### Architecture")
        lines.append("- Base: Ubuntu 24.04")
        lines.append("- Desktop: Godot 4 spatial environment (13 rooms)")
        lines.append("- Model: Ollama local server (qwen2.5-coder:7b)")
        lines.append("- Embeddings: nomic-embed-text (768-dim)")
        lines.append("- IPC: Unix socket at /tmp/anubis.sock")
        lines.append("- Sandbox: unshare + mount namespace, network blocked")
        lines.append("")

        return "\n".join(lines)

    def generate_knowledge_doc(self) -> str:
        """Generate knowledge library documentation."""
        lines = ["# Knowledge Library", ""]
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        for d in self.registry.directors():
            specs = self.registry.specialties_by_director(d.director_id)
            doc_count = sum(
                1 for doc in self.kb.library_documents()
                if doc.specialty_id in [s.specialty_id for s in specs]
            )
            lines.append(f"## {d.name}")
            lines.append(f"- Specialties: {len(specs)}")
            lines.append(f"- Documents: {doc_count}")
            lines.append("")
            for spec in specs[:5]:
                docs = [doc for doc in self.kb.library_documents() if doc.specialty_id == spec.specialty_id]
                lines.append(f"  - {spec.canonical_name} ({len(docs)} docs)")
            if len(specs) > 5:
                lines.append(f"  - ... and {len(specs) - 5} more")
            lines.append("")

        return "\n".join(lines)

    def generate_all(self, output_dir: str | Path) -> dict[str, str]:
        """Generate all documentation to files."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        files = {}
        docs = {
            "skills.md": self.generate_skill_docs(),
            "system.md": self.generate_system_doc(),
            "knowledge.md": self.generate_knowledge_doc(),
        }
        for fname, content in docs.items():
            path = out / fname
            path.write_text(content, encoding="utf-8")
            files[fname] = str(path)

        return files
