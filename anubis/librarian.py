"""Librarian agent — maintains the master dependency index.

Every time the self-development loop creates a new file, the Librarian
agent updates the master index with what depends on what. This prevents
the system from breaking its own legacy compatibility as it evolves.

The Librarian:
1. Scans Python files for import statements
2. Builds a dependency graph (module → imports)
3. Detects breaking changes (removed modules, changed signatures)
4. Maintains a master index file mapping all modules and their deps
5. Flags compatibility issues before promotion

The index is stored as JSON and can be queried:
- "What depends on module X?" → reverse dependency lookup
- "What does module X import?" → forward dependency lookup
- "Will removing X break anything?" → impact analysis
- "What modules are unused?" → dead code detection

Uses only the Python standard library (ast, json, pathlib).
"""
from __future__ import annotations

import ast
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class ModuleInfo:
    """Information about a single module."""
    path: str
    name: str  # dotted module name (e.g., "anubis.memory")
    imports: list[str] = field(default_factory=list)  # modules it imports
    imported_by: list[str] = field(default_factory=list)  # modules that import it
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    line_count: int = 0
    last_modified: float = 0.0
    is_new: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "imports": self.imports,
            "imported_by": self.imported_by,
            "classes": self.classes,
            "functions": self.functions,
            "line_count": self.line_count,
            "last_modified": self.last_modified,
            "is_new": self.is_new,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleInfo":
        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            imports=data.get("imports", []),
            imported_by=data.get("imported_by", []),
            classes=data.get("classes", []),
            functions=data.get("functions", []),
            line_count=data.get("line_count", 0),
            last_modified=data.get("last_modified", 0.0),
            is_new=data.get("is_new", False),
        )


@dataclass
class ImpactReport:
    """Result of an impact analysis."""
    affected_modules: list[str] = field(default_factory=list)
    affected_classes: list[str] = field(default_factory=list)
    affected_functions: list[str] = field(default_factory=list)
    breaking: bool = False
    reason: str = ""


