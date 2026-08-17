"""Funding prospects system for ANUBIS.

This module searches for legitimate revenue and funding opportunities
(grants, freelance projects, bounties) through the external gateway,
evaluates them for legitimacy and feasibility, and stores them as
structured proposals for Creator approval.

ANUBIS must NOT:
  - Apply anonymously
  - Sign contracts
  - Represent itself as a legal entity
  - Move money without an approved mandate
  - Treat speculative returns as guaranteed
  - Execute investments merely because they appear profitable

The system produces proposals, not actions. Every proposal includes:
  - Opportunity source
  - Description
  - Eligibility
  - Estimated effort
  - Estimated cost
  - Estimated return or funding amount
  - Deadline
  - Feasibility assessment
  - Evidence and citations
  - Risks
  - Required Creator actions
  - Confidence/uncertainty indicators
  - Approval status

Approved proposals can be converted into bounded missions via the
existing mission queue.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Default prospect storage location
PROSPECTS_FILE = "prospects/prospects.json"

# Whitelisted opportunity sources (must match external_gateway policy)
DEFAULT_SOURCES = [
    "grants.gov",
    "findgrants.io",
    "grantable.co",
    "sentient.foundation",
    "upwork.com",
    "task-bounty.com",
    "codebounty.ai",
]

# Approval states
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUS_SUBMITTED = "submitted"  # Creator submitted the application


@dataclass
class Prospect:
    """A funding or revenue opportunity proposal."""
    id: str
    source: str  # e.g. "grants.gov", "upwork.com"
    source_url: str = ""
    title: str = ""
    description: str = ""
    opportunity_type: str = ""  # grant, contract, bounty, investment
    eligibility: str = ""
    estimated_effort_hours: float = 0.0
    estimated_cost: float = 0.0
    estimated_return: float = 0.0
    currency: str = "USD"
    deadline: str = ""  # ISO date string
    feasibility_score: float = 0.0  # 0.0 to 1.0
    confidence_score: float = 0.0  # 0.0 to 1.0
    risks: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    required_creator_actions: list[str] = field(default_factory=list)
    status: str = STATUS_PENDING
    created_at: float = 0.0
    updated_at: float = 0.0
    approved_at: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Prospect":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def is_actionable(self) -> bool:
        """True if the prospect has enough detail to be actionable."""
        return (
            bool(self.title)
            and bool(self.source)
            and self.feasibility_score > 0.0
            and bool(self.deadline)
        )

    @property
    def net_estimate(self) -> float:
        """Estimated net return (return - cost)."""
        return self.estimated_return - self.estimated_cost


class ProspectsStore:
    """Persistent storage for funding prospects.

    All prospects are stored in a single JSON file. The store supports
    adding, listing, updating, and filtering prospects by status.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or PROSPECTS_FILE)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._prospects: dict[str, Prospect] = {}
        self._load()

    def _load(self) -> None:
        """Load prospects from disk."""
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for item in data.get("prospects", []):
                p = Prospect.from_dict(item)
                self._prospects[p.id] = p
        except (json.JSONDecodeError, OSError):
            pass

    def _save(self) -> None:
        """Save prospects to disk."""
        data = {
            "prospects": [p.to_dict() for p in self._prospects.values()],
            "count": len(self._prospects),
            "updated_at": time.time(),
        }
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def add(self, prospect: Prospect) -> str:
        """Add a prospect. Returns the prospect ID."""
        if not prospect.created_at:
            prospect.created_at = time.time()
            prospect.updated_at = time.time()
        self._prospects[prospect.id] = prospect
        self._save()
        return prospect.id

    def get(self, prospect_id: str) -> Prospect | None:
        """Get a prospect by ID."""
        return self._prospects.get(prospect_id)

    def update(self, prospect_id: str, updates: dict[str, Any]) -> bool:
        """Update a prospect. Returns True if found and updated."""
        p = self._prospects.get(prospect_id)
        if not p:
            return False
        for k, v in updates.items():
            if k in Prospect.__dataclass_fields__:
                setattr(p, k, v)
        p.updated_at = time.time()
        self._save()
        return True

    def approve(self, prospect_id: str) -> bool:
        """Mark a prospect as approved by the Creator."""
        return self.update(prospect_id, {
            "status": STATUS_APPROVED,
            "approved_at": time.time(),
        })

    def reject(self, prospect_id: str) -> bool:
        """Mark a prospect as rejected by the Creator."""
        return self.update(prospect_id, {"status": STATUS_REJECTED})

    def list_all(self) -> list[Prospect]:
        """List all prospects."""
        return list(self._prospects.values())

    def list_by_status(self, status: str) -> list[Prospect]:
        """List prospects filtered by status."""
        return [p for p in self._prospects.values() if p.status == status]

    def list_pending(self) -> list[Prospect]:
        """List pending prospects awaiting Creator review."""
        return self.list_by_status(STATUS_PENDING)

    def list_approved(self) -> list[Prospect]:
        """List approved prospects."""
        return self.list_by_status(STATUS_APPROVED)

    def delete(self, prospect_id: str) -> bool:
        """Delete a prospect."""
        if prospect_id in self._prospects:
            del self._prospects[prospect_id]
            self._save()
            return True
        return False

    def stats(self) -> dict[str, Any]:
        """Return prospect statistics."""
        all_prospects = list(self._prospects.values())
        return {
            "total": len(all_prospects),
            "pending": sum(1 for p in all_prospects if p.status == STATUS_PENDING),
            "approved": sum(1 for p in all_prospects if p.status == STATUS_APPROVED),
            "rejected": sum(1 for p in all_prospects if p.status == STATUS_REJECTED),
            "expired": sum(1 for p in all_prospects if p.status == STATUS_EXPIRED),
            "submitted": sum(1 for p in all_prospects if p.status == STATUS_SUBMITTED),
            "avg_feasibility": (
                sum(p.feasibility_score for p in all_prospects) / len(all_prospects)
                if all_prospects else 0.0
            ),
            "avg_confidence": (
                sum(p.confidence_score for p in all_prospects) / len(all_prospects)
                if all_prospects else 0.0
            ),
            "total_estimated_return": sum(p.estimated_return for p in all_prospects),
        }


