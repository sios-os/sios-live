"""Desktop notifications — system tray, push, visual alerts.

ANUBIS uses notifications to get the Creator's attention:
- System tray notifications (Windows, Linux)
- Terminal notifications (notify-send, msg)
- Visual alerts (screen flash, border)
- Sound alerts (beep, custom sound)
- Email notifications (fallback)

Uses stdlib only. Platform-specific commands for each OS.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Notification priority
PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"

# Notification category
CAT_INFO = "info"
CAT_WARNING = "warning"
CAT_ERROR = "error"
CAT_SUCCESS = "success"
CAT_SECURITY = "security"
CAT_REMINDER = "reminder"
CAT_SYSTEM = "system"


@dataclass
class Notification:
    """A desktop notification."""
    notif_id: str
    title: str = ""
    body: str = ""
    priority: str = PRIORITY_NORMAL
    category: str = CAT_INFO
    timestamp: float = 0.0
    displayed: bool = False
    dismissed: bool = False
    action_taken: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "notif_id": self.notif_id,
            "title": self.title,
            "body": self.body,
            "priority": self.priority,
            "category": self.category,
            "timestamp": self.timestamp,
            "displayed": self.displayed,
            "dismissed": self.dismissed,
            "action_taken": self.action_taken,
        }


class NotificationSystem:
    """Desktop notification system.

    Displays notifications using the platform's native notification
    system. Falls back to terminal output if no GUI is available.
    """

    ACTOR = "anubis.notifications"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        on_notification: Callable[[Notification], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_notification = on_notification

        self._state_dir = self.root / "memory" / "notifications"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "history.jsonl"

        self._history: list[Notification] = []
        self._platform = platform.system().lower()

        # Check available notification tools
        self._notify_send = shutil.which("notify-send")  # Linux
        self._powershell = shutil.which("powershell") or shutil.which("powershell.exe")  # Windows
        self._terminal_notifier = shutil.which("terminal-notifier")  # macOS

    def notify(
        self, title: str, body: str = "",
        priority: str = PRIORITY_NORMAL, category: str = CAT_INFO,
    ) -> Notification:
        """Send a notification."""
        notif_id = hashlib.sha256(
            f"notif:{title}:{time.time()}".encode()
        ).hexdigest()[:16]
        notif = Notification(
            notif_id=notif_id, title=title, body=body,
            priority=priority, category=category,
            timestamp=time.time(),
        )

        # Display via platform-specific method
        notif.displayed = self._display(notif)

        # Record
        self._history.append(notif)
        self._record(notif)

        # Callback
        if self.on_notification:
            try:
                self.on_notification(notif)
            except Exception:
                pass

        self._log("notification.sent", {
            "title": title, "priority": priority, "category": category,
        })

        return notif

    def _display(self, notif: Notification) -> bool:
        """Display notification using platform tools."""
        # Linux: notify-send
        if self._notify_send:
            return self._display_linux(notif)
        # Windows: PowerShell toast
        if self._powershell:
            return self._display_windows(notif)
        # macOS: terminal-notifier
        if self._terminal_notifier:
            return self._display_macos(notif)
        # Fallback: terminal output
        return self._display_terminal(notif)

    def _display_linux(self, notif: Notification) -> bool:
        """Display via notify-send (Linux)."""
        try:
            urgency = "normal"
            if notif.priority == PRIORITY_URGENT:
                urgency = "critical"
            elif notif.priority == PRIORITY_LOW:
                urgency = "low"

            cmd = [self._notify_send, "-u", urgency, notif.title]  # type: ignore
            if notif.body:
                cmd.append(notif.body)

            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _display_windows(self, notif: Notification) -> bool:
        """Display via PowerShell toast notification (Windows)."""
        try:
            # Use Windows toast notification via PowerShell
            script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $text = $template.GetElementsByTagName("text")
            $text.Item(0).AppendChild($template.CreateTextNode("{notif.title}")) | Out-Null
            $text.Item(1).AppendChild($template.CreateTextNode("{notif.body}")) | Out-Null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ANUBIS").Show($toast)
            """
            result = subprocess.run(
                [self._powershell, "-Command", script],  # type: ignore
                capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _display_macos(self, notif: Notification) -> bool:
        """Display via terminal-notifier (macOS)."""
        try:
            cmd = [self._terminal_notifier, "-title", notif.title]  # type: ignore
            if notif.body:
                cmd.extend(["-message", notif.body])
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _display_terminal(self, notif: Notification) -> bool:
        """Fallback: print to terminal."""
        try:
            prefix = ""
            if notif.priority == PRIORITY_URGENT:
                prefix = "[URGENT] "
            elif notif.priority == PRIORITY_HIGH:
                prefix = "[HIGH] "
            elif notif.category == CAT_ERROR:
                prefix = "[ERROR] "
            elif notif.category == CAT_WARNING:
                prefix = "[WARN] "

            print(f"\n{prefix}{notif.title}: {notif.body}\n", file=sys.stderr)
            return True
        except Exception:
            return False

    def alert(self, message: str) -> Notification:
        """Send an urgent alert."""
        return self.notify(
            "ANUBIS Alert", message,
            priority=PRIORITY_URGENT, category=CAT_SECURITY,
        )

    def remind(self, title: str, body: str = "") -> Notification:
        """Send a reminder."""
        return self.notify(
            title, body,
            priority=PRIORITY_NORMAL, category=CAT_REMINDER,
        )

    def info(self, title: str, body: str = "") -> Notification:
        """Send an info notification."""
        return self.notify(
            title, body,
            priority=PRIORITY_LOW, category=CAT_INFO,
        )

    # --------------------------------------------------- queries

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return [n.to_dict() for n in self._history[-limit:]]

    def get_urgent(self) -> list[dict[str, Any]]:
        return [
            n.to_dict() for n in self._history
            if n.priority == PRIORITY_URGENT
        ]

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        return [
            n.to_dict() for n in self._history
            if n.category == category
        ]

    def dismiss(self, notif_id: str) -> bool:
        for n in self._history:
            if n.notif_id == notif_id:
                n.dismissed = True
                return True
        return False

    def get_status(self) -> dict[str, Any]:
        return {
            "platform": self._platform,
            "notify_send": self._notify_send is not None,
            "powershell": self._powershell is not None,
            "terminal_notifier": self._terminal_notifier is not None,
            "total_notifications": len(self._history),
            "urgent_count": len(self.get_urgent()),
        }

    def _record(self, notif: Notification) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(notif.to_dict()) + "\n")
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
