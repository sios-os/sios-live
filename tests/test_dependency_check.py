"""Tests for the dependency checker module.

Tests verify:
- Dependency dataclass
- Dependency manifest contents
- Self-check runs and produces a report
- Status endpoint
- Mark replaced
- Get dependency
- Self-reliance calculation
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.dependency_check import (
    DependencyChecker,
    Dependency,
    DEPENDENCY_MANIFEST,
)


class TestDependency(unittest.TestCase):
    """Tests for Dependency dataclass."""

    def test_creation(self):
        dep = Dependency(name="test", type="pip_package")
        self.assertEqual(dep.name, "test")
        self.assertEqual(dep.status, "active")

    def test_to_dict(self):
        dep = Dependency(name="test", type="service", status="replaced",
                         replacement="self-hosted")
        d = dep.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["status"], "replaced")
        self.assertEqual(d["replacement"], "self-hosted")


class TestDependencyManifest(unittest.TestCase):
    """Tests for the manifest contents."""

    def test_manifest_not_empty(self):
        self.assertGreater(len(DEPENDENCY_MANIFEST), 5)

    def test_all_have_required_fields(self):
        for dep in DEPENDENCY_MANIFEST:
            self.assertTrue(dep.name)
            self.assertTrue(dep.type)
            self.assertIn(dep.status, ["replaced", "optional", "active", "missing"])

    def test_ollama_in_manifest(self):
        names = [d.name for d in DEPENDENCY_MANIFEST]
        self.assertIn("Ollama", names)

    def test_paramiko_marked_replaced(self):
        dep = next(d for d in DEPENDENCY_MANIFEST if d.name == "paramiko")
        self.assertEqual(dep.status, "replaced")

    def test_nomic_marked_optional(self):
        dep = next(d for d in DEPENDENCY_MANIFEST if d.name == "nomic-embed-text")
        self.assertEqual(dep.status, "optional")


class TestDependencyChecker(unittest.TestCase):
    """Tests for the DependencyChecker."""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_check_pip_package_installed(self):
        # json is always installed
        self.assertTrue(self.checker.check_pip_package("json"))

    def test_check_pip_package_not_installed(self):
        self.assertFalse(self.checker.check_pip_package("nonexistent_pkg_xyz"))

    def test_check_system_binary(self):
        # python should be available
        result = self.checker.check_system_binary("python")
        # May or may not be available depending on system
        self.assertIsInstance(result, bool)

    def test_run_self_check(self):
        report = self.checker.run_self_check()
        self.assertIn("total_dependencies", report)
        self.assertIn("replaced", report)
        self.assertIn("optional", report)
        self.assertIn("active", report)
        self.assertIn("self_reliance_pct", report)
        self.assertIn("dependencies", report)
        self.assertGreater(report["total_dependencies"], 0)

    def test_self_reliance_positive(self):
        report = self.checker.run_self_check()
        self.assertGreater(report["self_reliance_pct"], 0)

    def test_status(self):
        status = self.checker.status()
        self.assertIn("total", status)
        self.assertIn("replaced", status)
        self.assertIn("optional", status)
        self.assertIn("active", status)
        self.assertIn("self_reliance_pct", status)

    def test_get_dependency(self):
        dep = self.checker.get_dependency("Ollama")
        self.assertIsNotNone(dep)
        self.assertEqual(dep.name, "Ollama")

    def test_get_nonexistent_dependency(self):
        self.assertIsNone(self.checker.get_dependency("nonexistent"))

    def test_mark_replaced(self):
        result = self.checker.mark_replaced("qwen2.5-coder:7b", "anubis-own-model")
        self.assertTrue(result)
        dep = self.checker.get_dependency("qwen2.5-coder:7b")
        self.assertEqual(dep.status, "replaced")
        self.assertEqual(dep.replacement, "anubis-own-model")
        self.assertGreater(dep.replaced_at, 0)

    def test_mark_replaced_nonexistent(self):
        result = self.checker.mark_replaced("nonexistent", "nothing")
        self.assertFalse(result)

    def test_self_check_includes_all_deps(self):
        report = self.checker.run_self_check()
        self.assertEqual(len(report["dependencies"]), len(DEPENDENCY_MANIFEST))


class TestSelfRelianceCalculation(unittest.TestCase):
    """Tests for self-reliance percentage calculation."""

    def test_all_optional_or_replaced(self):
        checker = DependencyChecker()
        # Mark all as replaced or optional
        for dep in checker._manifest:
            if dep.status == "active":
                dep.status = "optional"
        status = checker.status()
        self.assertEqual(status["self_reliance_pct"], 100.0)

    def test_all_active(self):
        checker = DependencyChecker()
        for dep in checker._manifest:
            dep.status = "active"
        status = checker.status()
        self.assertEqual(status["self_reliance_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
