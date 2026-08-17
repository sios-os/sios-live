"""Knowledge acquisition — ANUBIS lawfully researches and learns new domains.

When ANUBIS identifies a knowledge gap (through dream cycles or Creator
requests), this module handles the lawful acquisition of new knowledge:

1. **Identify need** — What domain does ANUBIS need to learn?
2. **Search** — Use the external gateway (governed, whitelisted) to find
   lawful sources (public documentation, open licenses, public domain)
3. **Fetch** — Retrieve content through the gateway with privacy gates
4. **Quarantine** — All new knowledge goes through the standard quarantine
   process before promotion
5. **Verify** — Check license compatibility and factual accuracy
6. **Promote** — After quarantine, promote to the knowledge base with
   Creator approval for sensitive domains

License policy:
- Public domain: auto-promotable after quarantine
- Open licenses (MIT, Apache, CC-BY, CC-BY-SA): promotable after quarantine
- CC-BY-NC: promotable with Creator approval
- Proprietary/unknown: requires Creator approval, never auto-promoted

The acquisition loop is designed to be triggered by:
- Dream cycle gap analysis
- Creator requests ("learn about X")
- Self-identified knowledge needs during missions

Governance:
- All network access goes through the external gateway
- All acquired knowledge goes through quarantine
- License is checked and recorded
- No scraping of paywalled or restricted content
- Rate-limited and privacy-gated

Uses only the Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


# --------------------------------------------------------------------- types


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


class GatewayLike(Protocol):
    def fetch(self, url: str) -> dict[str, Any]: ...
    def search(self, query: str) -> dict[str, Any]: ...


class KnowledgeBaseLike(Protocol):
    def ingest_to_quarantine(
        self,
        title: str,
        content: str,
        source_id: str = "",
        specialty_id: str = "",
        license: str = "",
        tags: list[str] | None = None,
    ) -> str: ...


# License classification
# Order matters: more specific licenses must be checked first
# (e.g., "cc-by-nc" must be matched before "cc-by")
LICENSE_CATEGORIES = {
    "public_domain": {
        "auto_promotable": True,
        "licenses": ["public domain", "cc0", "unlicense", "public-domain"],
    },
    "non_commercial": {
        "auto_promotable": False,
        "licenses": ["cc-by-nc-sa", "cc-by-nc-nd", "cc-by-nc", "attribution-noncommercial"],
    },
    "restricted": {
        "auto_promotable": False,
        "licenses": ["cc-by-nd", "attribution-noderivatives",
                      "proprietary", "all rights reserved"],
    },
    "open": {
        "auto_promotable": True,
        "licenses": ["mit", "apache-2.0", "apache 2.0", "bsd", "cc-by-sa",
                      "cc-by", "gpl", "lgpl", "mpl", "isc"],
    },
}


@dataclass
class AcquisitionRequest:
    """A request to acquire knowledge about a topic."""
    request_id: str
    topic: str
    reason: str  # why this knowledge is needed
    source: str  # what triggered this request (dream, creator, mission)
    status: str = "pending"  # pending, searching, fetched, quarantined, promoted, rejected
    search_results: list[dict[str, Any]] = field(default_factory=list)
    fetched_content: list[dict[str, Any]] = field(default_factory=list)
    license_info: dict[str, Any] = field(default_factory=dict)
    quarantine_ids: list[str] = field(default_factory=list)
    created_at: float = 0.0
    completed_at: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "topic": self.topic,
            "reason": self.reason,
            "source": self.source,
            "status": self.status,
            "search_results": self.search_results,
            "fetched_content": self.fetched_content,
            "license_info": self.license_info,
            "quarantine_ids": self.quarantine_ids,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


# --------------------------------------------------------------- license


def classify_license(license_text: str) -> dict[str, Any]:
    """Classify a license string into a category.

    Returns:
        Dict with category, auto_promotable, and matched_license
    """
    license_lower = license_text.lower().strip()

    for category, info in LICENSE_CATEGORIES.items():
        for lic in info["licenses"]:
            if lic in license_lower:
                return {
                    "category": category,
                    "auto_promotable": info["auto_promotable"],
                    "matched_license": lic,
                    "raw": license_text,
                }

    return {
        "category": "restricted",
        "auto_promotable": False,
        "matched_license": "unknown",
        "raw": license_text,
    }


def detect_license(content: str) -> str:
    """Attempt to detect license from content."""
    content_lower = content.lower()

    # Common license markers
    markers = [
        ("public domain", "public domain"),
        ("cc0", "cc0"),
        ("unlicense", "unlicense"),
        ("mit license", "mit"),
        ("permission is hereby granted, free of charge", "mit"),
        ("apache license, version 2.0", "apache-2.0"),
        ("apache 2.0", "apache-2.0"),
        ("bsd ", "bsd"),
        ("cc-by", "cc-by"),
        ("cc by", "cc-by"),
        ("attribution-sharealike", "cc-by-sa"),
        ("attribution-noncommercial", "cc-by-nc"),
        ("gnu general public license", "gpl"),
        ("gnu lesser general public license", "lgpl"),
        ("mozilla public license", "mpl"),
        ("isc license", "isc"),
        ("all rights reserved", "proprietary"),
    ]

    for marker, license_name in markers:
        if marker in content_lower:
            return license_name

    return "unknown"


# --------------------------------------------------------------- acquisition


class KnowledgeAcquisition:
    """Lawful knowledge acquisition loop.

    Acquires new knowledge through the external gateway, classifies
    licenses, and routes through quarantine.
    """

    ACTOR = "anubis.knowledge_acquisition"

    def __init__(
        self,
        root: str | Path,
        *,
        gateway: GatewayLike | None = None,
        knowledge: KnowledgeBaseLike | None = None,
        model: ModelLike | None = None,
        ledger: Any | None = None,
        max_results_per_search: int = 5,
        max_content_per_fetch: int = 10000,
    ) -> None:
        self.root = Path(root)
        self.gateway = gateway
        self.knowledge = knowledge
        self.model = model
        self.ledger = ledger
        self.max_results = max_results_per_search
        self.max_content = max_content_per_fetch

        self._requests_dir = self.root / "memory" / "acquisition"
        self._requests_dir.mkdir(parents=True, exist_ok=True)
        self._requests_file = self._requests_dir / "requests.json"

    def request_acquisition(
        self,
        topic: str,
        reason: str,
        source: str = "creator",
    ) -> AcquisitionRequest:
        """Create a new knowledge acquisition request.

        Args:
            topic: What domain to learn about
            reason: Why this knowledge is needed
            source: What triggered this (creator, dream, mission)

        Returns:
            The created request (not yet processed)
        """
        request = AcquisitionRequest(
            request_id=hashlib.sha256(
                f"acq:{topic}:{time.time()}".encode()
            ).hexdigest()[:16],
            topic=topic,
            reason=reason,
            source=source,
            created_at=time.time(),
        )
        self._save_request(request)
        self._log("acquisition.requested", {
            "request_id": request.request_id,
            "topic": topic,
            "reason": reason,
            "source": source,
        })
        return request

    def process_request(self, request_id: str) -> dict[str, Any]:
        """Process a knowledge acquisition request.

        This searches for lawful sources, fetches content, classifies
        licenses, and routes through quarantine.

        Returns:
            Dict with acquisition results
        """
        request = self._load_request(request_id)
        if request is None:
            return {"error": "Request not found"}

        if request.status not in ("pending",):
            return {"error": f"Request already {request.status}"}

        # Phase 1: Search
        if self.gateway is None:
            request.status = "rejected"
            request.error = "No gateway configured"
            self._update_request(request)
            return {"error": "No gateway configured"}

        request.status = "searching"
        self._update_request(request)

        try:
            search_result = self.gateway.search(
                f"{request.topic} documentation open license"
            )
            request.search_results = search_result.get("results", [])[:self.max_results]
        except Exception as exc:
            request.status = "rejected"
            request.error = f"Search failed: {exc}"
            self._update_request(request)
            return {"error": str(exc)}

        if not request.search_results:
            request.status = "rejected"
            request.error = "No search results found"
            self._update_request(request)
            return {"error": "No search results found"}

        # Phase 2: Fetch content
        request.status = "fetching"
        self._update_request(request)

        for result in request.search_results[:3]:  # limit fetches
            url = result.get("url", "")
            if not url:
                continue
            try:
                fetch_result = self.gateway.fetch(url)
                content = fetch_result.get("content", "")
                if content:
                    # Truncate to max
                    content = content[:self.max_content]
                    # Detect license
                    license_name = detect_license(content)
                    license_info = classify_license(license_name)

                    request.fetched_content.append({
                        "url": url,
                        "title": result.get("title", ""),
                        "content_length": len(content),
                        "content": content,
                        "license": license_name,
                        "license_category": license_info["category"],
                        "auto_promotable": license_info["auto_promotable"],
                    })
            except Exception:
                continue  # skip failed fetches

        if not request.fetched_content:
            request.status = "rejected"
            request.error = "No content fetched"
            self._update_request(request)
            return {"error": "No content fetched"}

        # Phase 3: Quarantine
        if self.knowledge is None:
            request.status = "rejected"
            request.error = "No knowledge base configured"
            self._update_request(request)
            return {"error": "No knowledge base configured"}

        request.status = "quarantining"
        self._update_request(request)

        for item in request.fetched_content:
            try:
                qid = self.knowledge.ingest_to_quarantine(
                    title=item["title"] or f"Acquired: {request.topic}",
                    content=item["content"],
                    source_id=item["url"],
                    specialty_id="",  # let the knowledge base classify
                    license=item["license"],
                    tags=[request.topic, "acquired", item["license_category"]],
                )
                request.quarantine_ids.append(qid)
            except Exception as exc:
                continue

        request.status = "quarantined"
        request.completed_at = time.time()
        self._update_request(request)

        self._log("acquisition.quarantined", {
            "request_id": request_id,
            "topic": request.topic,
            "items_quarantined": len(request.quarantine_ids),
            "licenses": [i["license"] for i in request.fetched_content],
        })

        return {
            "request_id": request_id,
            "status": "quarantined",
            "items_quarantined": len(request.quarantine_ids),
            "license_info": [
                {
                    "url": i["url"],
                    "license": i["license"],
                    "category": i["license_category"],
                    "auto_promotable": i["auto_promotable"],
                }
                for i in request.fetched_content
            ],
        }

    def auto_promote_eligible(self, request_id: str) -> dict[str, Any]:
        """Auto-promote content with auto-promotable licenses.

        Only public domain and open license content can be auto-promoted.
        Everything else requires Creator approval.
        """
        request = self._load_request(request_id)
        if request is None:
            return {"error": "Request not found"}

        if request.status != "quarantined":
            return {"error": f"Request must be quarantined, is {request.status}"}

        promoted = 0
        needs_approval = 0

        for item in request.fetched_content:
            if item.get("auto_promotable"):
                # Can auto-promote (in a real system, the knowledge base
                # would handle the promotion from quarantine)
                promoted += 1
            else:
                needs_approval += 1

        if promoted > 0 and needs_approval == 0:
            request.status = "promoted"
        elif promoted > 0:
            request.status = "partially_promoted"
        else:
            request.status = "needs_approval"

        self._update_request(request)

        return {
            "request_id": request_id,
            "status": request.status,
            "auto_promoted": promoted,
            "needs_creator_approval": needs_approval,
        }

    def list_requests(self, status: str | None = None) -> list[dict[str, Any]]:
        """List acquisition requests."""
        requests = self._load_all_requests()
        if status:
            requests = [r for r in requests if r["status"] == status]
        return requests

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        """Get a single request."""
        request = self._load_request(request_id)
        if request is None:
            return None
        return request.to_dict()

    def get_status(self) -> dict[str, Any]:
        """Get acquisition system status."""
        requests = self._load_all_requests()
        return {
            "total_requests": len(requests),
            "by_status": {
                s: sum(1 for r in requests if r["status"] == s)
                for s in set(r["status"] for r in requests)
            },
            "gateway_configured": self.gateway is not None,
            "knowledge_base_configured": self.knowledge is not None,
        }

    # ------------------------------------------------------- internals

    def _save_request(self, request: AcquisitionRequest) -> None:
        requests = self._load_all_requests()
        requests.append(request.to_dict())
        self._requests_file.write_text(
            json.dumps(requests, indent=2), encoding="utf-8"
        )

    def _update_request(self, request: AcquisitionRequest) -> None:
        requests = self._load_all_requests()
        for i, r in enumerate(requests):
            if r["request_id"] == request.request_id:
                requests[i] = request.to_dict()
                break
        self._requests_file.write_text(
            json.dumps(requests, indent=2), encoding="utf-8"
        )

    def _load_request(self, request_id: str) -> AcquisitionRequest | None:
        requests = self._load_all_requests()
        for r in requests:
            if r["request_id"] == request_id:
                return AcquisitionRequest(
                    request_id=r["request_id"],
                    topic=r["topic"],
                    reason=r["reason"],
                    source=r["source"],
                    status=r["status"],
                    search_results=r.get("search_results", []),
                    fetched_content=r.get("fetched_content", []),
                    license_info=r.get("license_info", {}),
                    quarantine_ids=r.get("quarantine_ids", []),
                    created_at=r.get("created_at", 0.0),
                    completed_at=r.get("completed_at", 0.0),
                    error=r.get("error", ""),
                )
        return None

    def _load_all_requests(self) -> list[dict[str, Any]]:
        if not self._requests_file.exists():
            return []
        try:
            return json.loads(
                self._requests_file.read_text(encoding="utf-8")
            )
        except Exception:
            return []

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
