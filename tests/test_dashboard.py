"""Tests for web dashboard."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.dashboard import WebDashboard


class TestWebDashboard(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.dashboard = WebDashboard(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_html(self):
        html = self.dashboard.get_html()
        self.assertIn("<html", html)
        self.assertIn("ANUBIS", html)
        self.assertIn("</html>", html)

    def test_get_html_bytes(self):
        data = self.dashboard.get_html_bytes()
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 100)

    def test_content_type(self):
        self.assertEqual(self.dashboard.content_type, "text/html; charset=utf-8")

    def test_content_length(self):
        self.assertEqual(self.dashboard.content_length, len(self.dashboard.get_html_bytes()))

    def test_html_contains_dashboard_elements(self):
        html = self.dashboard.get_html()
        self.assertIn("Control Panel", html)
        self.assertIn("Cameras", html)
        self.assertIn("Threats", html)
        self.assertIn("Network", html)
        self.assertIn("Weather", html)
        self.assertIn("Schedule", html)
        self.assertIn("Chat", html)

    def test_html_contains_api_calls(self):
        html = self.dashboard.get_html()
        self.assertIn("/api/status", html)
        self.assertIn("/api/cameras", html)
        self.assertIn("/api/threats", html)
        self.assertIn("/api/chat", html)

    def test_html_contains_javascript(self):
        html = self.dashboard.get_html()
        self.assertIn("<script>", html)
        self.assertIn("function", html)
        self.assertIn("fetch(", html)

    def test_html_contains_css(self):
        html = self.dashboard.get_html()
        self.assertIn("<style>", html)
        self.assertIn("background", html)

    def test_html_valid_structure(self):
        html = self.dashboard.get_html()
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<head>", html)
        self.assertIn("<body>", html)
        self.assertIn("</head>", html)
        self.assertIn("</body>", html)


if __name__ == "__main__":
    unittest.main()
