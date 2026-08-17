"""Tests for the external gateway module — policy-gated network access.

These tests verify:
- Constitutional gate (Creator approval required for CONSEQUENTIAL)
- Domain whitelist enforcement
- Rate limit enforcement
- Sensitive data detection (local_privacy law)
- Policy management (add/remove domains, set rate limits)
- Status endpoint (no secrets)
- Logging to evidence ledger

Network tests (actual HTTP calls) use mocked urllib to avoid
real network dependencies.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.external_gateway import (
    ExternalGateway,
    GatewayRequest,
    GatewayResponse,
    DEFAULT_POLICY,
    SENSITIVE_PATTERNS,
)
from anubis.constitution import ChangeClass, Request, Verdict, evaluate


class TestPolicyLoading(unittest.TestCase):
    """Tests for policy loading and defaults."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-policy-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_policy_loaded(self):
        gw = ExternalGateway(policy_path=Path(self.tmpdir) / "nonexistent.json")
        self.assertIn("allowed_domains", gw._policy)
        self.assertIn("grants.gov", gw._policy["allowed_domains"])

    def test_custom_policy_loaded(self):
        policy_path = Path(self.tmpdir) / "policy.json"
        policy_path.write_text(json.dumps({
            "allowed_domains": ["custom.example.com"],
            "rate_limits": {"requests_per_hour": 10, "requests_per_day": 50},
        }), encoding="utf-8")
        gw = ExternalGateway(policy_path=policy_path)
        self.assertIn("custom.example.com", gw._policy["allowed_domains"])
        self.assertEqual(gw._policy["rate_limits"]["requests_per_hour"], 10)

    def test_invalid_policy_falls_back_to_default(self):
        policy_path = Path(self.tmpdir) / "bad.json"
        policy_path.write_text("not json", encoding="utf-8")
        gw = ExternalGateway(policy_path=policy_path)
        self.assertIn("allowed_domains", gw._policy)


class TestDomainWhitelist(unittest.TestCase):
    """Tests for domain whitelist enforcement."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-domain-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_allowed_domain_exact_match(self):
        self.assertTrue(self.gw._is_domain_allowed("https://grants.gov/search"))

    def test_allowed_domain_subdomain(self):
        self.assertTrue(self.gw._is_domain_allowed("https://api.grants.gov/search"))

    def test_blocked_domain(self):
        self.assertFalse(self.gw._is_domain_allowed("https://evil.example.com"))

    def test_no_domain(self):
        self.assertFalse(self.gw._is_domain_allowed("not-a-url"))

    def test_empty_url(self):
        self.assertFalse(self.gw._is_domain_allowed(""))


class TestRateLimit(unittest.TestCase):
    """Tests for rate limit enforcement."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-rate-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")
        # Set low limits for testing
        self.gw._policy["rate_limits"] = {"requests_per_hour": 3, "requests_per_day": 10}

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_within_limits(self):
        self.assertTrue(self.gw._check_rate_limit())

    def test_exceeds_hourly_limit(self):
        now = time.time()
        self.gw._request_times = [now, now, now]  # 3 requests already
        self.assertFalse(self.gw._check_rate_limit())

    def test_exceeds_daily_limit(self):
        now = time.time()
        self.gw._request_times = [now - 7200] * 10  # 10 requests 2 hours ago
        self.assertFalse(self.gw._check_rate_limit())

    def test_old_requests_cleaned(self):
        now = time.time()
        self.gw._request_times = [now - 100000] * 20  # very old requests
        self.assertTrue(self.gw._check_rate_limit())


class TestSensitiveData(unittest.TestCase):
    """Tests for sensitive data detection (local_privacy law)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-sensitive-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_clean_payload(self):
        self.assertIsNone(self.gw._check_sensitive_data("just a normal search query"))

    def test_private_key_detected(self):
        payload = "-----BEGIN RSA PRIVATE KEY-----\nMIIkey..."
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)
        self.assertIn("sensitive data", result)

    def test_password_detected(self):
        payload = "password=secret123"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_api_key_detected(self):
        payload = "api_key=ABC123XYZ"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_access_key_detected(self):
        payload = "access_key_id=AKIATEST123"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_secret_access_key_detected(self):
        payload = "secret_access_key=supersecret"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_passphrase_detected(self):
        payload = "passphrase=mysecret"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_creator_id_detected(self):
        payload = "creator_id=4670b4cf48fed7c5"
        result = self.gw._check_sensitive_data(payload)
        self.assertIsNotNone(result)

    def test_empty_payload(self):
        self.assertIsNone(self.gw._check_sensitive_data(""))


class TestConstitutionalGate(unittest.TestCase):
    """Tests for the constitutional evaluation gate."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-const-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_request_without_approval_denied(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search for grants",
            creator_approved=False,
        )
        allowed, reason = self.gw._evaluate_request(req)
        self.assertFalse(allowed)
        self.assertIn("Creator approval", reason)

    def test_request_with_approval_allowed(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search for grants",
            creator_approved=True,
            capabilities_granted=frozenset({"external.request"}),
        )
        allowed, reason = self.gw._evaluate_request(req)
        self.assertTrue(allowed)


