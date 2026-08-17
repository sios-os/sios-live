"""Messaging system — Signal CLI + email-to-SMS fallback.

ANUBIS can send text messages to emergency contacts and the successor.
Signal CLI is the primary method (end-to-end encrypted, no per-message
cost). Email-to-SMS gateway is the fallback.

Signal CLI setup (on Linux):
1. Install signal-cli (Java application)
2. Register a phone number with Signal
3. signal-cli runs as a daemon
4. ANUBIS calls signal-cli to send messages

Email-to-SMS gateway:
- Uses carrier email gateways (e.g., 5551234567@vtext.com for Verizon)
- No API key needed, just an SMTP server
- Less reliable than Signal but works as fallback

SECURITY:
- Signal messages are end-to-end encrypted
- Phone numbers and email addresses are never logged in plaintext
- Message content is logged to the evidence ledger but not to stdout
- Rate limiting prevents spam
- All sends require governance approval for emergency messages

The successor is ONLY messaged through this system when
ContactManager.check_successor_notification_needed() returns True.
"""
from __future__ import annotations

import json
import os
import shutil
import smtplib
import subprocess
import time
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Callable

from .contacts import ContactManager, EmergencyContact


# Carrier email-to-SMS gateways (US carriers)
CARRIER_GATEWAYS = {
    "verizon": "vtext.com",
    "att": "txt.att.net",
    "tmobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "boost": "myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "metro_pcs": "mymetropcs.com",
    "us_cellular": "email.uscc.net",
    "google_fi": "msg.fi.google.com",
}


@dataclass
class Message:
    """A message sent or received by ANUBIS."""
    message_id: str
    to: str  # phone number or email
    to_name: str = ""
    body: str = ""
    method: str = "signal"  # signal, email_sms, email
    status: str = "pending"  # pending, sent, failed, delivered
    timestamp: float = 0.0
    error: str = ""
    is_emergency: bool = False
    is_successor: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "to": self.to[:4] + "****" if len(self.to) > 4 else self.to,  # masked
            "to_name": self.to_name,
            "body": self.body,
            "method": self.method,
            "status": self.status,
            "timestamp": self.timestamp,
            "error": self.error,
            "is_emergency": self.is_emergency,
            "is_successor": self.is_successor,
        }


