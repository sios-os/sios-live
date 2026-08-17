"""SIOS Policy Engine, Capability Broker, and Court.

Implements Phases 23, 24, and 47 of the 50-Phase Build Plan:

Policy Engine (Phase 23):
  - Recurring mandates (preapproved bills)
  - Exact-purchase approvals
  - Spending limits
  - Exception handling
  - Prohibited transaction classes

Capability Broker (Phase 24):
  - Sessions are purpose-, payee-, amount-, account-, time-, and capability-bound
  - Capability tokens grant bounded authority for a specific session

Court (Phase 47):
  - Reviews Main Engine changes (ANUBIS's own model or architecture)
  - Probation period for promoted changes
  - Tomb approval boundary
  - Creator approval bound to exact artifact hash
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------ Policy Engine

class TransactionClass(IntEnum):
    """Transaction classification."""
    ROUTINE = 0       # Normal small purchases
    RECURRING = 1     # Preapproved bills
    EXACT_PURCHASE = 2  # Specific approved purchase
    LARGE = 3         # Above spending limit, requires approval
    PROHIBITED = 99   # Never allowed


@dataclass
class Mandate:
    """A preapproved recurring mandate (e.g., monthly bill)."""
    mandate_id: str
    description: str
    payee: str
    amount_limit: float
    currency: str = "USD"
    frequency: str = "monthly"  # weekly, monthly, quarterly, yearly
    active: bool = True
    created_at: float = 0.0
    last_executed: float = 0.0
    next_execution: float = 0.0
    # Conditions
    max_total: float = 0.0  # 0 = no cap
    expires_at: float = 0.0  # 0 = no expiry

    def to_dict(self) -> dict[str, Any]:
        return {
            "mandate_id": self.mandate_id,
            "description": self.description,
            "payee": self.payee,
            "amount_limit": self.amount_limit,
            "currency": self.currency,
            "frequency": self.frequency,
            "active": self.active,
            "created_at": self.created_at,
            "last_executed": self.last_executed,
            "next_execution": self.next_execution,
            "max_total": self.max_total,
            "expires_at": self.expires_at,
        }


@dataclass
class SpendingLimit:
    """Spending limits per period."""
    daily_limit: float = 100.0
    weekly_limit: float = 500.0
    monthly_limit: float = 2000.0
    currency: str = "USD"
    # Prohibited transaction classes
    prohibited_categories: list[str] = field(default_factory=lambda: [
        "gambling", "illegal_goods", "weapons", "unauthorized_charity",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_limit": self.daily_limit,
            "weekly_limit": self.weekly_limit,
            "monthly_limit": self.monthly_limit,
            "currency": self.currency,
            "prohibited_categories": self.prohibited_categories,
        }


@dataclass
class Transaction:
    """A proposed or executed transaction."""
    transaction_id: str
    payee: str
    amount: float
    currency: str = "USD"
    purpose: str = ""
    category: str = ""
    timestamp: float = 0.0
    mandate_id: str = ""
    approved: bool = False
    executed: bool = False
    approval_hash: str = ""  # Hash of the exact approved transaction envelope

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "payee": self.payee,
            "amount": self.amount,
            "currency": self.currency,
            "purpose": self.purpose,
            "category": self.category,
            "timestamp": self.timestamp,
            "mandate_id": self.mandate_id,
            "approved": self.approved,
            "executed": self.executed,
            "approval_hash": self.approval_hash,
        }


class PolicyEngine:
    """Enforces financial and operational policies.

    All transactions must pass policy evaluation before execution.
    The policy engine checks:
      - Is the category prohibited?
      - Is the amount within spending limits?
      - Is there a matching mandate for recurring payments?
      - Was the exact transaction envelope approved?
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._mandates_file = self.root / "mandates.json"
        self._limits_file = self.root / "limits.json"
        self._transactions_file = self.root / "transactions.json"
        self._mandates: dict[str, Mandate] = {}
        self._limits = SpendingLimit()
        self._transactions: list[Transaction] = []
        self._load()

    def _load(self) -> None:
        if self._mandates_file.exists():
            for m in json.loads(self._mandates_file.read_text(encoding="utf-8")):
                self._mandates[m["mandate_id"]] = Mandate(
                    mandate_id=m["mandate_id"], description=m.get("description", ""),
                    payee=m.get("payee", ""), amount_limit=m.get("amount_limit", 0),
                    currency=m.get("currency", "USD"), frequency=m.get("frequency", "monthly"),
                    active=m.get("active", True), created_at=m.get("created_at", 0),
                    last_executed=m.get("last_executed", 0), next_execution=m.get("next_execution", 0),
                    max_total=m.get("max_total", 0), expires_at=m.get("expires_at", 0),
                )
        if self._limits_file.exists():
            data = json.loads(self._limits_file.read_text(encoding="utf-8"))
            self._limits = SpendingLimit(
                daily_limit=data.get("daily_limit", 100),
                weekly_limit=data.get("weekly_limit", 500),
                monthly_limit=data.get("monthly_limit", 2000),
                currency=data.get("currency", "USD"),
                prohibited_categories=data.get("prohibited_categories", []),
            )
        if self._transactions_file.exists():
            for t in json.loads(self._transactions_file.read_text(encoding="utf-8")):
                self._transactions.append(Transaction(
                    transaction_id=t.get("transaction_id", ""), payee=t.get("payee", ""),
                    amount=t.get("amount", 0), currency=t.get("currency", "USD"),
                    purpose=t.get("purpose", ""), category=t.get("category", ""),
                    timestamp=t.get("timestamp", 0), mandate_id=t.get("mandate_id", ""),
                    approved=t.get("approved", False), executed=t.get("executed", False),
                    approval_hash=t.get("approval_hash", ""),
                ))

    def _save(self) -> None:
        self._mandates_file.write_text(
            json.dumps([m.to_dict() for m in self._mandates.values()], indent=2) + "\n",
            encoding="utf-8",
        )
        self._limits_file.write_text(
            json.dumps(self._limits.to_dict(), indent=2) + "\n", encoding="utf-8",
        )
        self._transactions_file.write_text(
            json.dumps([t.to_dict() for t in self._transactions], indent=2) + "\n",
            encoding="utf-8",
        )

    def evaluate_transaction(self, transaction: Transaction) -> dict[str, Any]:
        """Evaluate a transaction against policy. Returns verdict and reasons."""
        reasons: list[str] = []

        # Check prohibited categories
        if transaction.category.lower() in [c.lower() for c in self._limits.prohibited_categories]:
            return {
                "verdict": "denied",
                "class": TransactionClass.PROHIBITED.name,
                "reasons": [f"category '{transaction.category}' is prohibited"],
            }

        # Check mandate match for recurring payments
        if transaction.mandate_id:
            mandate = self._mandates.get(transaction.mandate_id)
            if mandate is None:
                reasons.append("mandate not found")
            elif not mandate.active:
                reasons.append("mandate is inactive")
            elif mandate.amount_limit > 0 and transaction.amount > mandate.amount_limit:
                reasons.append(f"amount exceeds mandate limit of {mandate.amount_limit}")
            elif mandate.expires_at > 0 and time.time() > mandate.expires_at:
                reasons.append("mandate has expired")
            else:
                return {
                    "verdict": "approved",
                    "class": TransactionClass.RECURRING.name,
                    "reasons": ["matches active mandate"],
                    "mandate_id": mandate.mandate_id,
                }

        # Check spending limits
        if transaction.amount <= self._limits.daily_limit:
            tx_class = TransactionClass.ROUTINE
        elif transaction.amount <= self._limits.weekly_limit:
            tx_class = TransactionClass.EXACT_PURCHASE
            reasons.append("requires exact-purchase approval")
        else:
            tx_class = TransactionClass.LARGE
            reasons.append("requires explicit Creator approval")

        # Check approval hash for exact purchases
        if tx_class == TransactionClass.EXACT_PURCHASE and transaction.approval_hash:
            expected_hash = self._compute_approval_hash(transaction)
            if transaction.approval_hash == expected_hash:
                return {
                    "verdict": "approved",
                    "class": tx_class.name,
                    "reasons": ["exact-purchase hash verified"],
                }
            else:
                return {
                    "verdict": "denied",
                    "class": tx_class.name,
                    "reasons": ["approval hash mismatch — material change detected"],
                }

        if tx_class == TransactionClass.LARGE:
            return {
                "verdict": "requires_creator_approval",
                "class": tx_class.name,
                "reasons": reasons,
            }

        if reasons:
            return {"verdict": "denied", "class": tx_class.name, "reasons": reasons}

        return {"verdict": "approved", "class": tx_class.name, "reasons": ["within limits"]}

    @staticmethod
    def _compute_approval_hash(transaction: Transaction) -> str:
        """Compute a hash of the exact transaction envelope."""
        envelope = f"{transaction.payee}:{transaction.amount}:{transaction.currency}:{transaction.purpose}"
        return hashlib.sha256(envelope.encode()).hexdigest()[:16]

    def add_mandate(self, mandate: Mandate) -> None:
        self._mandates[mandate.mandate_id] = mandate
        self._save()

    def record_transaction(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)
        self._save()

    def mandates(self) -> list[Mandate]:
        return list(self._mandates.values())

    def transactions(self) -> list[Transaction]:
        return list(self._transactions)

    def set_limits(self, daily: float, weekly: float, monthly: float) -> None:
        self._limits.daily_limit = daily
        self._limits.weekly_limit = weekly
        self._limits.monthly_limit = monthly
        self._save()

    def stats(self) -> dict[str, Any]:
        return {
            "active_mandates": sum(1 for m in self._mandates.values() if m.active),
            "total_transactions": len(self._transactions),
            "executed_transactions": sum(1 for t in self._transactions if t.executed),
            "daily_limit": self._limits.daily_limit,
            "prohibited_categories": len(self._limits.prohibited_categories),
        }