class ProspectsSystem:
    """Funding prospects search and evaluation system.

    Uses the external gateway to search for opportunities, evaluates
    them for legitimacy and feasibility, and stores them as proposals.
    """

    def __init__(
        self,
        store: ProspectsStore | None = None,
        gateway: Any | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.store = store or ProspectsStore()
        self.gateway = gateway
        self.ledger = ledger

    def _generate_id(self, source: str, title: str) -> str:
        """Generate a unique prospect ID."""
        import hashlib
        raw = f"{source}:{title}:{time.time()}"
        return "prospect_" + hashlib.sha256(raw.encode()).hexdigest()[:12]

    def search_opportunities(
        self,
        query: str,
        *,
        creator_approved: bool = False,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Search for funding opportunities through the gateway.

        Returns search results. The Creator must approve before
        ANUBIS can store these as prospects.
        """
        if self.gateway is None:
            return {"ok": False, "error": "no gateway configured"}

        resp = self.gateway.search(query, creator_approved=creator_approved)
        if not resp.ok:
            return {"ok": False, "error": resp.error, "refused": resp.refused_reason}

        # Parse results (format depends on the search API)
        # For now, return the raw response for the Creator to review
        return {
            "ok": True,
            "query": query,
            "results": resp.body[:5000],
            "logged": resp.logged,
        }

    def create_prospect(
        self,
        source: str,
        title: str,
        description: str = "",
        source_url: str = "",
        opportunity_type: str = "",
        eligibility: str = "",
        estimated_effort_hours: float = 0.0,
        estimated_cost: float = 0.0,
        estimated_return: float = 0.0,
        deadline: str = "",
        feasibility_score: float = 0.0,
        confidence_score: float = 0.0,
        risks: list[str] | None = None,
        evidence: list[str] | None = None,
        citations: list[str] | None = None,
        required_creator_actions: list[str] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        """Create a new prospect proposal.

        The prospect is stored with status 'pending' for Creator review.
        ANUBIS does not execute any actions — it only proposes.
        """
        prospect = Prospect(
            id=self._generate_id(source, title),
            source=source,
            source_url=source_url,
            title=title,
            description=description,
            opportunity_type=opportunity_type,
            eligibility=eligibility,
            estimated_effort_hours=estimated_effort_hours,
            estimated_cost=estimated_cost,
            estimated_return=estimated_return,
            deadline=deadline,
            feasibility_score=feasibility_score,
            confidence_score=confidence_score,
            risks=risks or [],
            evidence=evidence or [],
            citations=citations or [],
            required_creator_actions=required_creator_actions or [],
            notes=notes,
        )
        self.store.add(prospect)
        self._log_prospect(prospect, "created")
        return {
            "ok": True,
            "prospect_id": prospect.id,
            "status": prospect.status,
            "message": "Prospect created with status 'pending'. Creator must approve.",
        }

    def evaluate_prospect(self, prospect_id: str) -> dict[str, Any]:
        """Evaluate a prospect for legitimacy and feasibility.

        This is a structured assessment that checks:
        - Source legitimacy (is it in the whitelist?)
        - Feasibility score (0-1)
        - Confidence score (0-1)
        - Risk factors
        - Required Creator actions
        """
        p = self.store.get(prospect_id)
        if not p:
            return {"ok": False, "error": "prospect not found"}

        # Check source legitimacy
        source_legitimate = p.source in DEFAULT_SOURCES

        # Check if prospect is actionable
        actionable = p.is_actionable

        # Assess risks
        risk_factors = []
        if p.feasibility_score < 0.3:
            risk_factors.append("low feasibility score")
        if p.confidence_score < 0.3:
            risk_factors.append("low confidence in estimates")
        if not p.evidence:
            risk_factors.append("no supporting evidence")
        if not p.citations:
            risk_factors.append("no citations")
        if p.estimated_return > 0 and p.estimated_cost > p.estimated_return:
            risk_factors.append("estimated cost exceeds return")
        if not source_legitimate:
            risk_factors.append("source not in whitelist")

        return {
            "ok": True,
            "prospect_id": prospect_id,
            "source_legitimate": source_legitimate,
            "actionable": actionable,
            "feasibility": p.feasibility_score,
            "confidence": p.confidence_score,
            "risk_factors": risk_factors,
            "net_estimate": p.net_estimate,
            "recommendation": (
                "proceed" if source_legitimate and actionable and not risk_factors
                else "review" if source_legitimate and actionable
                else "reject"
            ),
        }

    def approve_prospect(self, prospect_id: str) -> dict[str, Any]:
        """Approve a prospect (Creator action).

        Approved prospects can be converted into missions.
        """
        if self.store.approve(prospect_id):
            p = self.store.get(prospect_id)
            self._log_prospect(p, "approved")
            return {
                "ok": True,
                "prospect_id": prospect_id,
                "status": STATUS_APPROVED,
                "message": "Prospect approved. Can be converted to a mission.",
            }
        return {"ok": False, "error": "prospect not found"}

    def reject_prospect(self, prospect_id: str) -> dict[str, Any]:
        """Reject a prospect (Creator action)."""
        if self.store.reject(prospect_id):
            p = self.store.get(prospect_id)
            self._log_prospect(p, "rejected")
            return {"ok": True, "prospect_id": prospect_id, "status": STATUS_REJECTED}
        return {"ok": False, "error": "prospect not found"}

    def list_pending(self) -> dict[str, Any]:
        """List pending prospects for Creator review."""
        prospects = self.store.list_pending()
        return {
            "prospects": [p.to_dict() for p in prospects],
            "count": len(prospects),
        }

    def list_approved(self) -> dict[str, Any]:
        """List approved prospects."""
        prospects = self.store.list_approved()
        return {
            "prospects": [p.to_dict() for p in prospects],
            "count": len(prospects),
        }

    def stats(self) -> dict[str, Any]:
        """Return prospect statistics."""
        return self.store.stats()

    def _log_prospect(self, prospect: Prospect, action: str) -> None:
        """Log a prospect action to the evidence ledger."""
        if self.ledger is None:
            return
        try:
            entry = {
                "type": "prospect",
                "action": action,
                "prospect_id": prospect.id,
                "source": prospect.source,
                "title": prospect.title,
                "status": prospect.status,
                "timestamp": time.time(),
            }
            self.ledger.append(entry)
        except Exception:
            pass

    def status(self) -> dict[str, Any]:
        """Return prospects system status."""
        return {
            "store_path": str(self.store.path),
            "gateway_connected": self.gateway is not None,
            "ledger_connected": self.ledger is not None,
            "default_sources": DEFAULT_SOURCES,
            "stats": self.store.stats(),
        }
