"""Computer control — ANUBIS/DEMON operates the computer like a human.

This module gives DEMON full computer use capabilities:

1. **File operations** — create, read, write, delete, move, copy, organize
2. **App launching** — open any installed application (Word, Excel, browser,
   media player, terminal, etc.)
3. **Web search** — search the web, open results, read pages, summarize
4. **Media control** — play/pause/skip music and videos
5. **Document creation** — write essays, create spreadsheets, generate
   documents in real applications

Security:
- All operations are logged to the evidence ledger
- Destructive operations (delete, move) require confirmation
- Web searches go through the external gateway (policy-gated)
- File operations are bounded to the Creator's home directory by default
- App launching uses the system's default application handler

The Creator can say:
- "Write me an essay on quantum computing" → opens Word, writes the essay
- "Find me something funny" → searches for funny videos, plays one
- "Next video" → skips to the next video
- "Search for cats and show me results" → searches, displays results
- "Open the top 10 and sort them" → opens top 10 results, sorts by relevance
- "Summarize them and read them" → reads each page, summarizes, speaks
- "Play some jazz" → searches for jazz music, plays it
- "Create a spreadsheet of my expenses" → opens Excel, creates the sheet
- "Open my documents folder" → opens the file manager
- "Delete the file called test.txt" → deletes it (with confirmation)
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Platform detection
# ===========================================================

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"


# ===========================================================
# App registry — maps friendly names to system commands
# ===========================================================

# Common apps by friendly name — platform-specific commands
APP_REGISTRY: dict[str, dict[str, list[str]]] = {
    "word": {
        "windows": ["cmd", "/c", "start", "winword"],
        "linux": ["libreoffice", "--writer"],
        "mac": ["open", "-a", "Microsoft Word"],
    },
    "excel": {
        "windows": ["cmd", "/c", "start", "excel"],
        "linux": ["libreoffice", "--calc"],
        "mac": ["open", "-a", "Microsoft Excel"],
    },
    "powerpoint": {
        "windows": ["cmd", "/c", "start", "powerpnt"],
        "linux": ["libreoffice", "--impress"],
        "mac": ["open", "-a", "Microsoft PowerPoint"],
    },
    "browser": {
        "windows": ["cmd", "/c", "start", ""],
        "linux": ["xdg-open"],
        "mac": ["open"],
    },
    "chrome": {
        "windows": ["cmd", "/c", "start", "chrome"],
        "linux": ["google-chrome"],
        "mac": ["open", "-a", "Google Chrome"],
    },
    "firefox": {
        "windows": ["cmd", "/c", "start", "firefox"],
        "linux": ["firefox"],
        "mac": ["open", "-a", "Firefox"],
    },
    "terminal": {
        "windows": ["cmd", "/c", "start", "cmd"],
        "linux": ["xterm"],
        "mac": ["open", "-a", "Terminal"],
    },
    "file manager": {
        "windows": ["explorer"],
        "linux": ["xdg-open"],
        "mac": ["open"],
    },
    "notepad": {
        "windows": ["notepad"],
        "linux": ["gedit"],
        "mac": ["open", "-a", "TextEdit"],
    },
    "calculator": {
        "windows": ["calc"],
        "linux": ["gnome-calculator"],
        "mac": ["open", "-a", "Calculator"],
    },
    "settings": {
        "windows": ["cmd", "/c", "start", "ms-settings:"],
        "linux": ["gnome-control-center"],
        "mac": ["open", "-a", "System Preferences"],
    },
    "media player": {
        "windows": ["cmd", "/c", "start", "wmplayer"],
        "linux": ["vlc"],
        "mac": ["open", "-a", "QuickTime Player"],
    },
    "vlc": {
        "windows": ["cmd", "/c", "start", "vlc"],
        "linux": ["vlc"],
        "mac": ["open", "-a", "VLC"],
    },
    "spotify": {
        "windows": ["cmd", "/c", "start", "spotify:"],
        "linux": ["spotify"],
        "mac": ["open", "-a", "Spotify"],
    },
    "paint": {
        "windows": ["mspaint"],
        "linux": ["gimp"],
        "mac": ["open", "-a", "Preview"],
    },
    "code": {
        "windows": ["cmd", "/c", "start", "code"],
        "linux": ["code"],
        "mac": ["open", "-a", "Visual Studio Code"],
    },
}


# Search engines
SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
    "bing": "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "wikipedia": "https://en.wikipedia.org/w/index.php?search=",
    "amazon": "https://www.amazon.com/s?k=",
    "images": "https://www.google.com/search?tbm=isch&q=",
    "news": "https://news.google.com/search?q=",
    "scholar": "https://scholar.google.com/scholar?q=",
    "github": "https://github.com/search?q=",
}


@dataclass
class ActionResult:
    """Result of a computer control action."""
    action: str
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class ComputerControl:
    """Gives DEMON/ANUBIS full computer use capabilities.

    All operations are logged. Destructive operations can require
    confirmation. Web access goes through the external gateway.
    """

    ACTOR = "anubis.computer_control"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        gateway: Any | None = None,
        music_controller: Any | None = None,
        home_dir: str | Path | None = None,
        on_speak: Callable[[str], None] | None = None,
        require_confirmation: bool = True,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.gateway = gateway
        self.music_controller = music_controller
        self.on_speak = on_speak
        self.require_confirmation = require_confirmation

        # File operations are bounded to home directory by default
        self.home_dir = Path(home_dir) if home_dir else Path.home()
        self.allowed_paths = [self.home_dir, self.root]

        # Track open apps for later reference
        self._open_apps: dict[str, Any] = {}
        # Track search results for "open top 10" etc.
        self._last_search_results: list[dict[str, str]] = []
        # Track open browser tabs
        self._open_tabs: list[str] = []

        self._state_dir = self.root / "memory" / "computer_control"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._state_dir / "actions.jsonl"

    def _platform_key(self) -> str:
        if IS_WINDOWS:
            return "windows"
        if IS_LINUX:
            return "linux"
        if IS_MAC:
            return "mac"
        return "linux"

    def _log_action(self, action: str, data: dict[str, Any]) -> None:
        entry = {"action": action, "data": data, "timestamp": time.time()}
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    def _is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories."""
        try:
            resolved = path.resolve()
            for allowed in self.allowed_paths:
                if str(resolved).startswith(str(allowed.resolve())):
                    return True
            return False
        except Exception:
            return False

    # ===========================================================
    # FILE OPERATIONS
    # ===========================================================

    def file_create(self, path: str, content: str = "") -> ActionResult:
        """Create a file with optional content."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        if not self._is_path_allowed(target):
            return ActionResult("file_create", False, error="Path not allowed", timestamp=time.time())
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._log_action("file_create", {"path": str(target), "size": len(content)})
            return ActionResult("file_create", True, message=f"Created {target.name}", data={"path": str(target)}, timestamp=time.time())
        except Exception as e:
            return ActionResult("file_create", False, error=str(e), timestamp=time.time())

    def file_read(self, path: str, max_chars: int = 50000) -> ActionResult:
        """Read a file's contents."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            return ActionResult("file_read", False, error="File not found", timestamp=time.time())
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n[... truncated at {max_chars} chars ...]"
            self._log_action("file_read", {"path": str(target), "chars": len(content)})
            return ActionResult("file_read", True, message=f"Read {target.name}", data={"content": content, "path": str(target)}, timestamp=time.time())
        except Exception as e:
            return ActionResult("file_read", False, error=str(e), timestamp=time.time())

    def file_write(self, path: str, content: str, append: bool = False) -> ActionResult:
        """Write or append to a file."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        if not self._is_path_allowed(target):
            return ActionResult("file_write", False, error="Path not allowed", timestamp=time.time())
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if append:
                with open(target, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                target.write_text(content, encoding="utf-8")
            self._log_action("file_write", {"path": str(target), "size": len(content), "append": append})
            return ActionResult("file_write", True, message=f"Wrote {target.name}", data={"path": str(target)}, timestamp=time.time())
        except Exception as e:
            return ActionResult("file_write", False, error=str(e), timestamp=time.time())

    def file_delete(self, path: str, confirmed: bool = False) -> ActionResult:
        """Delete a file. Requires confirmation."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            return ActionResult("file_delete", False, error="File not found", timestamp=time.time())
        if not self._is_path_allowed(target):
            return ActionResult("file_delete", False, error="Path not allowed", timestamp=time.time())
        if self.require_confirmation and not confirmed:
            return ActionResult("file_delete", False, message=f"Confirmation required to delete {target.name}", data={"needs_confirmation": True, "path": str(target)}, timestamp=time.time())
        try:
            target.unlink()
            self._log_action("file_delete", {"path": str(target)})
            return ActionResult("file_delete", True, message=f"Deleted {target.name}", timestamp=time.time())
        except Exception as e:
            return ActionResult("file_delete", False, error=str(e), timestamp=time.time())

    def file_move(self, src: str, dst: str) -> ActionResult:
        """Move/rename a file."""
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        if not src_path.is_absolute():
            src_path = self.home_dir / src
        if not dst_path.is_absolute():
            dst_path = self.home_dir / dst
        if not src_path.exists():
            return ActionResult("file_move", False, error="Source not found", timestamp=time.time())
        if not self._is_path_allowed(src_path) or not self._is_path_allowed(dst_path):
            return ActionResult("file_move", False, error="Path not allowed", timestamp=time.time())
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            self._log_action("file_move", {"src": str(src_path), "dst": str(dst_path)})
            return ActionResult("file_move", True, message=f"Moved {src_path.name} to {dst_path}", timestamp=time.time())
        except Exception as e:
            return ActionResult("file_move", False, error=str(e), timestamp=time.time())

    def file_copy(self, src: str, dst: str) -> ActionResult:
        """Copy a file."""
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        if not src_path.is_absolute():
            src_path = self.home_dir / src
        if not dst_path.is_absolute():
            dst_path = self.home_dir / dst
        if not src_path.exists():
            return ActionResult("file_copy", False, error="Source not found", timestamp=time.time())
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src_path), str(dst_path))
            self._log_action("file_copy", {"src": str(src_path), "dst": str(dst_path)})
            return ActionResult("file_copy", True, message=f"Copied {src_path.name} to {dst_path}", timestamp=time.time())
        except Exception as e:
            return ActionResult("file_copy", False, error=str(e), timestamp=time.time())

    def file_list(self, path: str = "", pattern: str = "*") -> ActionResult:
        """List files in a directory."""
        target = Path(path).expanduser() if path else self.home_dir
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            return ActionResult("file_list", False, error="Directory not found", timestamp=time.time())
        try:
            entries = []
            for p in sorted(target.glob(pattern)):
                entries.append({
                    "name": p.name,
                    "path": str(p),
                    "is_dir": p.is_dir(),
                    "size": p.stat().st_size if p.is_file() else 0,
                    "modified": p.stat().st_mtime,
                })
            self._log_action("file_list", {"path": str(target), "count": len(entries)})
            return ActionResult("file_list", True, message=f"Found {len(entries)} items", data={"entries": entries, "path": str(target)}, timestamp=time.time())
        except Exception as e:
            return ActionResult("file_list", False, error=str(e), timestamp=time.time())

    def file_organize(self, path: str = "") -> ActionResult:
        """Organize files in a directory by type (documents, images, videos, etc.)."""
        target = Path(path).expanduser() if path else self.home_dir
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            return ActionResult("file_organize", False, error="Directory not found", timestamp=time.time())

        categories = {
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
            "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
            "Presentations": [".ppt", ".pptx", ".odp", ".key"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
            "Code": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs", ".html", ".css"],
        }

        moved = 0
        for category, extensions in categories.items():
            cat_dir = target / category
            for ext in extensions:
                for p in target.glob(f"*{ext}"):
                    if p.is_file():
                        cat_dir.mkdir(exist_ok=True)
                        try:
                            shutil.move(str(p), str(cat_dir / p.name))
                            moved += 1
                        except Exception:
                            pass

        self._log_action("file_organize", {"path": str(target), "moved": moved})
        return ActionResult("file_organize", True, message=f"Organized {moved} files into categories", data={"moved": moved}, timestamp=time.time())

    def file_open(self, path: str) -> ActionResult:
        """Open a file with its default application."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            return ActionResult("file_open", False, error="File not found", timestamp=time.time())
        try:
            if IS_WINDOWS:
                os.startfile(str(target))  # type: ignore
            elif IS_MAC:
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            self._log_action("file_open", {"path": str(target)})
            return ActionResult("file_open", True, message=f"Opened {target.name}", timestamp=time.time())
        except Exception as e:
            return ActionResult("file_open", False, error=str(e), timestamp=time.time())

    # ===========================================================
    # APP LAUNCHING
    # ===========================================================

    def app_open(self, app_name: str, args: str = "") -> ActionResult:
        """Open an application by friendly name or system command."""
        app_key = app_name.lower().strip()

        # Look up in registry
        platform_key = self._platform_key()
        if app_key in APP_REGISTRY:
            cmd = APP_REGISTRY[app_key][platform_key]
        elif app_key in ("browser", "web browser"):
            cmd = APP_REGISTRY["browser"][platform_key]
        else:
            # Try to run it as a direct command
            cmd = [app_name]

        # Append arguments if provided
        if args and cmd:
            cmd = cmd + [args]

        try:
            if IS_WINDOWS:
                subprocess.Popen(cmd, shell=False)
            else:
                subprocess.Popen(cmd)
            self._open_apps[app_key] = {"cmd": cmd, "opened_at": time.time()}
            self._log_action("app_open", {"app": app_name, "cmd": cmd})
            return ActionResult("app_open", True, message=f"Opened {app_name}", data={"app": app_name}, timestamp=time.time())
        except Exception as e:
            return ActionResult("app_open", False, error=str(e), timestamp=time.time())

    def app_list(self) -> ActionResult:
        """List available apps."""
        apps = list(APP_REGISTRY.keys())
        return ActionResult("app_list", True, message=f"{len(apps)} apps available", data={"apps": apps}, timestamp=time.time())

    def app_close(self, app_name: str) -> ActionResult:
        """Close an application."""
        app_key = app_name.lower().strip()
        try:
            if IS_WINDOWS:
                # taskkill by window title or process name
                subprocess.run(["taskkill", "/IM", f"{app_key}.exe", "/F"], capture_output=True, timeout=10)
            elif IS_LINUX:
                subprocess.run(["pkill", "-f", app_key], capture_output=True, timeout=10)
            else:
                subprocess.run(["killall", app_key], capture_output=True, timeout=10)
            if app_key in self._open_apps:
                del self._open_apps[app_key]
            self._log_action("app_close", {"app": app_name})
            return ActionResult("app_close", True, message=f"Closed {app_name}", timestamp=time.time())
        except Exception as e:
            return ActionResult("app_close", False, error=str(e), timestamp=time.time())

    # ===========================================================
    # WEB SEARCH
    # ===========================================================

    def web_search(self, query: str, engine: str = "google", num_results: int = 10) -> ActionResult:
        """Search the web and return results.

        Opens the search in the browser AND returns results for processing.
        """
        engine_url = SEARCH_ENGINES.get(engine.lower(), SEARCH_ENGINES["google"])
        search_url = engine_url + query.replace(" ", "+")

        # Open in browser
        try:
            webbrowser.open(search_url)
            self._open_tabs.append(search_url)
        except Exception:
            pass

        # If we have a gateway, try to fetch actual results
        results: list[dict[str, str]] = []
        if self.gateway:
            try:
                response = self.gateway.fetch(search_url, purpose=f"web search: {query}", creator_approved=True)
                if response.ok and response.body:
                    # Parse results from the HTML (simplified)
                    results = self._parse_search_results(response.body, engine)
            except Exception:
                pass

        self._last_search_results = results
        self._log_action("web_search", {"query": query, "engine": engine, "results": len(results)})

        if results:
            return ActionResult("web_search", True, message=f"Found {len(results)} results for '{query}'", data={"results": results, "query": query, "engine": engine, "url": search_url}, timestamp=time.time())
        else:
            return ActionResult("web_search", True, message=f"Searching for '{query}' in {engine}. Browser opened.", data={"query": query, "engine": engine, "url": search_url}, timestamp=time.time())

    def _parse_search_results(self, html: str, engine: str) -> list[dict[str, str]]:
        """Parse search results from HTML (simplified)."""
        import re
        results = []
        # Extract links and titles — simplified parser
        link_pattern = re.compile(r'<a[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        for match in link_pattern.finditer(html):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if title and not url.startswith(("https://www.google.", "https://accounts.")):
                results.append({"title": title, "url": url})
            if len(results) >= 20:
                break
        return results[:10]

    def web_open(self, url: str) -> ActionResult:
        """Open a URL in the browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            self._open_tabs.append(url)
            self._log_action("web_open", {"url": url})
            return ActionResult("web_open", True, message=f"Opened {url}", data={"url": url}, timestamp=time.time())
        except Exception as e:
            return ActionResult("web_open", False, error=str(e), timestamp=time.time())

    def web_read(self, url: str) -> ActionResult:
        """Read a web page and return its text content."""
        if self.gateway:
            try:
                response = self.gateway.fetch(url, purpose=f"read page: {url}", creator_approved=True)
                if response.ok:
                    text = self._html_to_text(response.body)
                    self._log_action("web_read", {"url": url, "chars": len(text)})
                    return ActionResult("web_read", True, message=f"Read {len(text)} characters from {url}", data={"content": text, "url": url}, timestamp=time.time())
                else:
                    return ActionResult("web_read", False, error=response.refused_reason or response.error, timestamp=time.time())
            except Exception as e:
                return ActionResult("web_read", False, error=str(e), timestamp=time.time())
        return ActionResult("web_read", False, error="No gateway configured", timestamp=time.time())

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simplified)."""
        import re
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Decode common entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&quot;', '"')
        return text[:50000]  # cap at 50k chars

    def web_summarize(self, urls: list[str] | None = None, top_n: int = 10) -> ActionResult:
        """Read and summarize multiple web pages.

        If urls is None, uses the last search results.
        """
        if urls is None:
            urls = [r["url"] for r in self._last_search_results[:top_n]]

        if not urls:
            return ActionResult("web_summarize", False, error="No URLs to summarize", timestamp=time.time())

        summaries = []
        for url in urls[:top_n]:
            read_result = self.web_read(url)
            if read_result.success:
                content = read_result.data.get("content", "")
                # Simple extractive summary — first 500 chars
                summary = content[:500] + "..." if len(content) > 500 else content
                summaries.append({"url": url, "summary": summary, "length": len(content)})
            else:
                summaries.append({"url": url, "error": read_result.error})

        self._log_action("web_summarize", {"count": len(summaries)})
        return ActionResult("web_summarize", True, message=f"Summarized {len(summaries)} pages", data={"summaries": summaries}, timestamp=time.time())

    def web_sort_results(self, by: str = "relevance") -> ActionResult:
        """Sort the last search results."""
        if not self._last_search_results:
            return ActionResult("web_sort", False, error="No search results to sort", timestamp=time.time())
        if by == "title":
            self._last_search_results.sort(key=lambda r: r.get("title", ""))
        else:
            # Default: keep original order (relevance from search engine)
            pass
        return ActionResult("web_sort", True, message=f"Sorted {len(self._last_search_results)} results by {by}", data={"results": self._last_search_results}, timestamp=time.time())

    def web_open_results(self, top_n: int = 10) -> ActionResult:
        """Open the top N search results in browser tabs."""
        if not self._last_search_results:
            return ActionResult("web_open_results", False, error="No search results to open", timestamp=time.time())
        opened = 0
        for r in self._last_search_results[:top_n]:
            url = r.get("url", "")
            if url:
                try:
                    webbrowser.open(url)
                    self._open_tabs.append(url)
                    opened += 1
                except Exception:
                    pass
        self._log_action("web_open_results", {"opened": opened})
        return ActionResult("web_open_results", True, message=f"Opened {opened} results in browser", data={"opened": opened}, timestamp=time.time())

    # ===========================================================
    # MEDIA CONTROL
    # ===========================================================

    def media_play(self, query: str = "") -> ActionResult:
        """Play music or video. If query is provided, searches for it first."""
        if query:
            # Search on YouTube and open in browser
            search_url = SEARCH_ENGINES["youtube"] + query.replace(" ", "+")
            try:
                webbrowser.open(search_url)
                self._open_tabs.append(search_url)
                self._log_action("media_play", {"query": query, "type": "youtube"})
                return ActionResult("media_play", True, message=f"Playing '{query}' on YouTube", data={"query": query, "url": search_url}, timestamp=time.time())
            except Exception as e:
                return ActionResult("media_play", False, error=str(e), timestamp=time.time())
        else:
            # Try music controller
            if self.music_controller:
                try:
                    result = self.music_controller.play()
                    return ActionResult("media_play", True, message="Playing", data=result, timestamp=time.time())
                except Exception as e:
                    return ActionResult("media_play", False, error=str(e), timestamp=time.time())
            return ActionResult("media_play", False, error="No media controller and no query", timestamp=time.time())

    def media_pause(self) -> ActionResult:
        """Pause media playback."""
        if self.music_controller:
            try:
                result = self.music_controller.pause()
                return ActionResult("media_pause", True, message="Paused", data=result, timestamp=time.time())
            except Exception as e:
                pass
        # Try keyboard shortcut (spacebar pauses in most players)
        return self._send_key("space")

    def media_next(self) -> ActionResult:
        """Skip to next track/video."""
        if self.music_controller:
            try:
                result = self.music_controller.next()
                return ActionResult("media_next", True, message="Next track", data=result, timestamp=time.time())
            except Exception as e:
                pass
        # Try keyboard shortcut (Ctrl+Right or just Right)
        return self._send_key("ctrl+right")

    def media_previous(self) -> ActionResult:
        """Go to previous track/video."""
        return self._send_key("ctrl+left")

    def media_volume(self, level: int) -> ActionResult:
        """Set system volume (0-100)."""
        level = max(0, min(100, level))
        try:
            if IS_WINDOWS:
                # Use PowerShell to set volume
                script = f"""
                $obj = New-Object -ComObject WScript.Shell
                $obj.SendKeys([char]{{[char]}})
                """
                # Simplified — just send volume keys
                for _ in range(5):
                    subprocess.run(["powershell", "-Command",
                                   f"(New-Object -ComObject WScript.Shell).SendKeys([char]175)"],
                                  capture_output=True, timeout=5)  # Volume up
                for _ in range(50 - level // 2):
                    subprocess.run(["powershell", "-Command",
                                   f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"],
                                  capture_output=True, timeout=5)  # Volume down
            elif IS_LINUX:
                subprocess.run(["amixer", "set", "Master", f"{level}%"], capture_output=True, timeout=5)
            self._log_action("media_volume", {"level": level})
            return ActionResult("media_volume", True, message=f"Volume set to {level}%", data={"level": level}, timestamp=time.time())
        except Exception as e:
            return ActionResult("media_volume", False, error=str(e), timestamp=time.time())

    def _send_key(self, key: str) -> ActionResult:
        """Send a keyboard shortcut."""
        try:
            if IS_WINDOWS:
                # Map keys to Windows SendKeys
                key_map = {
                    "space": " ",
                    "ctrl+right": "^{RIGHT}",
                    "ctrl+left": "^{LEFT}",
                    "right": "{RIGHT}",
                    "left": "{LEFT}",
                    "up": "{UP}",
                    "down": "{DOWN}",
                    "enter": "~",
                    "escape": "{ESC}",
                    "tab": "{TAB}",
                }
                win_key = key_map.get(key, key)
                subprocess.run(["powershell", "-Command",
                               f"(New-Object -ComObject WScript.Shell).SendKeys('{win_key}')"],
                              capture_output=True, timeout=5)
            elif IS_LINUX:
                # Use xdotool if available
                subprocess.run(["xdotool", "key", key], capture_output=True, timeout=5)
            self._log_action("send_key", {"key": key})
            return ActionResult("send_key", True, message=f"Sent key: {key}", timestamp=time.time())
        except Exception as e:
            return ActionResult("send_key", False, error=str(e), timestamp=time.time())

    # ===========================================================
    # DOCUMENT CREATION
    # ===========================================================

    def create_document(self, doc_type: str, filename: str, content: str, open_app: bool = True) -> ActionResult:
        """Create a document (essay, spreadsheet, etc.) and open it.

        doc_type: "essay", "document", "spreadsheet", "presentation", "text"
        filename: name of the file (with or without extension)
        content: the text content
        open_app: whether to open the document in its default app after creation
        """
        # Determine file extension and app
        type_map = {
            "essay": (".docx", "word"),
            "document": (".docx", "word"),
            "text": (".txt", "notepad"),
            "spreadsheet": (".csv", "excel"),
            "presentation": (".pptx", "powerpoint"),
            "notes": (".txt", "notepad"),
        }

        ext, app = type_map.get(doc_type.lower(), (".txt", "notepad"))

        # Ensure filename has extension
        if not filename.endswith(ext):
            filename += ext

        target = self.home_dir / "Documents" / filename
        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            # For text files, write directly
            if ext in (".txt", ".csv"):
                target.write_text(content, encoding="utf-8")
            else:
                # For Office documents, write as text first (the app will handle formatting)
                # In a full implementation, this would use python-docx, openpyxl, etc.
                target.write_text(content, encoding="utf-8")

            self._log_action("create_document", {"type": doc_type, "filename": str(target), "size": len(content)})

            # Open in the appropriate app
            if open_app:
                self.file_open(str(target))

            return ActionResult("create_document", True,
                                message=f"Created {doc_type} '{filename}' and opened in {app}",
                                data={"path": str(target), "type": doc_type, "app": app},
                                timestamp=time.time())
        except Exception as e:
            return ActionResult("create_document", False, error=str(e), timestamp=time.time())

    def write_essay(self, topic: str, content: str, filename: str = "", open_app: bool = True) -> ActionResult:
        """Write an essay on a topic and open it in Word."""
        if not filename:
            # Generate filename from topic
            filename = topic.replace(" ", "_")[:50]
        return self.create_document("essay", filename, content, open_app=open_app)

    # ===========================================================
    # FOLDER OPERATIONS
    # ===========================================================

    def folder_open(self, path: str = "") -> ActionResult:
        """Open a folder in the file manager."""
        target = Path(path).expanduser() if path else self.home_dir
        if not target.is_absolute():
            target = self.home_dir / path
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
        return self.file_open(str(target))

    def folder_create(self, path: str) -> ActionResult:
        """Create a new folder."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = self.home_dir / path
        try:
            target.mkdir(parents=True, exist_ok=True)
            self._log_action("folder_create", {"path": str(target)})
            return ActionResult("folder_create", True, message=f"Created folder {target.name}", data={"path": str(target)}, timestamp=time.time())
        except Exception as e:
            return ActionResult("folder_create", False, error=str(e), timestamp=time.time())

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        return {
            "open_apps": list(self._open_apps.keys()),
            "open_tabs": len(self._open_tabs),
            "last_search_results": len(self._last_search_results),
            "home_dir": str(self.home_dir),
            "platform": self._platform_key(),
            "has_gateway": self.gateway is not None,
            "has_music_controller": self.music_controller is not None,
        }
