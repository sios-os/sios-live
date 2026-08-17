"""Tests for the librarian module.

Tests verify:
- File scanning and import extraction
- Dependency graph building (forward and reverse)
- Impact analysis (what depends on what)
- Unused module detection
- New module detection
- Compatibility checking
- Index persistence (save/load)
- Stats endpoint
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.librarian import Librarian, ModuleInfo, ImpactReport


class TestModuleInfo(unittest.TestCase):
    """Tests for ModuleInfo dataclass."""

    def test_creation(self):
        m = ModuleInfo(path="anubis/foo.py", name="anubis.foo")
        self.assertEqual(m.name, "anubis.foo")
        self.assertEqual(m.imports, [])

    def test_to_dict_and_from_dict(self):
        m = ModuleInfo(
            path="anubis/foo.py", name="anubis.foo",
            imports=["os", "json"], classes=["Foo"],
            functions=["bar"], line_count=100,
        )
        d = m.to_dict()
        m2 = ModuleInfo.from_dict(d)
        self.assertEqual(m2.name, "anubis.foo")
        self.assertEqual(m2.imports, ["os", "json"])
        self.assertEqual(m2.classes, ["Foo"])


class TestLibrarian(unittest.TestCase):
    """Tests for the Librarian agent."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-librarian-")
        # Create a small codebase
        root = Path(self.tmpdir)
        (root / "anubis").mkdir()
        (root / "anubis" / "__init__.py").write_text("")
        (root / "anubis" / "core.py").write_text(
            "import os\nimport json\n\nclass Core:\n    pass\n\ndef main():\n    pass\n"
        )
        (root / "anubis" / "utils.py").write_text(
            "from anubis.core import Core\n\nclass Utils:\n    pass\n\ndef helper():\n    pass\n"
        )
        (root / "anubis" / "extra.py").write_text(
            "from anubis.core import Core\nfrom anubis.utils import Utils\n\nclass Extra:\n    pass\n"
        )
        (root / "standalone.py").write_text(
            "import sys\n\ndef standalone_func():\n    pass\n"
        )

        self.librarian = Librarian(
            root=root,
            index_path=Path(self.tmpdir) / "index.json",
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan(self):
        result = self.librarian.scan()
        self.assertGreater(result["total_modules"], 0)
        self.assertIn("anubis.core", self.librarian._modules)
        self.assertIn("anubis.utils", self.librarian._modules)

    def test_imports_extracted(self):
        self.librarian.scan()
        core = self.librarian.get_module("anubis.core")
        self.assertIsNotNone(core)
        self.assertIn("os", core.imports)
        self.assertIn("json", core.imports)

    def test_classes_and_functions_extracted(self):
        self.librarian.scan()
        core = self.librarian.get_module("anubis.core")
        self.assertIn("Core", core.classes)
        self.assertIn("main", core.functions)

    def test_reverse_dependencies(self):
        self.librarian.scan()
        core = self.librarian.get_module("anubis.core")
        # anubis.utils and anubis.extra both import anubis.core
        self.assertIn("anubis.utils", core.imported_by)
        self.assertIn("anubis.extra", core.imported_by)

    def test_get_dependencies(self):
        self.librarian.scan()
        deps = self.librarian.get_dependencies("anubis.utils")
        self.assertIn("anubis.core", deps)

    def test_get_dependents(self):
        self.librarian.scan()
        dependents = self.librarian.get_dependents("anubis.core")
        self.assertIn("anubis.utils", dependents)

    def test_impact_analysis(self):
        self.librarian.scan()
        impact = self.librarian.impact_analysis("anubis.core")
        self.assertTrue(impact.breaking)
        self.assertIn("anubis.utils", impact.affected_modules)
        self.assertIn("anubis.extra", impact.affected_modules)

    def test_impact_analysis_no_dependents(self):
        self.librarian.scan()
        impact = self.librarian.impact_analysis("standalone")
        self.assertFalse(impact.breaking)
        self.assertEqual(impact.affected_modules, [])

    def test_impact_analysis_transitive(self):
        self.librarian.scan()
        # anubis.extra depends on anubis.utils which depends on anubis.core
        impact = self.librarian.impact_analysis("anubis.core")
        # anubis.extra should be affected (transitively through utils)
        self.assertIn("anubis.extra", impact.affected_modules)

    def test_find_unused(self):
        self.librarian.scan()
        unused = self.librarian.find_unused()
        # standalone.py is not imported by anything
        self.assertIn("standalone", unused)

    def test_check_compatibility_safe(self):
        self.librarian.scan()
        result = self.librarian.check_compatibility("standalone")
        self.assertTrue(result["safe_to_remove"])
        self.assertEqual(result["affected_count"], 0)

    def test_check_compatibility_unsafe(self):
        self.librarian.scan()
        result = self.librarian.check_compatibility("anubis.core")
        self.assertFalse(result["safe_to_remove"])
        self.assertGreater(result["affected_count"], 0)

    def test_index_persistence(self):
        self.librarian.scan()
        # Create new librarian from same index
        lib2 = Librarian(
            root=self.librarian.root,
            index_path=self.librarian.index_path,
        )
        lib2.load_index()
        self.assertIn("anubis.core", lib2._modules)

    def test_stats(self):
        self.librarian.scan()
        stats = self.librarian.stats()
        self.assertIn("total_modules", stats)
        self.assertIn("total_imports", stats)
        self.assertIn("total_classes", stats)
        self.assertGreater(stats["total_modules"], 0)

    def test_new_modules_detected(self):
        self.librarian.scan()
        # First scan — all modules are new
        new = self.librarian.find_new_modules()
        self.assertGreater(len(new), 0)

    def test_scan_finds_all_files(self):
        self.librarian.scan()
        names = self.librarian._modules.keys()
        self.assertIn("anubis.core", names)
        self.assertIn("anubis.utils", names)
        self.assertIn("anubis.extra", names)
        self.assertIn("standalone", names)


class TestLibrarianEdgeCases(unittest.TestCase):
    """Edge case tests for the Librarian."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-lib-edge-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_codebase(self):
        lib = Librarian(root=self.tmpdir, index_path=Path(self.tmpdir) / "idx.json")
        result = lib.scan()
        self.assertEqual(result["total_modules"], 0)

    def test_syntax_error_file_skipped(self):
        root = Path(self.tmpdir)
        (root / "bad.py").write_text("def broken(:\n    pass\n")
        lib = Librarian(root=root, index_path=Path(self.tmpdir) / "idx.json")
        lib.scan()
        # Should not crash, bad file should be skipped
        self.assertNotIn("bad", lib._modules)

    def test_load_nonexistent_index(self):
        lib = Librarian(root=self.tmpdir, index_path=Path(self.tmpdir) / "nope.json")
        lib.load_index()
        self.assertEqual(len(lib._modules), 0)


if __name__ == "__main__":
    unittest.main()