class TestGatewayRequest(unittest.TestCase):
    """Tests for the full gateway request flow with mocked network."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-req-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_request_denied_without_approval(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search for grants",
            creator_approved=False,
        )
        resp = self.gw.request(req)
        self.assertFalse(resp.ok)
        self.assertIn("Creator approval", resp.refused_reason)

    def test_request_denied_for_non_whitelisted_domain(self):
        req = GatewayRequest(
            url="https://evil.example.com/data",
            purpose="fetch data",
            creator_approved=True,
            capabilities_granted=frozenset({"external.request"}),
        )
        resp = self.gw.request(req)
        self.assertFalse(resp.ok)
        self.assertIn("whitelist", resp.refused_reason)

    def test_request_denied_for_sensitive_data(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search",
            method="POST",
            body=b"password=secret123",
            creator_approved=True,
            capabilities_granted=frozenset({"external.request"}),
        )
        resp = self.gw.request(req)
        self.assertFalse(resp.ok)
        self.assertIn("sensitive data", resp.refused_reason)

    @patch("anubis.external_gateway.urllib.request.urlopen")
    def test_successful_request(self, mock_urlopen):
        # Mock the HTTP response
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"results": ["grant1", "grant2"]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        req = GatewayRequest(
            url="https://grants.gov/search?q=test",
            purpose="search for grants",
            creator_approved=True,
            capabilities_granted=frozenset({"external.request"}),
        )
        resp = self.gw.request(req)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("grant1", resp.body)

    @patch("anubis.external_gateway.urllib.request.urlopen")
    def test_http_error_handled(self, mock_urlopen):
        import urllib.error
        import io
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://grants.gov/search", 404, "Not Found",
            {}, io.BytesIO(b'{"error": "not found"}')
        )

        req = GatewayRequest(
            url="https://grants.gov/search?q=test",
            purpose="search for grants",
            creator_approved=True,
            capabilities_granted=frozenset({"external.request"}),
        )
        resp = self.gw.request(req)
        self.assertFalse(resp.ok)
        self.assertEqual(resp.status_code, 404)


class TestPolicyManagement(unittest.TestCase):
    """Tests for policy management (add/remove domains, rate limits)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-mgmt-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_domain(self):
        self.gw.add_domain("new.example.com")
        self.assertIn("new.example.com", self.gw._policy["allowed_domains"])
        # Verify it persists
        gw2 = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")
        self.assertIn("new.example.com", gw2._policy["allowed_domains"])

    def test_add_duplicate_domain(self):
        original_count = len(self.gw._policy["allowed_domains"])
        self.gw.add_domain("grants.gov")  # already in defaults
        self.assertEqual(len(self.gw._policy["allowed_domains"]), original_count)

    def test_remove_domain(self):
        self.gw.remove_domain("grants.gov")
        self.assertNotIn("grants.gov", self.gw._policy["allowed_domains"])

    def test_set_rate_limits(self):
        self.gw.set_rate_limits(50, 200)
        self.assertEqual(self.gw._policy["rate_limits"]["requests_per_hour"], 50)
        self.assertEqual(self.gw._policy["rate_limits"]["requests_per_day"], 200)


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-status-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_status_returns_dict(self):
        status = self.gw.status()
        self.assertIsInstance(status, dict)

    def test_status_has_allowed_domains(self):
        status = self.gw.status()
        self.assertIn("allowed_domains", status)
        self.assertIn("grants.gov", status["allowed_domains"])

    def test_status_has_rate_limits(self):
        status = self.gw.status()
        self.assertIn("rate_limits", status)

    def test_status_has_request_counts(self):
        status = self.gw.status()
        self.assertIn("requests_last_hour", status)
        self.assertIn("requests_last_day", status)

    def test_status_shows_ledger_connection(self):
        status = self.gw.status()
        self.assertIn("ledger_connected", status)
        self.assertFalse(status["ledger_connected"])

    def test_status_with_ledger(self):
        ledger = MagicMock()
        gw = ExternalGateway(
            policy_path=Path(self.tmpdir) / "policy.json",
            ledger=ledger,
        )
        status = gw.status()
        self.assertTrue(status["ledger_connected"])


class TestLogging(unittest.TestCase):
    """Tests for evidence ledger logging."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-log-")
        self.ledger = MagicMock()
        self.gw = ExternalGateway(
            policy_path=Path(self.tmpdir) / "policy.json",
            ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_denied_request_is_logged(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search",
            creator_approved=False,
        )
        resp = self.gw.request(req)
        self.assertFalse(resp.ok)
        self.assertTrue(resp.logged)
        self.ledger.append.assert_called_once()

    def test_log_entry_contains_url_and_reason(self):
        req = GatewayRequest(
            url="https://grants.gov/search",
            purpose="search",
            creator_approved=False,
        )
        self.gw.request(req)
        call_args = self.gw.ledger.append.call_args[0][0]
        self.assertEqual(call_args["url"], "https://grants.gov/search")
        self.assertIn("refused_reason", call_args)
        self.assertEqual(call_args["type"], "external_gateway")


class TestFetchAndSearch(unittest.TestCase):
    """Tests for the convenience methods."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-gw-fetch-")
        self.gw = ExternalGateway(policy_path=Path(self.tmpdir) / "policy.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fetch_without_approval_denied(self):
        resp = self.gw.fetch("https://grants.gov/search", creator_approved=False)
        self.assertFalse(resp.ok)
        self.assertIn("Creator approval", resp.refused_reason)

    def test_search_without_approval_denied(self):
        resp = self.gw.search("test query", creator_approved=False)
        self.assertFalse(resp.ok)
        self.assertIn("Creator approval", resp.refused_reason)

    def test_fetch_with_approval_attempts_request(self):
        # Even with approval, non-whitelisted domain should be refused
        resp = self.gw.fetch(
            "https://evil.example.com/data",
            purpose="test",
            creator_approved=True,
        )
        self.assertFalse(resp.ok)
        self.assertIn("whitelist", resp.refused_reason)


if __name__ == "__main__":
    unittest.main()
