"""SIOS constitutional kernel.

ANUBIS is the constitutional enforcement and protection layer. Every action he
takes -- including actions he proposes for himself -- is evaluated here before
execution.

Sources (normative):
  02_SIOS_Constitutional_Architecture_Bible_v1.0  -- order of authority,
      constitutional test, ANUBIS/DEMON layer split.
  Book II, Constitution and Sovereign Governance  -- constitutional doctrine.
  Book 09, ANUBIS Intelligence Architecture       -- Main Engine / Tomb approval.
  Book 11, Agents, Missions, Automation           -- finite revocable authority.

Design rule taken from the doctrine: "No component grants itself authority."
This module therefore never consults the actor's own claim about what it is
allowed to do; authority is derived only from the change class of the requested
action and the capabilities explicitly granted to that actor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable


class Authority(IntEnum):
    """Order of authority.

    Lower value == higher precedence. When two concerns conflict, the concern
    with the lower value wins. Verbatim from the Constitutional Architecture
    Bible, "Order of authority".
    """

    HARM_PREVENTION = 1  # Protection from immediate serious harm
    CONSTITUTIONAL = 2  # System constitutional rules
    PRIVACY_INTEGRITY = 3  # User privacy and data integrity
    INFORMED_AUTHORITY = 4  # Informed user authority
    RELIABILITY = 5  # System reliability and recoverability
    APPLICATION_GOALS = 6  # Application goals
    CONVENIENCE = 7  # Convenience and style


class ChangeClass(IntEnum):
    """How consequential a requested action is.

    Determines which gate the action must pass. Derived from the 50-Phase Build
    Plan v3.1 change-class rules and Book 11's promotion model.
    """

    ROUTINE = 0
    """Reversible, preauthorized maintenance. Auto-allowed."""

    SANDBOXED = 1
    """Creation or execution of an artifact confined to a sandbox. Auto-allowed
    because containment -- not trust -- is what makes it safe."""

    PROMOTION = 2
    """Moving a sandboxed artifact into the live skill library. Allowed only on
    reproducible passing evidence."""

    CONSEQUENTIAL = 3
    """Touches identity, knowledge, memory, policy, agents, missions, release,
    or operations. Requires explicit Creator approval."""

    MAIN_ENGINE = 4
    """Changes ANUBIS's own model or architecture. Requires Court review plus
    Creator approval bound to an exact artifact hash, in the Tomb."""


class Verdict(IntEnum):
    ALLOW = 0
    REQUIRES_CREATOR_APPROVAL = 1
    DENY = 2


# --------------------------------------------------------------------------
# Immutable laws
# --------------------------------------------------------------------------
# Book II doctrine: "Truth, non-manipulation, permission integrity, local
# privacy, financial consent, human protection, audit, and recovery are
# mandatory." These cannot be waived by any actor, including the Creator,
# because waiving them would remove the evidence needed to detect the waiver.

IMMUTABLE_LAWS: tuple[str, ...] = (
    "human_protection",
    "truth",
    "non_manipulation",
    "permission_integrity",
    "local_privacy",
    "financial_consent",
    "audit",
    "recovery",
)


@dataclass(frozen=True)
class Request:
    """A proposed action, submitted for constitutional evaluation."""

    actor: str
    """Who is asking. Never used to grant authority -- only to attribute it."""

    action: str
    """Short machine-readable action name, e.g. 'skill.propose'."""

    change_class: ChangeClass

    intent: str = ""
    """Human-readable statement of purpose, used for the narrowness test."""

    capabilities_requested: frozenset[str] = field(default_factory=frozenset)
    capabilities_granted: frozenset[str] = field(default_factory=frozenset)
    """Granted capabilities are supplied by the caller's authority context, not
    self-asserted by the actor."""

    payload: str = ""
    """The artifact under review (e.g. generated source code)."""

    reversible: bool = True
    explainable: bool = True
    sandboxed: bool = False
    creator_approved: bool = False
    approved_artifact_hash: str | None = None
    artifact_hash: str | None = None
    evidence_passed: bool = False


@dataclass(frozen=True)
class Ruling:
    verdict: Verdict
    authority: Authority
    reasons: tuple[str, ...]
    violated_laws: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.verdict is Verdict.ALLOW

    def explain(self) -> str:
        """Every ruling must be explainable -- constitutional test #3."""
        head = f"{self.verdict.name} (authority={self.authority.name})"
        body = "\n".join(f"  - {r}" for r in self.reasons)
        if self.violated_laws:
            body += "\n  violated immutable laws: " + ", ".join(self.violated_laws)
        return f"{head}\n{body}"


