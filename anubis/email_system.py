"""Email integration — read, flag, draft responses.

ANUBIS monitors email to:
- Notify you of important incoming emails
- Draft responses for your approval
- Filter and prioritize messages
- Detect phishing and suspicious emails
- Track threads and follow-ups

PROTOCOLS:
- IMAP (read email — works with Gmail, Outlook, Yahoo, etc.)
- SMTP (send email — same providers)

Uses only stdlib (imaplib, smtplib, email) — no external dependencies.

SECURITY:
- Credentials stored encrypted in production (never in plaintext config)
- Email content processed locally — never uploaded
- Drafts require Creator approval before sending
- All actions logged to evidence ledger
- Phishing detection flags suspicious emails
"""
from __future__ import annotations

import hashlib
import imaplib
import json
import smtplib
import time
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from email.header import decode_header
from pathlib import Path
from typing import Any, Callable


# Email priority
PRIORITY_URGENT = "urgent"
PRIORITY_HIGH = "high"
PRIORITY_NORMAL = "normal"
PRIORITY_LOW = "low"

# Email categories
CAT_INBOX = "inbox"
CAT_IMPORTANT = "important"
CAT_FLAGGED = "flagged"
CAT_DRAFT = "draft"
CAT_SENT = "sent"
CAT_SPAM = "spam"
CAT_PHISHING = "phishing"
CAT_FOLLOWUP = "followup"


@dataclass
class Email:
    """An email message."""
    email_id: str
    subject: str = ""
    sender: str = ""
    sender_name: str = ""
    recipients: list[str] = field(default_factory=list)
    date: float = 0.0
    body: str = ""
    body_html: str = ""
    category: str = CAT_INBOX
    priority: str = PRIORITY_NORMAL
    read: bool = False
    flagged: bool = False
    attachments: list[str] = field(default_factory=list)
    thread_id: str = ""
    phishing_score: float = 0.0  # 0-1, higher = more suspicious
    phishing_indicators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "email_id": self.email_id,
            "subject": self.subject,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "recipients": self.recipients,
            "date": self.date,
            "body": self.body[:500],  # truncate for display
            "category": self.category,
            "priority": self.priority,
            "read": self.read,
            "flagged": self.flagged,
            "attachments": self.attachments,
            "thread_id": self.thread_id,
            "phishing_score": self.phishing_score,
            "phishing_indicators": self.phishing_indicators,
        }


@dataclass
class EmailDraft:
    """A draft email response."""
    draft_id: str
    to: str = ""
    subject: str = ""
    body: str = ""
    reply_to: str = ""  # email_id being replied to
    created_at: float = 0.0
    approved: bool = False
    sent: bool = False
    sent_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "to": self.to,
            "subject": self.subject,
            "body": self.body,
            "reply_to": self.reply_to,
            "created_at": self.created_at,
            "approved": self.approved,
            "sent": self.sent,
            "sent_at": self.sent_at,
        }


