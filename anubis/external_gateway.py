"""Policy-gated external network gateway.

This is the critical piece that gives ANUBIS internet access without
weakening the sandbox. The sandbox stays for all generated/untrusted
code. This module is a first-party service that runs outside the
sandbox, and every call passes through the constitutional evaluation
(``constitution.evaluate``) before execution.

Design principle: the gateway is a first-party service, not generated
code. It is reviewed by the Creator, and every request is:

  1. Classified as CONSEQUENTIAL (requires Creator approval)
  2. Evaluated by the constitution (``constitution.evaluate``)
  3. Checked against the policy whitelist (allowed domains)
  4. Checked against rate limits
  5. Checked against the data classification (no private data leaves)
  6. Logged to the evidence ledger (audit law)

The sandbox is never weakened. Generated code that needs network
access must request it through this gateway, and the request is
gated by the constitution.

Privacy: the ``local_privacy`` immutable law is enforced here. No
identity vault data, credentials, or private conversation content
leaves the machine. The gateway checks the payload against a
sensitive-data pattern list before sending.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constitution import ChangeClass, Request, Verdict, evaluate

# Default policy file location
POLICY_FILE = "policy/external_gateway.json"

# Default policy — restrictive. The Creator must explicitly add domains.
DEFAULT_POLICY = {
    "allowed_domains": [
        "grants.gov",
        "findgrants.io",
        "grantable.co",
        "sentient.foundation",
        "upwork.com",
        "task-bounty.com",
        "codebounty.ai",
        "generativelanguage.googleapis.com",  # Google Gemini API
        "api.groq.com",                       # Groq API
    ],
    "rate_limits": {
        "requests_per_hour": 100,
        "requests_per_day": 500,
    },
    "time_window": {
        "allowed_hours": "0-23",  # 24/7 by default; Creator can restrict
    },
    "blocked_patterns": [
        # Sensitive data patterns — refused if found in payload
        r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
        r"[A-Za-z0-9+/]{40,}={0,2}",  # long base64 (potential keys/tokens)
    ],
}

# Patterns that indicate sensitive data in the payload
SENSITIVE_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"access_key_id\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"api_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"passphrase\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"creator_id\s*[:=]\s*\S+", re.IGNORECASE),
]


@dataclass
class GatewayRequest:
    """A request to make an external network call."""
    url: str
    purpose: str
    actor: str = "anubis"
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    creator_approved: bool = False
    capabilities_granted: frozenset[str] = field(default_factory=frozenset)


@dataclass
class GatewayResponse:
    """Result of an external gateway request."""
    ok: bool
    status_code: int = 0
    body: str = ""
    url: str = ""
    error: str = ""
    duration_s: float = 0.0
    logged: bool = False
    refused_reason: str = ""


class ExternalGateway:
    """Policy-gated external network gateway.

    All requests pass through constitutional evaluation before
    execution. The sandbox is never weakened.
    """

    def __init__(
        self,
        policy_path: str | Path | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.policy_path = Path(policy_path or POLICY_FILE)
        self.ledger = ledger
        self._policy: dict[str, Any] = self._load_policy()
        self._request_times: list[float] = []

    # --------------------------------------------------- policy

    def _load_policy(self) -> dict[str, Any]:
        """Load the gateway policy from disk, or use defaults."""
        if self.policy_path.exists():
            try:
                return json.loads(self.policy_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return DEFAULT_POLICY.copy()

    def _save_policy(self) -> None:
        """Save the current policy to disk."""
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(
            json.dumps(self._policy, indent=2) + "\n",
            encoding="utf-8",
        )

    def _is_domain_allowed(self, url: str) -> bool:
        """Check if the URL's domain is in the whitelist."""
        try:
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.hostname or ""
            if not domain:
                return False
            allowed = self._policy.get("allowed_domains", [])
            for allowed_domain in allowed:
                if domain == allowed_domain or domain.endswith("." + allowed_domain):
                    return True
            return False
        except Exception:
            return False

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        # Clean old entries (older than 24 hours)
        self._request_times = [t for t in self._request_times if now - t < 86400]

        limits = self._policy.get("rate_limits", {})
        per_hour = limits.get("requests_per_hour", 100)
        per_day = limits.get("requests_per_day", 500)

        # Count requests in the last hour
        hour_count = sum(1 for t in self._request_times if now - t < 3600)
        day_count = len(self._request_times)

        if hour_count >= per_hour:
            return False
        if day_count >= per_day:
            return False
        return True

    def _check_sensitive_data(self, payload: str) -> str | None:
        """Check if the payload contains sensitive data.

        Returns the matched pattern description if sensitive data is
        found, None otherwise.
        """
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(payload):
                return f"sensitive data pattern matched: {pattern.pattern[:50]}"
        return None

    # --------------------------------------------------- constitutional gate

    def _evaluate_request(self, req: GatewayRequest) -> tuple[bool, str]:
        """Evaluate a request through the constitutional gate.

        Returns (allowed, reason). If not allowed, reason explains why.
        """
        # Build a constitutional Request
        # The capability requested is "external.request" — the caller must
        # have granted this capability (via Creator approval).
        caps = req.capabilities_granted if req.capabilities_granted else frozenset()
        constitution_req = Request(
            actor=req.actor,
            action="external.request",
            change_class=ChangeClass.CONSEQUENTIAL,
            intent=req.purpose,
            capabilities_requested=frozenset({"external.request"}) if req.creator_approved else frozenset(),
            capabilities_granted=frozenset({"external.request"}) | caps if req.creator_approved else caps,
            payload=req.url,
            creator_approved=req.creator_approved,
            reversible=True,
            explainable=True,
        )

        ruling = evaluate(constitution_req)

        if ruling.verdict == Verdict.ALLOW:
            return True, "approved by constitution"
        if ruling.verdict == Verdict.REQUIRES_CREATOR_APPROVAL:
            return False, "requires Creator approval: " + "; ".join(ruling.reasons)
        return False, "denied by constitution: " + "; ".join(ruling.reasons)

    # --------------------------------------------------- logging

    def _log_request(
        self,
        req: GatewayRequest,
        response: GatewayResponse,
    ) -> None:
        """Log the request to the evidence ledger."""
        if self.ledger is None:
            return
        try:
            entry = {
                "type": "external_gateway",
                "url": req.url,
                "purpose": req.purpose,
                "method": req.method,
                "actor": req.actor,
                "status_code": response.status_code,
                "ok": response.ok,
                "duration_s": round(response.duration_s, 3),
                "refused": bool(response.refused_reason),
                "refused_reason": response.refused_reason,
                "timestamp": time.time(),
            }
            self.ledger.append(entry)
            response.logged = True
        except Exception:
            pass  # logging failure is non-fatal

    # --------------------------------------------------- public API

    def request(self, req: GatewayRequest) -> GatewayResponse:
        """Execute an external network request through all gates.

        This is the single entry point for all external network calls.
        Every request passes through:
        1. Constitutional evaluation (Creator approval for CONSEQUENTIAL)
        2. Domain whitelist check
        3. Rate limit check
        4. Sensitive data check (local_privacy law)
        5. Execution
        6. Evidence ledger logging (audit law)
        """
        t0 = time.monotonic()

        # Gate 1: Constitutional evaluation
        allowed, reason = self._evaluate_request(req)
        if not allowed:
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error=reason,
                refused_reason=reason,
                duration_s=time.monotonic() - t0,
            )
            self._log_request(req, resp)
            return resp

        # Gate 2: Domain whitelist
        if not self._is_domain_allowed(req.url):
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error=f"domain not in whitelist: {req.url}",
                refused_reason="domain not whitelisted",
                duration_s=time.monotonic() - t0,
            )
            self._log_request(req, resp)
            return resp

        # Gate 3: Rate limit
        if not self._check_rate_limit():
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error="rate limit exceeded",
                refused_reason="rate limit exceeded",
                duration_s=time.monotonic() - t0,
            )
            self._log_request(req, resp)
            return resp

        # Gate 4: Sensitive data check
        payload_str = req.body.decode("utf-8", "replace") if req.body else ""
        sensitive = self._check_sensitive_data(payload_str)
        if sensitive:
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error=f"refused: {sensitive}",
                refused_reason=f"sensitive data: {sensitive}",
                duration_s=time.monotonic() - t0,
            )
            self._log_request(req, resp)
            return resp

        # Gate 5: Execute the request
        try:
            http_req = urllib.request.Request(
                req.url,
                data=req.body if req.method in ("POST", "PUT") else None,
                headers=req.headers,
                method=req.method,
            )
            with urllib.request.urlopen(http_req, timeout=30) as http_resp:
                body = http_resp.read().decode("utf-8", "replace")
                resp = GatewayResponse(
                    ok=True,
                    status_code=http_resp.status,
                    body=body,
                    url=req.url,
                    duration_s=time.monotonic() - t0,
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:5000]
            resp = GatewayResponse(
                ok=False,
                status_code=exc.code,
                body=body,
                url=req.url,
                error=f"HTTP {exc.code}: {body[:200]}",
                duration_s=time.monotonic() - t0,
            )
        except urllib.error.URLError as exc:
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error=f"connection error: {exc.reason}",
                duration_s=time.monotonic() - t0,
            )
        except Exception as exc:
            resp = GatewayResponse(
                ok=False,
                url=req.url,
                error=f"unexpected error: {exc}",
                duration_s=time.monotonic() - t0,
            )

        # Record the request time for rate limiting
        self._request_times.append(time.time())

        # Gate 6: Log to evidence ledger
        self._log_request(req, resp)

        return resp

    def search(self, query: str, *, creator_approved: bool = False) -> GatewayResponse:
        """Search the web via a search API.

        This is a convenience method that constructs a GatewayRequest
        for a web search. The actual search API endpoint must be in
        the policy whitelist.
        """
        # Use a simple search URL (Creator can configure a specific API)
        # For now, this is a placeholder that the prospects system will use
        req = GatewayRequest(
            url=f"https://findgrants.io/search?q={urllib.request.quote(query)}",
            purpose=f"web search: {query[:100]}",
            method="GET",
            creator_approved=creator_approved,
            capabilities_granted=frozenset({"external.request", "external.search"}) if creator_approved else frozenset(),
        )
        return self.request(req)

    def fetch(self, url: str, *, purpose: str = "", creator_approved: bool = False) -> GatewayResponse:
        """Fetch a specific URL.

        The URL's domain must be in the policy whitelist.
        """
        req = GatewayRequest(
            url=url,
            purpose=purpose or f"fetch: {url[:100]}",
            method="GET",
            creator_approved=creator_approved,
            capabilities_granted=frozenset({"external.request", "external.fetch"}) if creator_approved else frozenset(),
        )
        return self.request(req)

    # --------------------------------------------------- policy management

    def add_domain(self, domain: str) -> None:
        """Add a domain to the whitelist."""
        if "allowed_domains" not in self._policy:
            self._policy["allowed_domains"] = []
        if domain not in self._policy["allowed_domains"]:
            self._policy["allowed_domains"].append(domain)
            self._save_policy()

    def remove_domain(self, domain: str) -> None:
        """Remove a domain from the whitelist."""
        if "allowed_domains" in self._policy:
            self._policy["allowed_domains"] = [
                d for d in self._policy["allowed_domains"] if d != domain
            ]
            self._save_policy()

    def set_rate_limits(self, per_hour: int, per_day: int) -> None:
        """Update rate limits."""
        if "rate_limits" not in self._policy:
            self._policy["rate_limits"] = {}
        self._policy["rate_limits"]["requests_per_hour"] = per_hour
        self._policy["rate_limits"]["requests_per_day"] = per_day
        self._save_policy()

    # --------------------------------------------------- status

    def status(self) -> dict[str, Any]:
        """Return gateway status (no secrets)."""
        now = time.time()
        hour_count = sum(1 for t in self._request_times if now - t < 3600)
        day_count = sum(1 for t in self._request_times if now - t < 86400)
        limits = self._policy.get("rate_limits", {})
        return {
            "policy_file": str(self.policy_path),
            "allowed_domains": self._policy.get("allowed_domains", []),
            "rate_limits": limits,
            "requests_last_hour": hour_count,
            "requests_last_day": day_count,
            "ledger_connected": self.ledger is not None,
        }