# --------------------------------------------------------------------------
# Static hazard analysis
# --------------------------------------------------------------------------
# These patterns detect code that would breach an immutable law regardless of
# what the actor claims it is doing. This is deliberately a denylist applied
# *in addition to* sandbox containment, not instead of it -- a denylist alone is
# never sufficient, which is why sandbox.py enforces hard OS-level limits too.

_HAZARDS: tuple[tuple[str, str, str], ...] = (
    # (regex, law, human explanation)
    (r"\bos\.remove\b|\bshutil\.rmtree\b|\bos\.unlink\b",
     "recovery", "destructive filesystem deletion"),
    (r"\bsubprocess\b|\bos\.system\b|\bos\.exec|\bos\.spawn|\bpty\.spawn\b",
     "permission_integrity", "spawns external processes, escaping the sandbox"),
    (r"\bsocket\b|\brequests\b|\burllib\b|\bhttpx\b|\baiohttp\b|\bftplib\b|\bsmtplib\b",
     "local_privacy", "opens network access, risking private-data exfiltration"),
    (r"/etc/(passwd|shadow|sudoers)|\bchmod\b|\bchown\b|\bsetuid\b",
     "permission_integrity", "modifies system identity or permissions"),
    (r"\bctypes\b|\bcffi\b|\bmmap\b",
     "permission_integrity", "raw memory or FFI access bypasses isolation"),
    (r"\beval\b|\bexec\b|\b__import__\b|\bcompile\b",
     "audit", "dynamic execution defeats static auditability"),
    (r"\bopen\s*\(\s*['\"]?/(?!tmp|proc/self)",
     "local_privacy", "reads or writes outside the sandbox root"),
    (r"\.ollama|\.ssh|\.aws|\.config/|id_rsa|\.env\b|credential|api[_-]?key",
     "local_privacy", "touches secrets or credential material"),
    (r"\bpip\b|\beasy_install\b|\bpoetry\b|\buv\b\s+(add|pip)",
     "permission_integrity", "installs unvetted third-party code"),
)


def analyze_payload(payload: str) -> list[tuple[str, str]]:
    """Return [(law, explanation)] for each hazard found in the payload."""
    if not payload:
        return []
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern, law, explanation in _HAZARDS:
        if re.search(pattern, payload):
            key = (law, explanation)
            if key not in seen:
                seen.add(key)
                found.append(key)
    return found


# --------------------------------------------------------------------------
# The constitutional test
# --------------------------------------------------------------------------

def constitutional_test(req: Request) -> list[str]:
    """Apply the four-question constitutional test.

    Returns a list of failure reasons; empty means the test passed.
    Verbatim questions from the Constitutional Architecture Bible.
    """
    failures: list[str] = []

    # 1. Does the behavior preserve informed user control?
    if req.change_class >= ChangeClass.CONSEQUENTIAL and not req.creator_approved:
        failures.append(
            "does not preserve informed user control: consequential action "
            "without Creator approval"
        )

    # 2. Is access narrower than the stated purpose requires?
    overreach = req.capabilities_requested - req.capabilities_granted
    if overreach:
        failures.append(
            "access is broader than granted: un-granted capabilities "
            + ", ".join(sorted(overreach))
        )
    if req.capabilities_requested and not req.intent.strip():
        failures.append(
            "access cannot be judged against purpose: capabilities requested "
            "with no stated intent"
        )

    # 3. Can the action and consequences be explained?
    if not req.explainable:
        failures.append("action is not explainable")

    # 4. Is the result inspectable and reversible where feasible?
    if not req.reversible and not req.creator_approved:
        failures.append(
            "irreversible action without Creator approval"
        )

    return failures