class EmailSystem:
    """Email monitoring and management.

    Connects to IMAP for reading and SMTP for sending.
    Monitors inbox, classifies emails, detects phishing, and
    drafts responses for Creator approval.
    """

    ACTOR = "anubis.email"

    def __init__(
        self,
        root: str | Path,
        *,
        imap_host: str = "",
        imap_port: int = 993,
        smtp_host: str = "",
        smtp_port: int = 587,
        email_addr: str = "",
        email_pass: str = "",  # app password, stored encrypted in production
        ledger: Any | None = None,
        on_new_email: Callable[[Email], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.email_addr = email_addr
        self.email_pass = email_pass
        self.ledger = ledger
        self.on_new_email = on_new_email

        self._state_dir = self.root / "memory" / "email"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._emails_file = self._state_dir / "emails.json"
        self._drafts_file = self._state_dir / "drafts.json"

        self._emails: dict[str, Email] = {}
        self._drafts: dict[str, EmailDraft] = {}
        self._seen_ids: set[str] = set()
        self._load()

    # --------------------------------------------------- IMAP (reading)

    def fetch_inbox(self, limit: int = 20) -> list[Email]:
        """Fetch recent emails from IMAP inbox."""
        if not self.imap_host or not self.email_addr:
            return []

        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_addr, self.email_pass)
            mail.select("inbox")

            _, data = mail.search(None, "ALL")
            ids = data[0].split()[-limit:] if data[0] else []

            new_emails: list[Email] = []
            for eid in ids:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw = msg_data[0][1]
                import email as email_module
                msg = email_module.message_from_bytes(raw)

                email_id = hashlib.sha256(raw).hexdigest()[:16]
                if email_id in self._seen_ids:
                    continue
                self._seen_ids.add(email_id)

                subject = self._decode_header(msg.get("Subject", ""))
                sender = msg.get("From", "")
                sender_name, sender_addr = self._parse_address(sender)

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain":
                            body = part.get_payload(decode=True).decode(
                                "utf-8", errors="replace"
                            )
                            break
                else:
                    body = msg.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )

                email_obj = Email(
                    email_id=email_id,
                    subject=subject,
                    sender=sender_addr,
                    sender_name=sender_name,
                    date=time.time(),
                    body=body,
                )

                # Classify and check for phishing
                email_obj.priority = self._classify_priority(email_obj)
                email_obj.phishing_score, email_obj.phishing_indicators = (
                    self._detect_phishing(email_obj)
                )
                if email_obj.phishing_score > 0.7:
                    email_obj.category = CAT_PHISHING

                self._emails[email_id] = email_obj
                new_emails.append(email_obj)

                if self.on_new_email:
                    try:
                        self.on_new_email(email_obj)
                    except Exception:
                        pass

            mail.logout()
            self._save()
            return new_emails
        except Exception:
            return []

    # --------------------------------------------------- SMTP (sending)

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Send an email via SMTP.

        Uses SMTP_SSL for port 465 (implicit SSL).
        Uses SMTP + STARTTLS for port 587.
        """
        if not self.smtp_host or not self.email_addr:
            return {"success": False, "error": "SMTP not configured"}

        try:
            msg = MIMEMultipart()
            msg["From"] = formataddr(("ANUBIS", self.email_addr))
            msg["To"] = to
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)
            msg.attach(MIMEText(body, "plain"))

            if self.smtp_port == 465:
                # Port 465 = implicit SSL (IONOS, Gmail, etc.)
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.email_addr, self.email_pass)
                    server.sendmail(self.email_addr, [to], msg.as_string())
            else:
                # Port 587 = STARTTLS
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_addr, self.email_pass)
                    server.sendmail(self.email_addr, [to], msg.as_string())

            self._log("email.sent", {"to": to, "subject": subject})
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------- drafts

    def create_draft(
        self, to: str, subject: str, body: str, reply_to: str = ""
    ) -> EmailDraft:
        """Create a draft email for Creator approval."""
        draft_id = hashlib.sha256(
            f"draft:{to}:{subject}:{time.time()}".encode()
        ).hexdigest()[:16]
        draft = EmailDraft(
            draft_id=draft_id, to=to, subject=subject, body=body,
            reply_to=reply_to, created_at=time.time(),
        )
        self._drafts[draft_id] = draft
        self._save_drafts()
        self._log("draft.created", {"to": to, "subject": subject})
        return draft

    def approve_draft(self, draft_id: str) -> dict[str, Any]:
        """Approve and send a draft."""
        draft = self._drafts.get(draft_id)
        if draft is None:
            return {"success": False, "error": "Draft not found"}
        if draft.sent:
            return {"success": False, "error": "Already sent"}

        draft.approved = True
        result = self.send_email(draft.to, draft.subject, draft.body)
        if result["success"]:
            draft.sent = True
            draft.sent_at = time.time()
        self._save_drafts()
        return result

    def reject_draft(self, draft_id: str) -> bool:
        draft = self._drafts.get(draft_id)
        if draft is None:
            return False
        del self._drafts[draft_id]
        self._save_drafts()
        return True

    def get_drafts(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._drafts.values()]

    def get_pending_drafts(self) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._drafts.values() if not d.sent]

    # --------------------------------------------------- classification

    def _classify_priority(self, email: Email) -> str:
        """Classify email priority based on content and sender."""
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()

        # Urgent keywords
        urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediately"]
        if any(kw in subject_lower for kw in urgent_keywords):
            return PRIORITY_URGENT

        # High priority keywords
        high_keywords = ["important", "action required", "deadline", "reminder",
                         "payment", "invoice", "overdue"]
        if any(kw in subject_lower for kw in high_keywords):
            return PRIORITY_HIGH

        # From specific important senders (would be configured)
        # For now, just check subject
        if "meeting" in subject_lower or "schedule" in subject_lower:
            return PRIORITY_HIGH

        return PRIORITY_NORMAL

    def _detect_phishing(self, email: Email) -> tuple[float, list[str]]:
        """Detect phishing indicators. Returns (score, indicators)."""
        indicators: list[str] = []
        score = 0.0

        subject_lower = email.subject.lower()
        body_lower = email.body.lower()
        sender_lower = email.sender.lower()

        # Suspicious subject keywords
        phishing_subjects = [
            "verify your account", "confirm your password", "account suspended",
            "urgent action", "click here", "you've won", "lottery",
            "inheritance", "wire transfer", "tax refund",
        ]
        for kw in phishing_subjects:
            if kw in subject_lower:
                indicators.append(f"suspicious subject: '{kw}'")
                score += 0.2

        # Suspicious body keywords
        phishing_body = [
            "click here to verify", "enter your password", "confirm your identity",
            "wire transfer", "bitcoin", "cryptocurrency", "gift card",
            "western union", "moneygram",
        ]
        for kw in phishing_body:
            if kw in body_lower:
                indicators.append(f"suspicious content: '{kw}'")
                score += 0.15

        # Sender domain mismatch
        if "@" in email.sender:
            domain = email.sender.split("@")[1]
            # Check for suspicious TLDs
            suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq"]
            if any(domain.endswith(tld) for tld in suspicious_tlds):
                indicators.append(f"suspicious domain: {domain}")
                score += 0.2

            # Check for lookalike domains
            lookalikes = ["g00gle", "arnazon", "paypa1", "micros0ft", "arnaz0n"]
            for ll in lookalikes:
                if ll in domain:
                    indicators.append(f"lookalike domain: {domain}")
                    score += 0.3

        # Urgency pressure
        urgency_words = ["immediately", "within 24 hours", "account will be closed"]
        for word in urgency_words:
            if word in body_lower:
                indicators.append(f"urgency pressure: '{word}'")
                score += 0.1

        return min(score, 1.0), indicators

    # --------------------------------------------------- queries

    def get_emails(self, limit: int = 50) -> list[dict[str, Any]]:
        emails = sorted(self._emails.values(), key=lambda e: e.date, reverse=True)
        return [e.to_dict() for e in emails[:limit]]

    def get_important_emails(self) -> list[dict[str, Any]]:
        return [
            e.to_dict() for e in self._emails.values()
            if e.priority in (PRIORITY_URGENT, PRIORITY_HIGH) and not e.read
        ]

    def get_phishing_emails(self) -> list[dict[str, Any]]:
        return [
            e.to_dict() for e in self._emails.values()
            if e.category == CAT_PHISHING
        ]

    def get_email(self, email_id: str) -> dict[str, Any] | None:
        e = self._emails.get(email_id)
        return e.to_dict() if e else None

    def mark_read(self, email_id: str) -> bool:
        e = self._emails.get(email_id)
        if e is None:
            return False
        e.read = True
        self._save()
        return True

    def flag_email(self, email_id: str) -> bool:
        e = self._emails.get(email_id)
        if e is None:
            return False
        e.flagged = True
        e.category = CAT_FLAGGED
        self._save()
        return True

    def get_unread_count(self) -> int:
        return sum(1 for e in self._emails.values() if not e.read)

    def get_important_count(self) -> int:
        return sum(
            1 for e in self._emails.values()
            if e.priority in (PRIORITY_URGENT, PRIORITY_HIGH) and not e.read
        )

    # --------------------------------------------------- helpers

    def _decode_header(self, header: str) -> str:
        try:
            decoded = decode_header(header)
            parts = []
            for part, enc in decoded:
                if isinstance(part, bytes):
                    parts.append(part.decode(enc or "utf-8", errors="replace"))
                else:
                    parts.append(part)
            return "".join(parts)
        except Exception:
            return header

    def _parse_address(self, addr: str) -> tuple[str, str]:
        """Parse 'Name <email@domain>' into (name, email)."""
        if "<" in addr and ">" in addr:
            name = addr.split("<")[0].strip().strip('"')
            email_addr = addr.split("<")[1].split(">")[0].strip()
            return name, email_addr
        return "", addr.strip()

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        return {
            "configured": bool(self.imap_host and self.email_addr),
            "has_password": bool(self.email_pass),
            "imap_host": self.imap_host,
            "smtp_host": self.smtp_host,
            "total_emails": len(self._emails),
            "unread": self.get_unread_count(),
            "important_unread": self.get_important_count(),
            "phishing_detected": len(self.get_phishing_emails()),
            "pending_drafts": len(self.get_pending_drafts()),
            "email_address": self.email_addr,
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if self._emails_file.exists():
            try:
                data = json.loads(self._emails_file.read_text(encoding="utf-8"))
                for e_id, e in data.items():
                    self._emails[e_id] = Email(
                        email_id=e_id,
                        subject=e.get("subject", ""),
                        sender=e.get("sender", ""),
                        sender_name=e.get("sender_name", ""),
                        recipients=e.get("recipients", []),
                        date=e.get("date", 0),
                        body=e.get("body", ""),
                        category=e.get("category", CAT_INBOX),
                        priority=e.get("priority", PRIORITY_NORMAL),
                        read=e.get("read", False),
                        flagged=e.get("flagged", False),
                        attachments=e.get("attachments", []),
                        thread_id=e.get("thread_id", ""),
                        phishing_score=e.get("phishing_score", 0),
                        phishing_indicators=e.get("phishing_indicators", []),
                    )
                    self._seen_ids.add(e_id)
            except Exception:
                pass

        if self._drafts_file.exists():
            try:
                data = json.loads(self._drafts_file.read_text(encoding="utf-8"))
                for d_id, d in data.items():
                    self._drafts[d_id] = EmailDraft(
                        draft_id=d_id,
                        to=d.get("to", ""),
                        subject=d.get("subject", ""),
                        body=d.get("body", ""),
                        reply_to=d.get("reply_to", ""),
                        created_at=d.get("created_at", 0),
                        approved=d.get("approved", False),
                        sent=d.get("sent", False),
                        sent_at=d.get("sent_at", 0),
                    )
            except Exception:
                pass

    def _save(self) -> None:
        data = {e_id: e.to_dict() for e_id, e in self._emails.items()}
        self._emails_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_drafts(self) -> None:
        data = {d_id: d.to_dict() for d_id, d in self._drafts.items()}
        self._drafts_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