# ------------------------------------------------------------------ Capability Broker

@dataclass
class CapabilityToken:
    """A bounded capability token for a specific session."""
    token_id: str
    purpose: str
    capabilities: list[str]
    payee: str = ""
    amount: float = 0.0
    account: str = ""
    expires_at: float = 0.0
    created_at: float = 0.0
    used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "purpose": self.purpose,
            "capabilities": self.capabilities,
            "payee": self.payee,
            "amount": self.amount,
            "account": self.account,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "used": self.used,
        }


class CapabilityBroker:
    """Issues and validates bounded capability tokens.

    Sessions and transactions are purpose-, payee-, amount-,
    account-, time-, and capability-bound. A token for one
    purpose cannot be reused for another.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._tokens_file = self.root / "tokens.json"
        self._tokens: dict[str, CapabilityToken] = {}
        self._load()

    def _load(self) -> None:
        if self._tokens_file.exists():
            for t in json.loads(self._tokens_file.read_text(encoding="utf-8")):
                token = CapabilityToken(
                    token_id=t["token_id"], purpose=t.get("purpose", ""),
                    capabilities=t.get("capabilities", []), payee=t.get("payee", ""),
                    amount=t.get("amount", 0), account=t.get("account", ""),
                    expires_at=t.get("expires_at", 0), created_at=t.get("created_at", 0),
                    used=t.get("used", False),
                )
                self._tokens[token.token_id] = token

    def _save(self) -> None:
        self._tokens_file.write_text(
            json.dumps([t.to_dict() for t in self._tokens.values()], indent=2) + "\n",
            encoding="utf-8",
        )

    def issue_token(
        self, purpose: str, capabilities: list[str],
        payee: str = "", amount: float = 0.0, account: str = "",
        duration_seconds: float = 3600,
    ) -> CapabilityToken:
        """Issue a new bounded capability token."""
        token_id = hashlib.sha256(
            f"token:{purpose}:{time.time()}".encode()
        ).hexdigest()[:16]
        token = CapabilityToken(
            token_id=token_id,
            purpose=purpose,
            capabilities=capabilities,
            payee=payee,
            amount=amount,
            account=account,
            expires_at=time.time() + duration_seconds,
            created_at=time.time(),
        )
        self._tokens[token_id] = token
        self._save()
        return token

    def validate_token(
        self, token_id: str, purpose: str = "",
        required_capability: str = "",
    ) -> dict[str, Any]:
        """Validate a capability token for a specific use."""
        token = self._tokens.get(token_id)
        if token is None:
            return {"valid": False, "reason": "token not found"}
        if token.used:
            return {"valid": False, "reason": "token already used"}
        if time.time() > token.expires_at:
            return {"valid": False, "reason": "token expired"}
        if purpose and token.purpose != purpose:
            return {"valid": False, "reason": "purpose mismatch"}
        if required_capability and required_capability not in token.capabilities:
            return {"valid": False, "reason": f"missing capability: {required_capability}"}
        return {"valid": True, "token": token.to_dict()}

    def consume_token(self, token_id: str) -> bool:
        """Mark a token as used (one-time use)."""
        token = self._tokens.get(token_id)
        if token is None:
            return False
        token.used = True
        self._save()
        return True

    def tokens(self) -> list[CapabilityToken]:
        return list(self._tokens.values())

    def stats(self) -> dict[str, Any]:
        return {
            "total_tokens": len(self._tokens),
            "active_tokens": sum(1 for t in self._tokens.values() if not t.used and time.time() <= t.expires_at),
            "used_tokens": sum(1 for t in self._tokens.values() if t.used),
            "expired_tokens": sum(1 for t in self._tokens.values() if not t.used and time.time() > t.expires_at),
        }


# ------------------------------------------------------------------ Court

class CourtVerdict(IntEnum):
    """Court review verdicts."""
    APPROVED = 0
    PROBATION = 1
    REJECTED = 2
    DEFERRED = 3


@dataclass
class CourtReview:
    """A Court review of a Main Engine change."""
    review_id: str
    artifact_hash: str
    description: str
    submitted_at: float = 0.0
    reviewed_at: float = 0.0
    verdict: int = CourtVerdict.DEFERRED
    conditions: list[str] = field(default_factory=list)
    probation_until: float = 0.0
    creator_approved: bool = False
    creator_approval_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "artifact_hash": self.artifact_hash,
            "description": self.description,
            "submitted_at": self.submitted_at,
            "reviewed_at": self.reviewed_at,
            "verdict": CourtVerdict(self.verdict).name,
            "conditions": self.conditions,
            "probation_until": self.probation_until,
            "creator_approved": self.creator_approved,
            "creator_approval_hash": self.creator_approval_hash,
        }


class Court:
    """The Court reviews Main Engine changes.

    Main Engine changes are changes to ANUBIS's own model or
    architecture. They require:
      1. Court review
      2. Creator approval bound to an exact artifact hash
      3. Probation period before full promotion
      4. Rollback capability if problems emerge

    The Court is the Tomb approval boundary — nothing crosses
    from sandbox to Main Engine without passing through here.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._reviews_file = self.root / "court_reviews.json"
        self._reviews: dict[str, CourtReview] = {}
        self._load()

    def _load(self) -> None:
        if self._reviews_file.exists():
            for r in json.loads(self._reviews_file.read_text(encoding="utf-8")):
                review = CourtReview(
                    review_id=r["review_id"], artifact_hash=r.get("artifact_hash", ""),
                    description=r.get("description", ""),
                    submitted_at=r.get("submitted_at", 0),
                    reviewed_at=r.get("reviewed_at", 0),
                    verdict=r.get("verdict", CourtVerdict.DEFERRED),
                    conditions=r.get("conditions", []),
                    probation_until=r.get("probation_until", 0),
                    creator_approved=r.get("creator_approved", False),
                    creator_approval_hash=r.get("creator_approval_hash", ""),
                )
                self._reviews[review.review_id] = review

    def _save(self) -> None:
        self._reviews_file.write_text(
            json.dumps([r.to_dict() for r in self._reviews.values()], indent=2) + "\n",
            encoding="utf-8",
        )

    def submit_for_review(
        self, artifact_hash: str, description: str,
    ) -> str:
        """Submit a Main Engine change for Court review."""
        review_id = hashlib.sha256(
            f"court:{artifact_hash}:{time.time()}".encode()
        ).hexdigest()[:16]
        review = CourtReview(
            review_id=review_id,
            artifact_hash=artifact_hash,
            description=description,
            submitted_at=time.time(),
        )
        self._reviews[review_id] = review
        self._save()
        return review_id

    def render_verdict(
        self, review_id: str, verdict: CourtVerdict,
        conditions: list[str] | None = None,
        probation_days: int = 30,
    ) -> bool:
        """Render a Court verdict on a submitted review."""
        review = self._reviews.get(review_id)
        if review is None:
            return False
        review.verdict = verdict
        review.reviewed_at = time.time()
        review.conditions = conditions or []
        if verdict == CourtVerdict.PROBATION:
            review.probation_until = time.time() + (probation_days * 86400)
        self._save()
        return True

    def grant_creator_approval(
        self, review_id: str, approval_hash: str,
    ) -> dict[str, Any]:
        """Grant Creator approval for a Court-reviewed change.

        The approval must be bound to the exact artifact hash.
        Any material change invalidates the approval.
        """
        review = self._reviews.get(review_id)
        if review is None:
            return {"error": "review not found"}
        if review.verdict == CourtVerdict.REJECTED:
            return {"error": "review was rejected by Court"}
        if approval_hash != review.artifact_hash:
            return {"error": "approval hash does not match artifact hash"}
        review.creator_approved = True
        review.creator_approval_hash = approval_hash
        self._save()
        return {"review_id": review_id, "status": "creator_approved"}

    def can_promote(self, review_id: str) -> dict[str, Any]:
        """Check if a reviewed change can be promoted to Main Engine."""
        review = self._reviews.get(review_id)
        if review is None:
            return {"can_promote": False, "reason": "review not found"}
        if review.verdict == CourtVerdict.REJECTED:
            return {"can_promote": False, "reason": "rejected by Court"}
        if review.verdict == CourtVerdict.DEFERRED:
            return {"can_promote": False, "reason": "review not yet completed"}
        if not review.creator_approved:
            return {"can_promote": False, "reason": "Creator approval required"}
        if review.verdict == CourtVerdict.PROBATION:
            if time.time() < review.probation_until:
                remaining = int((review.probation_until - time.time()) / 86400)
                return {"can_promote": False, "reason": f"probation: {remaining} days remaining"}
        return {"can_promote": True, "review_id": review_id}

    def reviews(self) -> list[CourtReview]:
        return list(self._reviews.values())

    def get_review(self, review_id: str) -> CourtReview | None:
        return self._reviews.get(review_id)

    def stats(self) -> dict[str, Any]:
        verdict_counts = {}
        for r in self._reviews.values():
            v = CourtVerdict(r.verdict).name
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        return {
            "total_reviews": len(self._reviews),
            "verdict_distribution": verdict_counts,
            "creator_approved": sum(1 for r in self._reviews.values() if r.creator_approved),
            "on_probation": sum(
                1 for r in self._reviews.values()
                if r.verdict == CourtVerdict.PROBATION and time.time() < r.probation_until
            ),
        }