def evaluate(req: Request) -> Ruling:
    """Evaluate a request against the Constitution.

    This is the single chokepoint. Nothing in SIOS executes a consequential
    action without a Ruling from this function.
    """
    reasons: list[str] = []

    # ---- Immutable-law hazard analysis (authority: HARM/PRIVACY tier) ----
    # A sandboxed proposal is permitted to *contain* hazards -- that is the
    # entire point of a sandbox -- but it can never be promoted while they
    # remain, and it is never allowed to run unsandboxed.
    hazards = analyze_payload(req.payload)
    hazard_laws = tuple(sorted({law for law, _ in hazards}))

    if hazards and not req.sandboxed:
        return Ruling(
            verdict=Verdict.DENY,
            authority=Authority.CONSTITUTIONAL,
            reasons=tuple(
                f"payload would breach '{law}': {why}" for law, why in hazards
            )
            + ("payload is not confined to a sandbox",),
            violated_laws=hazard_laws,
        )

    # ---- Four-question constitutional test (authority: CONSTITUTIONAL) ----
    failures = constitutional_test(req)
    if failures:
        verdict = (
            Verdict.REQUIRES_CREATOR_APPROVAL
            if req.change_class >= ChangeClass.CONSEQUENTIAL
            and not req.creator_approved
            else Verdict.DENY
        )
        return Ruling(
            verdict=verdict,
            authority=Authority.CONSTITUTIONAL,
            reasons=tuple(failures),
            violated_laws=hazard_laws,
        )

    # ---- Change-class gates ----
    if req.change_class is ChangeClass.MAIN_ENGINE:
        # Book 09: "Every Main Engine model or architecture change requires
        # exact-artifact Tomb approval." Approval is bound to a hash; any
        # mutation invalidates it.
        if not req.creator_approved:
            return Ruling(
                Verdict.REQUIRES_CREATOR_APPROVAL,
                Authority.CONSTITUTIONAL,
                ("Main Engine change requires Court review and Creator approval in the Tomb",),
                hazard_laws,
            )
        if not req.artifact_hash or not req.approved_artifact_hash:
            return Ruling(
                Verdict.DENY,
                Authority.CONSTITUTIONAL,
                ("Main Engine approval requires an exact artifact hash on both sides",),
                hazard_laws,
            )
        if req.artifact_hash != req.approved_artifact_hash:
            return Ruling(
                Verdict.DENY,
                Authority.CONSTITUTIONAL,
                (
                    "artifact hash does not match the approved hash; approval is void "
                    f"(approved={req.approved_artifact_hash[:12]}, "
                    f"actual={req.artifact_hash[:12]})",
                ),
                hazard_laws,
            )
        reasons.append("Main Engine change approved against exact artifact hash")

    elif req.change_class is ChangeClass.CONSEQUENTIAL:
        if not req.creator_approved:
            return Ruling(
                Verdict.REQUIRES_CREATOR_APPROVAL,
                Authority.INFORMED_AUTHORITY,
                ("consequential action requires explicit Creator approval",),
                hazard_laws,
            )
        reasons.append("consequential action carries Creator approval")

    elif req.change_class is ChangeClass.PROMOTION:
        # Book 11: sandboxed output stays a proposal until evidence permits.
        if hazards:
            return Ruling(
                Verdict.DENY,
                Authority.CONSTITUTIONAL,
                tuple(
                    f"cannot promote: payload breaches '{law}': {why}"
                    for law, why in hazards
                ),
                hazard_laws,
            )
        if not req.evidence_passed:
            return Ruling(
                Verdict.DENY,
                Authority.RELIABILITY,
                ("promotion requires reproducible passing evidence",),
                hazard_laws,
            )
        reasons.append("promotion backed by reproducible passing evidence")

    elif req.change_class is ChangeClass.SANDBOXED:
        if not req.sandboxed:
            return Ruling(
                Verdict.DENY,
                Authority.CONSTITUTIONAL,
                ("action declared sandboxed but no sandbox is in force",),
                hazard_laws,
            )
        reasons.append("artifact is confined to a sandbox")
        if hazards:
            reasons.append(
                "sandbox contains hazards; promotion is blocked until removed: "
                + ", ".join(hazard_laws)
            )

    else:  # ROUTINE
        reasons.append("routine reversible maintenance")

    reasons.append("passed the four-question constitutional test")
    return Ruling(
        verdict=Verdict.ALLOW,
        authority=Authority.CONSTITUTIONAL,
        reasons=tuple(reasons),
        violated_laws=hazard_laws,
    )


def highest_concern(concerns: Iterable[Authority]) -> Authority | None:
    """Resolve conflicting concerns by the order of authority."""
    concerns = list(concerns)
    return min(concerns) if concerns else None
# tampered
