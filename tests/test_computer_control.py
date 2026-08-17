"""Tests for computer control — file ops, app launching, web search, media."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.computer_control import ComputerControl, ActionResult, APP_REGISTRY, SEARCH_ENGINES


class TestComputerControl(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.home = self.root / "home"
        self.home.mkdir(parents=True, exist_ok=True)
        self.cc = ComputerControl(
            self.root,
            ledger=MagicMock(),
            home_dir=self.home,
            require_confirmation=True,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # FILE OPERATIONS
    # ===========================================================

    def test_file_create(self):
        result = self.cc.file_create("test.txt", "Hello World")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "test.txt").exists())
        self.assertEqual((self.home / "test.txt").read_text(), "Hello World")

    def test_file_create_nested(self):
        result = self.cc.file_create("subdir/test.txt", "content")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "subdir" / "test.txt").exists())

    def test_file_read(self):
        self.cc.file_create("test.txt", "Hello World")
        result = self.cc.file_read("test.txt")
        self.assertTrue(result.success)
        self.assertEqual(result.data["content"], "Hello World")

    def test_file_read_not_found(self):
        result = self.cc.file_read("nonexistent.txt")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error.lower())

    def test_file_read_truncation(self):
        long_content = "A" * 100000
        self.cc.file_create("big.txt", long_content)
        result = self.cc.file_read("big.txt", max_chars=1000)
        self.assertTrue(result.success)
        self.assertLessEqual(len(result.data["content"]), 1100)

    def test_file_write(self):
        self.cc.file_create("test.txt", "initial")
        result = self.cc.file_write("test.txt", "overwritten")
        self.assertTrue(result.success)
        self.assertEqual((self.home / "test.txt").read_text(), "overwritten")

    def test_file_write_append(self):
        self.cc.file_create("test.txt", "line1\n")
        result = self.cc.file_write("test.txt", "line2\n", append=True)
        self.assertTrue(result.success)
        self.assertEqual((self.home / "test.txt").read_text(), "line1\nline2\n")

    def test_file_delete_requires_confirmation(self):
        self.cc.file_create("test.txt", "content")
        result = self.cc.file_delete("test.txt")
        self.assertFalse(result.success)
        self.assertTrue(result.data.get("needs_confirmation"))
        # File should still exist
        self.assertTrue((self.home / "test.txt").exists())

    def test_file_delete_confirmed(self):
        self.cc.file_create("test.txt", "content")
        result = self.cc.file_delete("test.txt", confirmed=True)
        self.assertTrue(result.success)
        self.assertFalse((self.home / "test.txt").exists())

    def test_file_delete_not_found(self):
        result = self.cc.file_delete("nonexistent.txt", confirmed=True)
        self.assertFalse(result.success)

    def test_file_move(self):
        self.cc.file_create("src.txt", "content")
        result = self.cc.file_move("src.txt", "dst.txt")
        self.assertTrue(result.success)
        self.assertFalse((self.home / "src.txt").exists())
        self.assertTrue((self.home / "dst.txt").exists())

    def test_file_copy(self):
        self.cc.file_create("src.txt", "content")
        result = self.cc.file_copy("src.txt", "dst.txt")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "src.txt").exists())
        self.assertTrue((self.home / "dst.txt").exists())

    def test_file_list(self):
        self.cc.file_create("a.txt", "1")
        self.cc.file_create("b.txt", "2")
        result = self.cc.file_list("")
        self.assertTrue(result.success)
        names = [e["name"] for e in result.data["entries"]]
        self.assertIn("a.txt", names)
        self.assertIn("b.txt", names)

    def test_file_list_with_pattern(self):
        self.cc.file_create("a.txt", "1")
        self.cc.file_create("b.csv", "2")
        result = self.cc.file_list("", pattern="*.txt")
        self.assertTrue(result.success)
        names = [e["name"] for e in result.data["entries"]]
        self.assertIn("a.txt", names)
        self.assertNotIn("b.csv", names)

    def test_file_organize(self):
        self.cc.file_create("doc.pdf", "content")
        self.cc.file_create("pic.jpg", "content")
        self.cc.file_create("song.mp3", "content")
        result = self.cc.file_organize("")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "Documents" / "doc.pdf").exists())
        self.assertTrue((self.home / "Images" / "pic.jpg").exists())
        self.assertTrue((self.home / "Audio" / "song.mp3").exists())

    def test_file_create_path_not_allowed(self):
        result = self.cc.file_create("/etc/somefile", "content")
        self.assertFalse(result.success)
        self.assertIn("not allowed", result.error.lower())

    # ===========================================================
    # FOLDER OPERATIONS
    # ===========================================================

    def test_folder_create(self):
        result = self.cc.folder_create("new_folder")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "new_folder").is_dir())

    def test_folder_create_nested(self):
        result = self.cc.folder_create("a/b/c")
        self.assertTrue(result.success)
        self.assertTrue((self.home / "a" / "b" / "c").is_dir())

    # ===========================================================
    # APP LAUNCHING
    # ===========================================================

    def test_app_list(self):
        result = self.cc.app_list()
        self.assertTrue(result.success)
        self.assertIn("word", result.data["apps"])
        self.assertIn("browser", result.data["apps"])

    def test_app_registry_has_all_platforms(self):
        for app_name, platforms in APP_REGISTRY.items():
            for plat in ("windows", "linux", "mac"):
                self.assertIn(plat, platforms, f"{app_name} missing {plat}")

    @patch("subprocess.Popen")
    def test_app_open_mocked(self, mock_popen):
        result = self.cc.app_open("notepad")
        self.assertTrue(result.success)
        mock_popen.assert_called()

    # ===========================================================
    # WEB SEARCH
    # ===========================================================

    def test_search_engines(self):
        self.assertIn("google", SEARCH_ENGINES)
        self.assertIn("youtube", SEARCH_ENGINES)
        self.assertIn("wikipedia", SEARCH_ENGINES)

    @patch("webbrowser.open")
    def test_web_search_opens_browser(self, mock_open):
        result = self.cc.web_search("cats")
        self.assertTrue(result.success)
        mock_open.assert_called()

    @patch("webbrowser.open")
    def test_web_search_youtube(self, mock_open):
        result = self.cc.web_search("funny cats", engine="youtube")
        self.assertTrue(result.success)
        called_url = mock_open.call_args[0][0]
        self.assertIn("youtube.com", called_url)

    @patch("webbrowser.open")
    def test_web_open(self, mock_open):
        result = self.cc.web_open("https://example.com")
        self.assertTrue(result.success)
        mock_open.assert_called_with("https://example.com")

    @patch("webbrowser.open")
    def test_web_open_adds_https(self, mock_open):
        result = self.cc.web_open("example.com")
        self.assertTrue(result.success)
        mock_open.assert_called_with("https://example.com")

    def test_web_read_no_gateway(self):
        result = self.cc.web_read("https://example.com")
        self.assertFalse(result.success)
        self.assertIn("No gateway", result.error)

    def test_web_read_with_gateway(self):
        gateway = MagicMock()
        gateway.fetch = MagicMock(return_value=MagicMock(
            ok=True, body="<html><body><p>Hello World</p></body></html>",
            refused_reason="", error="",
        ))
        cc = ComputerControl(self.root, gateway=gateway, home_dir=self.home)
        result = cc.web_read("https://example.com")
        self.assertTrue(result.success)
        self.assertIn("Hello World", result.data["content"])

    def test_web_summarize_no_results(self):
        result = self.cc.web_summarize()
        self.assertFalse(result.success)

    def test_web_summarize_with_gateway(self):
        gateway = MagicMock()
        gateway.fetch = MagicMock(return_value=MagicMock(
            ok=True, body="<html><body><p>Article about cats.</p></body></html>",
            refused_reason="", error="",
        ))
        cc = ComputerControl(self.root, gateway=gateway, home_dir=self.home)
        result = cc.web_summarize(urls=["https://example.com/cats"])
        self.assertTrue(result.success)
        self.assertEqual(len(result.data["summaries"]), 1)
        self.assertIn("cats", result.data["summaries"][0]["summary"])

    def test_web_sort_no_results(self):
        result = self.cc.web_sort_results()
        self.assertFalse(result.success)

    def test_web_sort_with_results(self):
        cc = ComputerControl(self.root, home_dir=self.home)
        cc._last_search_results = [
            {"title": "Zebra", "url": "https://z.com"},
            {"title": "Apple", "url": "https://a.com"},
        ]
        result = cc.web_sort_results(by="title")
        self.assertTrue(result.success)
        self.assertEqual(result.data["results"][0]["title"], "Apple")

    @patch("webbrowser.open")
    def test_web_open_results(self, mock_open):
        cc = ComputerControl(self.root, home_dir=self.home)
        cc._last_search_results = [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]
        result = cc.web_open_results(top_n=2)
        self.assertTrue(result.success)
        self.assertEqual(result.data["opened"], 2)

    # ===========================================================
    # MEDIA CONTROL
    # ===========================================================

    @patch("webbrowser.open")
    def test_media_play_query(self, mock_open):
        result = self.cc.media_play("jazz music")
        self.assertTrue(result.success)
        mock_open.assert_called()
        called_url = mock_open.call_args[0][0]
        self.assertIn("youtube.com", called_url)

    def test_media_play_no_query_no_controller(self):
        result = self.cc.media_play()
        self.assertFalse(result.success)

    def test_media_play_with_music_controller(self):
        mc = MagicMock()
        mc.play = MagicMock(return_value={"status": "playing"})
        cc = ComputerControl(self.root, music_controller=mc, home_dir=self.home)
        result = cc.media_play()
        self.assertTrue(result.success)
        mc.play.assert_called_once()

    def test_media_pause_with_music_controller(self):
        mc = MagicMock()
        mc.pause = MagicMock(return_value={"status": "paused"})
        cc = ComputerControl(self.root, music_controller=mc, home_dir=self.home)
        result = cc.media_pause()
        self.assertTrue(result.success)
        mc.pause.assert_called_once()

    def test_media_next_with_music_controller(self):
        mc = MagicMock()
        mc.next = MagicMock(return_value={"status": "next"})
        cc = ComputerControl(self.root, music_controller=mc, home_dir=self.home)
        result = cc.media_next()
        self.assertTrue(result.success)
        mc.next.assert_called_once()

    # ===========================================================
    # DOCUMENT CREATION
    # ===========================================================

    def test_create_document_text(self):
        result = self.cc.create_document("text", "mydoc", "Hello World", open_app=False)
        self.assertTrue(result.success)
        doc_path = self.home / "Documents" / "mydoc.txt"
        self.assertTrue(doc_path.exists())
        self.assertEqual(doc_path.read_text(), "Hello World")

    def test_create_document_essay(self):
        result = self.cc.create_document("essay", "my_essay", "This is an essay.", open_app=False)
        self.assertTrue(result.success)
        doc_path = self.home / "Documents" / "my_essay.docx"
        self.assertTrue(doc_path.exists())

    def test_create_document_spreadsheet(self):
        result = self.cc.create_document("spreadsheet", "data", "a,b,c\n1,2,3", open_app=False)
        self.assertTrue(result.success)
        doc_path = self.home / "Documents" / "data.csv"
        self.assertTrue(doc_path.exists())

    def test_write_essay(self):
        result = self.cc.write_essay("quantum computing", "Quantum computing is...", open_app=False)
        self.assertTrue(result.success)
        # Filename should be derived from topic
        doc_path = self.home / "Documents" / "quantum_computing.docx"
        self.assertTrue(doc_path.exists())

    def test_write_essay_custom_filename(self):
        result = self.cc.write_essay("cats", "Cats are great.", filename="my_cats_essay", open_app=False)
        self.assertTrue(result.success)
        doc_path = self.home / "Documents" / "my_cats_essay.docx"
        self.assertTrue(doc_path.exists())

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_status(self):
        status = self.cc.get_status()
        self.assertIn("platform", status)
        self.assertIn("home_dir", status)
        self.assertIn("has_gateway", status)
        self.assertIn("has_music_controller", status)

    def test_status_with_music_controller(self):
        mc = MagicMock()
        cc = ComputerControl(self.root, music_controller=mc, home_dir=self.home)
        status = cc.get_status()
        self.assertTrue(status["has_music_controller"])

    # ===========================================================
    # HTML PARSING
    # ===========================================================

    def test_html_to_text(self):
        html = "<html><head><style>body{}</style></head><body><p>Hello &amp; welcome</p></body></html>"
        text = self.cc._html_to_text(html)
        self.assertIn("Hello & welcome", text)
        self.assertNotIn("<", text)
        self.assertNotIn("body{}", text)

    def test_html_to_text_removes_scripts(self):
        html = "<html><body><script>alert('xss')</script><p>Safe content</p></body></html>"
        text = self.cc._html_to_text(html)
        self.assertIn("Safe content", text)
        self.assertNotIn("alert", text)

    def test_parse_search_results(self):
        html = """
        <a href="https://example.com/page1">Page 1</a>
        <a href="https://example.com/page2">Page 2</a>
        <a href="https://www.google.com/foo">Google link</a>
        """
        results = self.cc._parse_search_results(html, "google")
        self.assertGreater(len(results), 0)
        # Google links should be filtered
        for r in results:
            self.assertNotIn("google.com", r["url"])


if __name__ == "__main__":
    unittest.main()