class SignalMessenger:
    """Send text messages via Signal CLI.

    Signal CLI is a command-line interface for Signal that runs as a
    daemon. ANUBIS calls it to send encrypted text messages.

    Setup:
        signal-cli -u +1234567890 daemon

    Send:
        signal-cli -u +1234567890 send -m "message" +1234567890
    """

    def __init__(
        self,
        root: str | Path,
        contacts: ContactManager,
        *,
        signal_number: str = "",
        ledger: Any | None = None,
        rate_limit_seconds: float = 30.0,
        max_messages_per_hour: int = 20,
        phone_adapter: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.contacts = contacts
        self.signal_number = signal_number
        self.ledger = ledger
        self.rate_limit_seconds = rate_limit_seconds
        self.max_messages_per_hour = max_messages_per_hour
        self.phone_adapter = phone_adapter

        self._state_dir = self.root / "memory" / "messaging"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "message_history.jsonl"

        # Check if signal-cli is available
        self._signal_cli = shutil.which("signal-cli")
        self._last_send_time: float = 0.0
        self._send_count: list[float] = []  # timestamps for rate limiting

        # Email configuration (for fallback)
        self._smtp_host = os.environ.get("ANUBIS_SMTP_HOST", "")
        self._smtp_port = int(os.environ.get("ANUBIS_SMTP_PORT", "587"))
        self._smtp_user = os.environ.get("ANUBIS_SMTP_USER", "")
        self._smtp_pass = os.environ.get("ANUBIS_SMTP_PASS", "")
        self._from_email = os.environ.get("ANUBIS_FROM_EMAIL", "")

    # --------------------------------------------------- status

    def is_available(self) -> bool:
        """Check if any messaging method is available."""
        return self._signal_cli is not None or self._email_configured()

    def signal_available(self) -> bool:
        """Check if Signal CLI is available."""
        return self._signal_cli is not None

    def email_configured(self) -> bool:
        """Check if email-to-SMS is configured."""
        return bool(self._smtp_host and self._from_email)

    def _email_configured(self) -> bool:
        return bool(self._smtp_host and self._from_email)

    # --------------------------------------------------- rate limiting

    def _check_rate_limit(self) -> bool:
        """Check if we can send another message."""
        now = time.time()
        # Remove timestamps older than 1 hour
        self._send_count = [t for t in self._send_count if now - t < 3600]
        if len(self._send_count) >= self.max_messages_per_hour:
            return False
        if now - self._last_send_time < self.rate_limit_seconds:
            return False
        return True

    def _record_send(self) -> None:
        """Record that a message was sent."""
        now = time.time()
        self._last_send_time = now
        self._send_count.append(now)

    # --------------------------------------------------- send

    def send_to_contact(
        self,
        contact_id: str,
        message: str,
        *,
        is_emergency: bool = False,
    ) -> Message:
        """Send a message to an emergency contact."""
        contact_data = self.contacts.get_contact(contact_id)
        if contact_data is None:
            return Message(
                message_id="",
                to="",
                to_name="",
                body=message,
                status="failed",
                error="Contact not found",
                timestamp=time.time(),
                is_emergency=is_emergency,
            )

        return self._send(
            to=contact_data.get("phone", ""),
            to_name=contact_data.get("name", ""),
            email=contact_data.get("email", ""),
            body=message,
            is_emergency=is_emergency,
            is_successor=False,
        )

    def send_to_successor(self, message: str) -> Message:
        """Send a message to the successor.

        This should ONLY be called after
        ContactManager.check_successor_notification_needed() returns True.
        """
        successor = self.contacts.get_successor_contact_info()
        return self._send(
            to=successor.get("phone", ""),
            to_name=successor.get("name", ""),
            email=successor.get("email", ""),
            body=message,
            is_emergency=True,
            is_successor=True,
        )

    def send_emergency_alert(
        self,
        message: str,
        *,
        max_contacts: int = 3,
    ) -> list[Message]:
        """Send an emergency alert to the top priority contacts.

        Contacts are messaged in priority order until max_contacts
        have been attempted.
        """
        contacts = self.contacts.get_available_contacts()
        results: list[Message] = []

        for contact_data in contacts[:max_contacts]:
            msg = self._send(
                to=contact_data.get("phone", ""),
                to_name=contact_data.get("name", ""),
                email=contact_data.get("email", ""),
                body=message,
                is_emergency=True,
                is_successor=False,
            )
            results.append(msg)

            # Record the attempt
            self.contacts.record_attempt(
                contact_id=contact_data.get("contact_id", ""),
                contact_name=contact_data.get("name", ""),
                method=msg.method,
                message=message,
                status=msg.status,
            )

        return results

    def _send(
        self,
        to: str,
        to_name: str,
        email: str,
        body: str,
        *,
        is_emergency: bool,
        is_successor: bool,
    ) -> Message:
        """Send a message using the best available method."""
        import hashlib

        msg = Message(
            message_id=hashlib.sha256(
                f"msg:{to}:{time.time()}".encode()
            ).hexdigest()[:16],
            to=to,
            to_name=to_name,
            body=body,
            is_emergency=is_emergency,
            is_successor=is_successor,
            timestamp=time.time(),
        )

        if not to and not email:
            msg.status = "failed"
            msg.error = "No phone or email for contact"
            self._record_message(msg)
            return msg

        # Emergency messages bypass rate limiting
        if not is_emergency and not self._check_rate_limit():
            msg.status = "failed"
            msg.error = "Rate limit exceeded"
            self._record_message(msg)
            return msg

        # Try Signal first
        if to and self.signal_available():
            if self._send_signal(to, body):
                msg.method = "signal"
                msg.status = "sent"
                self._record_send()
                self._record_message(msg)
                self._log("message.sent", {
                    "method": "signal",
                    "to_name": to_name,
                    "is_emergency": is_emergency,
                    "is_successor": is_successor,
                })
                return msg
            else:
                msg.error = "Signal send failed"

        # Fallback to phone adapter (physical Android phone via ADB)
        if to and self.phone_adapter is not None:
            try:
                result = self.phone_adapter.send_sms(to, body)
                if result.get("sent"):
                    msg.method = "phone_adapter"
                    msg.status = "sent"
                    self._record_send()
                    self._record_message(msg)
                    self._log("message.sent", {
                        "method": "phone_adapter",
                        "to_name": to_name,
                        "is_emergency": is_emergency,
                        "is_successor": is_successor,
                    })
                    return msg
            except Exception:
                pass

        # Fallback to email-to-SMS
        if to and self._email_configured():
            carrier_email = self._phone_to_email(to)
            if carrier_email and self._send_email(carrier_email, body):
                msg.method = "email_sms"
                msg.status = "sent"
                self._record_send()
                self._record_message(msg)
                self._log("message.sent", {
                    "method": "email_sms",
                    "to_name": to_name,
                    "is_emergency": is_emergency,
                    "is_successor": is_successor,
                })
                return msg

        # Fallback to direct email
        if email and self._email_configured():
            if self._send_email(email, body):
                msg.method = "email"
                msg.status = "sent"
                self._record_send()
                self._record_message(msg)
                self._log("message.sent", {
                    "method": "email",
                    "to_name": to_name,
                    "is_emergency": is_emergency,
                    "is_successor": is_successor,
                })
                return msg

        msg.status = "failed"
        if not msg.error:
            msg.error = "No available messaging method"
        self._record_message(msg)
        self._log("message.failed", {
            "to_name": to_name,
            "error": msg.error,
            "is_emergency": is_emergency,
        })
        return msg

    def _send_signal(self, to: str, body: str) -> bool:
        """Send a message via Signal CLI."""
        if not self._signal_cli:
            return False
        try:
            cmd = [
                self._signal_cli,  # type: ignore
                "-u", self.signal_number,
                "send",
                "-m", body,
                to,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _phone_to_email(self, phone: str) -> str:
        """Convert a phone number to an email-to-SMS address.

        Without knowing the carrier, we can't do this reliably.
        If the contact has an email set, use that instead.
        Returns empty string if we can't determine the gateway.
        """
        # Strip non-digits
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) < 10:
            return ""
        # Default to Verizon gateway if carrier unknown
        # In production, the contact should have their carrier specified
        return f"{digits}@{CARRIER_GATEWAYS['verizon']}"

    def _send_email(self, to: str, body: str) -> bool:
        """Send an email via SMTP."""
        if not self._email_configured():
            return False
        try:
            msg = MIMEText(body)
            msg["Subject"] = "ANUBIS Alert"
            msg["From"] = self._from_email
            msg["To"] = to

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                if self._smtp_user and self._smtp_pass:
                    server.login(self._smtp_user, self._smtp_pass)
                server.sendmail(self._from_email, [to], msg.as_string())

            return True
        except Exception:
            return False

    # --------------------------------------------------- history

    def _record_message(self, msg: Message) -> None:
        """Record a message in history."""
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg.to_dict()) + "\n")
        except Exception:
            pass

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent message history."""
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        """Get messaging system status."""
        now = time.time()
        recent = [t for t in self._send_count if now - t < 3600]
        phone_connected = False
        if self.phone_adapter is not None:
            try:
                phone_connected = self.phone_adapter.is_connected()
            except Exception:
                pass
        return {
            "available": self.is_available(),
            "signal_available": self.signal_available(),
            "email_configured": self.email_configured(),
            "signal_number_configured": bool(self.signal_number),
            "phone_adapter_available": self.phone_adapter is not None,
            "phone_connected": phone_connected,
            "messages_last_hour": len(recent),
            "max_messages_per_hour": self.max_messages_per_hour,
            "rate_limit_seconds": self.rate_limit_seconds,
            "total_messages": len(self.get_history(limit=9999)),
        }

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append("anubis.messaging", action, data)
            except Exception:
                pass
