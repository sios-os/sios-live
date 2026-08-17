"""Tests for the Linux deployment checker."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.linux_deploy_check import LinuxDeployChecker, CheckResult


class TestLinuxDeployChecker(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent
        self.checker = LinuxDeployChecker(self.root)

    def test_run_all_returns_results(self):
        results = self.checker.run_all()
        self.assertIn("total_checks", results)
        self.assertIn("passed", results)
        self.assertIn("failed", results)
        self.assertIn("results", results)
        self.assertGreater(results["total_checks"], 0)

    def test_check_python_version(self):
        self.checker.check_python_version()
        self.assertEqual(len(self.checker.results), 1)
        self.assertTrue(self.checker.results[0].passed)

    def test_check_platform_imports(self):
        self.checker.check_platform_imports()
        self.assertEqual(len(self.checker.results), 1)
        # On Windows this will fail, on Linux it will pass
        if sys.platform == "win32":
            self.assertFalse(self.checker.results[0].passed)
        else:
            self.assertTrue(self.checker.results[0].passed)

    def test_check_unix_socket_config(self):
        self.checker.check_unix_socket_config()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_hardcoded_windows_paths(self):
        self.checker.check_hardcoded_windows_paths()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_systemd_services(self):
        self.checker.check_systemd_services()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_signal_handling(self):
        self.checker.check_signal_handling()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_process_management(self):
        self.checker.check_process_management()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_path_separators(self):
        self.checker.check_path_separators()
        self.assertEqual(len(self.checker.results), 1)

    def test_check_test_compatibility(self):
        self.checker.check_test_compatibility()
        self.assertEqual(len(self.checker.results), 1)

    def test_all_checks_run(self):
        """Ensure all checks complete without exceptions."""
        results = self.checker.run_all()
        for r in results["results"]:
            self.assertIn("name", r)
            self.assertIn("passed", r)
            self.assertIn("message", r)


class TestCheckResult(unittest.TestCase):
    def test_creation(self):
        r = CheckResult(name="test", passed=True, message="OK")
        self.assertEqual(r.name, "test")
        self.assertTrue(r.passed)
        self.assertEqual(r.message, "OK")
        self.assertEqual(r.fix, "")

    def test_with_fix(self):
        r = CheckResult(name="test", passed=False, message="Bad", fix="Fix it")
        self.assertEqual(r.fix, "Fix it")


if __name__ == "__main__":
    unittest.main()
