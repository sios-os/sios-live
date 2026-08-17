"""Tests for email system."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.email_system import (
    EmailSystem, Email, EmailDraft,
    PRIORITY_URGENT, PRIORITY_HIGH, PRIORITY_NORMAL,
    CAT_PHISHING, CAT_FLAGGED,
)


class TestEmail(unittest.TestCase):
    def test_to_dict(self):
        e = Email(email_id="e1", subject="Test", sender="user@example.com")
        d = e.to_dict()
        self.assertEqual(d["email_id"], "e1")
        self.assertEqual(d["subject"], "Test")


class TestEmailDraft(unittest.TestCase):
    def test_to_dict(self):
        d = EmailDraft(draft_id="d1", to="user@example.com", subject="Re: Test")
        data = d.to_dict()
        self.assertEqual(data["draft_id"], "d1")
        self.assertFalse(data["sent"])


class TestEmailSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.email = EmailSystem(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        self.assertFalse(self.email.get_status()["configured"])

    def test_classify_priority_urgent(self):
        e = Email(email_id="e1", subject="URGENT: Action needed")
        self.assertEqual(self.email._classify_priority(e), PRIORITY_URGENT)

    def test_classify_priority_high(self):
        e = Email(email_id="e1", subject="Important: Invoice overdue")
        self.assertEqual(self.email._classify_priority(e), PRIORITY_HIGH)

    def test_classify_priority_normal(self):
        e = Email(email_id="e1", subject="Lunch tomorrow?")
        self.assertEqual(self.email._classify_priority(e), PRIORITY_NORMAL)

    def test_detect_phishing_clean(self):
        e = Email(email_id="e1", subject="Lunch?", sender="friend@example.com", body="Want to grab lunch?")
        score, indicators = self.email._detect_phishing(e)
        self.assertEqual(score, 0.0)
        self.assertEqual(len(indicators), 0)

    def test_detect_phishing_subject(self):
        e = Email(email_id="e1", subject="Verify your account", sender="phish@evil.tk")
        score, indicators = self.email._detect_phishing(e)
        self.assertGreater(score, 0.3)
        self.assertTrue(len(indicators) > 0)

    def test_detect_phishing_body(self):
        e = Email(
            email_id="e1", subject="Hello",
            sender="scammer@evil.com",
            body="Click here to verify your password. Enter your password now. Bitcoin payment.",
        )
        score, indicators = self.email._detect_phishing(e)
        self.assertGreater(score, 0.4)

    def test_detect_phishing_lookalike_domain(self):
        e = Email(email_id="e1", subject="Hi", sender="noreply@paypa1.com")
        score, indicators = self.email._detect_phishing(e)
        self.assertGreaterEqual(score, 0.3)
        self.assertTrue(any("lookalike" in i for i in indicators))

    def test_detect_phishing_suspicious_tld(self):
        e = Email(email_id="e1", subject="Hi", sender="user@scam.tk")
        score, indicators = self.email._detect_phishing(e)
        self.assertGreater(score, 0.1)

    def test_detect_phishing_urgency(self):
        e = Email(
            email_id="e1", subject="Account",
            sender="security@bank.com",
            body="Your account will be closed. Respond immediately.",
        )
        score, indicators = self.email._detect_phishing(e)
        self.assertGreater(score, 0.1)
        self.assertTrue(any("urgency" in i for i in indicators))

    def test_parse_address_with_name(self):
        name, addr = self.email._parse_address('John Doe <john@example.com>')
        self.assertEqual(name, "John Doe")
        self.assertEqual(addr, "john@example.com")

    def test_parse_address_without_name(self):
        name, addr = self.email._parse_address("john@example.com")
        self.assertEqual(name, "")
        self.assertEqual(addr, "john@example.com")

    def test_create_draft(self):
        draft = self.email.create_draft("user@example.com", "Test", "Body")
        self.assertEqual(draft.to, "user@example.com")
        self.assertFalse(draft.sent)
        drafts = self.email.get_drafts()
        self.assertEqual(len(drafts), 1)

    def test_reject_draft(self):
        draft = self.email.create_draft("user@example.com", "Test", "Body")
        self.assertTrue(self.email.reject_draft(draft.draft_id))
        self.assertEqual(len(self.email.get_drafts()), 0)

    def test_get_pending_drafts(self):
        self.email.create_draft("user@example.com", "Test", "Body")
        pending = self.email.get_pending_drafts()
        self.assertEqual(len(pending), 1)

    def test_send_email_not_configured(self):
        result = self.email.send_email("user@example.com", "Test", "Body")
        self.assertFalse(result["success"])

    def test_approve_draft_not_configured(self):
        draft = self.email.create_draft("user@example.com", "Test", "Body")
        result = self.email.approve_draft(draft.draft_id)
        self.assertFalse(result["success"])

    def test_approve_nonexistent_draft(self):
        result = self.email.approve_draft("nonexistent")
        self.assertFalse(result["success"])

    def test_fetch_inbox_not_configured(self):
        result = self.email.fetch_inbox()
        self.assertEqual(result, [])

    def test_mark_read(self):
        e = Email(email_id="e1", subject="Test")
        self.email._emails["e1"] = e
        self.assertTrue(self.email.mark_read("e1"))
        self.assertTrue(self.email._emails["e1"].read)

    def test_flag_email(self):
        e = Email(email_id="e1", subject="Test")
        self.email._emails["e1"] = e
        self.assertTrue(self.email.flag_email("e1"))
        self.assertTrue(self.email._emails["e1"].flagged)
        self.assertEqual(self.email._emails["e1"].category, CAT_FLAGGED)

    def test_get_unread_count(self):
        self.email._emails["e1"] = Email(email_id="e1", read=False)
        self.email._emails["e2"] = Email(email_id="e2", read=True)
        self.assertEqual(self.email.get_unread_count(), 1)

    def test_get_important_emails(self):
        self.email._emails["e1"] = Email(
            email_id="e1", priority=PRIORITY_URGENT, read=False
        )
        self.email._emails["e2"] = Email(
            email_id="e2", priority=PRIORITY_NORMAL, read=False
        )
        important = self.email.get_important_emails()
        self.assertEqual(len(important), 1)

    def test_get_phishing_emails(self):
        self.email._emails["e1"] = Email(email_id="e1", category=CAT_PHISHING)
        self.email._emails["e2"] = Email(email_id="e2")
        phishing = self.email.get_phishing_emails()
        self.assertEqual(len(phishing), 1)

    def test_get_status(self):
        self.email._emails["e1"] = Email(email_id="e1", read=False)
        status = self.email.get_status()
        self.assertEqual(status["total_emails"], 1)
        self.assertEqual(status["unread"], 1)

    def test_emails_persist(self):
        self.email._emails["e1"] = Email(email_id="e1", subject="Test")
        self.email._save()
        email2 = EmailSystem(self.root)
        self.assertEqual(len(email2.get_emails()), 1)

    def test_drafts_persist(self):
        self.email.create_draft("user@example.com", "Test", "Body")
        email2 = EmailSystem(self.root)
        self.assertEqual(len(email2.get_drafts()), 1)

    def test_on_new_email_callback(self):
        called = []
        system = EmailSystem(self.root, on_new_email=lambda e: called.append(e))
        # Can't test with real IMAP, but verify callback is stored
        self.assertIsNotNone(system.on_new_email)


if __name__ == "__main__":
    unittest.main()