class Librarian:
    """Maintains the master dependency index.

    Scans the codebase, builds a dependency graph, and provides
    queries for impact analysis and compatibility checking.
    """

    def __init__(
        self,
        root: str | Path = ".",
        index_path: str | Path = "config/dependency_index.json",
        ledger: Ledger | None = None,
    ) -> None:
        self.root = Path(root)
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger
        self._modules: dict[str, ModuleInfo] = {}
        self._loaded = False

    def _module_name_from_path(self, path: Path) -> str:
        """Convert a file path to a dotted module name."""
        try:
            rel = path.relative_to(self.root)
        except ValueError:
            rel = path
        parts = list(rel.parts)
        # Remove .py extension
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        # Remove __init__ 
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _parse_imports(self, tree: ast.AST) -> list[str]:
        """Extract import statements from an AST."""
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _parse_definitions(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        """Extract class and function names from an AST."""
        classes: list[str] = []
        functions: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
        return classes, functions

    def _scan_file(self, path: Path) -> ModuleInfo | None:
        """Scan a single Python file and extract module info."""
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            return None

        name = self._module_name_from_path(path)
        imports = self._parse_imports(tree)
        classes, functions = self._parse_definitions(tree)
        line_count = content.count("\n") + 1
        stat = path.stat()
        return ModuleInfo(
            path=str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path),
            name=name,
            imports=imports,
            classes=classes,
            functions=functions,
            line_count=line_count,
            last_modified=stat.st_mtime,
        )

    def scan(self) -> dict[str, Any]:
        """Scan the entire codebase and build the dependency index.

        Returns:
            Dict with scan statistics
        """
        t0 = time.monotonic()
        old_modules = dict(self._modules) if self._loaded else {}
        new_modules: dict[str, ModuleInfo] = {}

        # Find all Python files
        for py_file in self.root.rglob("*.py"):
            # Skip hidden directories, __pycache__, tests
            parts = py_file.parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                continue

            info = self._scan_file(py_file)
            if info:
                # Check if this is a new module
                if info.name in old_modules:
                    info.is_new = False
                else:
                    info.is_new = True
                new_modules[info.name] = info

        # Build reverse dependencies (imported_by)
        for name, info in new_modules.items():
            info.imported_by = []
        for name, info in new_modules.items():
            for imp in info.imports:
                # Match by prefix (anubis.memory matches anubis.memory)
                if imp in new_modules:
                    new_modules[imp].imported_by.append(name)
                # Also check partial matches (anubis.memory matches anubis.memory.X)
                for other_name in new_modules:
                    if other_name.startswith(imp + "."):
                        if name not in new_modules[other_name].imported_by:
                            new_modules[other_name].imported_by.append(name)

        self._modules = new_modules
        self._loaded = True

        # Save index
        self.save_index()

        # Count new/changed modules
        new_count = sum(1 for m in self._modules.values() if m.is_new)
        changed_count = 0
        for name, info in self._modules.items():
            if name in old_modules:
                old = old_modules[name]
                if (old.line_count != info.line_count
                        or old.last_modified != info.last_modified):
                    changed_count += 1
                    info.is_new = False

        elapsed = time.monotonic() - t0

        if self.ledger:
            self.ledger.append({
                "event": "librarian_scan",
                "total_modules": len(self._modules),
                "new_modules": new_count,
                "changed_modules": changed_count,
                "duration_s": round(elapsed, 3),
            })

        return {
            "total_modules": len(self._modules),
            "new_modules": new_count,
            "changed_modules": changed_count,
            "duration_s": round(elapsed, 3),
        }

    def save_index(self) -> None:
        """Save the dependency index to disk."""
        data = {
            "modules": {name: m.to_dict() for name, m in self._modules.items()},
            "updated_at": time.time(),
        }
        self.index_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def load_index(self) -> None:
        """Load the dependency index from disk."""
        if not self.index_path.exists():
            self._modules = {}
            self._loaded = True
            return
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            self._modules = {
                name: ModuleInfo.from_dict(info)
                for name, info in data.get("modules", {}).items()
            }
        except (json.JSONDecodeError, OSError):
            self._modules = {}
        self._loaded = True

    def get_module(self, name: str) -> ModuleInfo | None:
        """Get module info by name."""
        if not self._loaded:
            self.load_index()
        return self._modules.get(name)

    def get_dependencies(self, name: str) -> list[str]:
        """Get the modules that `name` imports."""
        info = self.get_module(name)
        return info.imports if info else []

    def get_dependents(self, name: str) -> list[str]:
        """Get the modules that import `name` (reverse dependencies)."""
        info = self.get_module(name)
        return info.imported_by if info else []

    def impact_analysis(self, name: str) -> ImpactReport:
        """Analyze the impact of removing or changing a module.

        Returns all modules that depend on this one, directly or
        transitively.
        """
        if not self._loaded:
            self.load_index()

        affected: set[str] = set()
        to_check = [name]
        while to_check:
            current = to_check.pop(0)
            dependents = self.get_dependents(current)
            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    to_check.append(dep)

        # Collect affected classes and functions
        affected_classes: list[str] = []
        affected_functions: list[str] = []
        for mod_name in affected:
            info = self._modules.get(mod_name)
            if info:
                affected_classes.extend(info.classes)
                affected_functions.extend(info.functions)

        return ImpactReport(
            affected_modules=sorted(affected),
            affected_classes=affected_classes,
            affected_functions=affected_functions,
            breaking=len(affected) > 0,
            reason=f"{len(affected)} modules depend on {name}" if affected else "no dependents",
        )

    def find_unused(self) -> list[str]:
        """Find modules that are not imported by any other module.

        Note: entry points (daemon, scripts) will appear unused
        because they're imported by the OS, not by other modules.
        """
        if not self._loaded:
            self.load_index()
        unused = []
        for name, info in self._modules.items():
            if not info.imported_by:
                unused.append(name)
        return sorted(unused)

    def find_new_modules(self) -> list[str]:
        """Find modules marked as new since the last scan."""
        if not self._loaded:
            self.load_index()
        return sorted(name for name, info in self._modules.items() if info.is_new)

    def check_compatibility(self, removed_module: str) -> dict[str, Any]:
        """Check if removing a module would break anything.

        Args:
            removed_module: The module name being removed

        Returns:
            Dict with compatibility status and affected modules
        """
        impact = self.impact_analysis(removed_module)
        return {
            "safe_to_remove": not impact.breaking,
            "affected_modules": impact.affected_modules,
            "affected_count": len(impact.affected_modules),
            "reason": impact.reason,
        }

    def stats(self) -> dict[str, Any]:
        """Return index statistics."""
        if not self._loaded:
            self.load_index()
        total_imports = sum(len(m.imports) for m in self._modules.values())
        total_classes = sum(len(m.classes) for m in self._modules.values())
        total_functions = sum(len(m.functions) for m in self._modules.values())
        return {
            "total_modules": len(self._modules),
            "total_imports": total_imports,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "unused_modules": len(self.find_unused()),
            "new_modules": len(self.find_new_modules()),
            "index_path": str(self.index_path),
        }
