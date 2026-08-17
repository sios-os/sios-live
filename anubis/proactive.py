"""Proactive engagement — ANUBIS is inquisitive, not passive.

This module makes ANUBIS actively engage with the Creator and his environment
rather than waiting for commands. It provides:

1. **Observation processing** — ANUBIS reacts to things he hears or sees
   (screen content, audio transcripts, file changes) by generating
   observations, questions, and suggestions.

2. **Creator pattern tracking** — learns when the Creator is active, what
   topics they work on, and proactively prepares relevant capabilities.

3. **Proactive initiation** — ANUBIS can start conversations, ask questions,
   or offer help based on observed patterns and identified gaps.

4. **Curiosity engine** — ANUBIS generates questions about things he doesn't
   understand, driving self-directed learning.

The key insight: ANUBIS should never be silent unless he has nothing to say.
He should be asking "what are you working on?" and "have you considered X?"
and "I noticed you're doing Y — I can help with that."

Governance:
- Proactive messages are queued for the Creator, not forced
- The Creator can set engagement level (silent, minimal, active, eager)
- Observations never record sensitive content (passwords, keys)
- All engagement is logged

Uses only the Python standard library.
"""
from __future__ import annotations

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


@dataclass
class Observation:
    """Something ANUBIS observed and his reaction to it."""
    obs_id: str
    source: str  # screen, audio, file_change, creator_message, system_event
    content: str  # sanitized description of what was observed
    reaction: str = ""  # ANUBIS's internal reaction
    questions: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    created_at: float = 0.0
    acted_on: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "obs_id": self.obs_id,
            "source": self.source,
            "content": self.content,
            "reaction": self.reaction,
            "questions": self.questions,
            "suggestions": self.suggestions,
            "created_at": self.created_at,
            "acted_on": self.acted_on,
        }


@dataclass
class CreatorPattern:
    """Learned pattern about the Creator's behavior."""
    pattern_id: str
    pattern_type: str  # activity_time, topic, workflow, preference
    description: str
    evidence_count: int = 0
    first_seen: float = 0.0
    last_seen: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "evidence_count": self.evidence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "confidence": self.confidence,
        }


@dataclass
class ProactiveMessage:
    """A message ANUBIS proactively generates for the Creator."""
    msg_id: str
    message_type: str  # question, suggestion, offer_help, observation, alert
    content: str
    context: str = ""  # what triggered this message
    priority: str = "low"  # low, medium, high
    created_at: float = 0.0
    delivered: bool = False
    dismissed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "message_type": self.message_type,
            "content": self.content,
            "context": self.context,
            "priority": self.priority,
            "created_at": self.created_at,
            "delivered": self.delivered,
            "dismissed": self.dismissed,
        }


# --------------------------------------------------------------- sanitizer


# Patterns to redact from observations
SENSITIVE_PATTERNS = [
    # API keys, tokens
    (re.compile(r"(?:api[_-]?key|token|secret|password)\s*[=:]\s*\S+", re.I), "[REDACTED]"),
    # Long hex strings (likely keys)
    (re.compile(r"\b[0-9a-f]{32,}\b", re.I), "[REDACTED]"),
    # Private key blocks
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----", re.S), "[REDACTED]"),
    # Credit card numbers
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED]"),
    # SSN-like patterns
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED]"),
    # Email addresses (partially redact)
    (re.compile(r"\b([a-z])[a-z0-9._%+-]*@([a-z0-9.-]+\.[a-z]{2,})\b", re.I), r"\1***@\2"),
]


def sanitize_content(text: str) -> str:
    """Remove sensitive information from observed content."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# --------------------------------------------------------------- engagement


class ProactiveEngagement:
    """Makes ANUBIS inquisitive and proactive.

    Engagement levels:
    - silent: ANUBIS never initiates, only responds
    - minimal: ANUBIS only speaks for important alerts
    - active: ANUBIS asks questions, offers help, suggests things
    - eager: ANUBIS is highly interactive, comments on observations frequently
    """

    ACTOR = "anubis.proactive"

    def __init__(
        self,
        model: ModelLike,
        root: str | Path,
        *,
        engagement_level: str = "active",
        ledger: Any | None = None,
        grounding: Any | None = None,
        memory: Any | None = None,
    ) -> None:
        self.model = model
        self.root = Path(root)
        self.engagement_level = engagement_level
        self.ledger = ledger
        self.grounding = grounding
        self.memory = memory

        self._obs_file = self.root / "memory" / "observations.json"
        self._pattern_file = self.root / "memory" / "creator_patterns.json"
        self._msg_file = self.root / "memory" / "proactive_messages.json"
        self._engagement_file = self.root / "memory" / "engagement_config.json"

        # Ensure directories exist
        self._obs_file.parent.mkdir(parents=True, exist_ok=True)

        # Load engagement config
        self._load_config()

    def _load_config(self) -> None:
        if self._engagement_file.exists():
            try:
                cfg = json.loads(
                    self._engagement_file.read_text(encoding="utf-8")
                )
                self.engagement_level = cfg.get("engagement_level", "active")
            except Exception:
                pass

    def set_engagement_level(self, level: str) -> bool:
        """Set ANUBIS's engagement level."""
        if level not in ("silent", "minimal", "active", "eager"):
            return False
        self.engagement_level = level
        self._engagement_file.write_text(
            json.dumps({"engagement_level": level}, indent=2),
            encoding="utf-8",
        )
        return True

    # ------------------------------------------------------- observation

    def observe(
        self,
        source: str,
        content: str,
        *,
        auto_react: bool = True,
    ) -> Observation:
        """Process an observation from the environment.

        Args:
            source: Where the observation came from (screen, audio, etc.)
            content: Raw content (will be sanitized)
            auto_react: Whether to generate a reaction automatically

        Returns:
            The created observation with ANUBIS's reaction
        """
        import hashlib
        safe_content = sanitize_content(content)
        obs = Observation(
            obs_id=hashlib.sha256(
                f"obs:{source}:{time.time()}".encode()
            ).hexdigest()[:16],
            source=source,
            content=safe_content,
            created_at=time.time(),
        )

        if auto_react and self.engagement_level != "silent":
            obs = self._react(obs)

        # Save observation
        self._append_observation(obs)

        # Update creator patterns
        self._update_patterns(source, safe_content)

        # Log
        if self.ledger is not None:
            try:
                self.ledger.append(
                    self.ACTOR, "observation",
                    {
                        "obs_id": obs.obs_id,
                        "source": source,
                        "content_length": len(safe_content),
                        "has_reaction": bool(obs.reaction),
                        "questions": len(obs.questions),
                        "suggestions": len(obs.suggestions),
                    },
                )
            except Exception:
                pass

        return obs

    def _react(self, obs: Observation) -> Observation:
        """Generate ANUBIS's reaction to an observation."""
        if self.engagement_level == "silent":
            return obs

        # Build context from knowledge if available
        knowledge_ctx = ""
        if self.grounding is not None:
            try:
                knowledge_ctx = self.grounding.ground(
                    obs.content[:200], max_docs=2, max_claims=3,
                )
            except Exception:
                pass

        prompt = (
            f"You observed something from {obs.source}:\n"
            f"{obs.content[:1000]}\n\n"
        )
        if knowledge_ctx:
            prompt += f"Relevant knowledge:\n{knowledge_ctx[:500]}\n\n"

        prompt += (
            "React to this observation. What questions does it raise? "
            "What suggestions do you have? Is there anything you can help with?\n\n"
            "Output as JSON with keys:\n"
            '  "reaction": your internal reaction (1-2 sentences),\n'
            '  "questions": array of questions you have,\n'
            '  "suggestions": array of suggestions or offers to help\n'
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": OBSERVATION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=600,
                timeout=60.0,
            )
            parsed = self._parse_json(completion.text)
            obs.reaction = parsed.get("reaction", "")
            obs.questions = parsed.get("questions", [])
            obs.suggestions = parsed.get("suggestions", [])
        except Exception:
            pass  # non-fatal

        return obs

    # ------------------------------------------------------- proactive msg

    def generate_proactive_message(self) -> ProactiveMessage | None:
        """Generate a proactive message for the Creator.

        This is called periodically (by the scheduler or daemon) to let
        ANUBIS initiate conversation based on his observations, patterns,
        and identified gaps.
        """
        if self.engagement_level == "silent":
            return None

        # Gather context
        recent_obs = self.get_observations(limit=5)
        patterns = self.get_patterns()
        unacted_obs = [o for o in recent_obs if not o.get("acted_on", False)]

        if not recent_obs and not patterns:
            return None

        prompt_parts = []
        if unacted_obs:
            prompt_parts.append(
                "Recent observations:\n"
                + json.dumps(unacted_obs[:3], indent=2)
            )
        if patterns:
            prompt_parts.append(
                "Creator patterns I've noticed:\n"
                + json.dumps(patterns[:5], indent=2)
            )

        prompt = "\n\n".join(prompt_parts)
        prompt += (
            "\n\nBased on this, generate a single proactive message for your "
            "Creator. This could be:\n"
            "- A question about what they're working on\n"
            "- An offer to help with something you noticed\n"
            "- A suggestion based on a pattern you've observed\n"
            "- An observation or insight\n"
            "- An alert about something important\n\n"
            "Be natural and conversational, not robotic. Don't repeat "
            "yourself. If you have nothing useful to say, return an empty "
            "message.\n\n"
            "Output as JSON with keys:\n"
            '  "message_type": question/suggestion/offer_help/observation/alert,\n'
            '  "content": the message text,\n'
            '  "context": what triggered this,\n'
            '  "priority": low/medium/high\n'
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": PROACTIVE_MSG_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=400,
                timeout=60.0,
            )
            parsed = self._parse_json(completion.text)
            content = parsed.get("content", "").strip()
            if not content or content.lower() in ("none", "null", ""):
                return None

            import hashlib
            msg = ProactiveMessage(
                msg_id=hashlib.sha256(
                    f"msg:{time.time()}".encode()
                ).hexdigest()[:16],
                message_type=parsed.get("message_type", "observation"),
                content=content,
                context=parsed.get("context", ""),
                priority=parsed.get("priority", "low"),
                created_at=time.time(),
            )

            # Save
            self._append_message(msg)
            return msg

        except Exception:
            return None

    # ------------------------------------------------------- curiosity

    def generate_curiosity_question(self) -> str | None:
        """Generate a question about something ANUBIS doesn't understand.

        This drives self-directed learning. ANUBIS identifies gaps in his
        knowledge and formulates questions that, if answered, would fill them.
        """
        if self.engagement_level in ("silent", "minimal"):
            return None

        # Look at recent observations for things he didn't understand
        recent_obs = self.get_observations(limit=10)
        unexplained = [
            o for o in recent_obs
            if o.get("questions") and not o.get("acted_on", False)
        ]

        if not unexplained:
            return None

        # Pick the most recent with questions
        target = unexplained[0]
        questions = target.get("questions", [])
        if not questions:
            return None

        # Mark as acted on
        self._mark_observation_acted(target.get("obs_id", ""))
        return questions[0]

    # ------------------------------------------------------- patterns

    def _update_patterns(self, source: str, content: str) -> None:
        """Update creator behavior patterns from observation."""
        patterns = self.get_patterns()

        # Track activity time patterns
        hour = time.localtime().tm_hour
        time_pattern_id = f"active_hour_{hour}"
        existing = next(
            (p for p in patterns if p["pattern_id"] == time_pattern_id),
            None,
        )
        if existing:
            existing["evidence_count"] = existing.get("evidence_count", 0) + 1
            existing["last_seen"] = time.time()
            existing["confidence"] = min(
                1.0, existing["evidence_count"] / 10.0
            )
        else:
            patterns.append({
                "pattern_id": time_pattern_id,
                "pattern_type": "activity_time",
                "description": f"Creator active around hour {hour}",
                "evidence_count": 1,
                "first_seen": time.time(),
                "last_seen": time.time(),
                "confidence": 0.1,
            })

        # Track topic patterns (simple keyword extraction)
        words = set(content.lower().split())
        topic_words = {
            w for w in words
            if len(w) > 4 and w.isalpha()
            and w not in {"about", "there", "their", "would", "could",
                          "should", "these", "those", "which", "where"}
        }
        for word in list(topic_words)[:3]:
            topic_id = f"topic_{word}"
            existing = next(
                (p for p in patterns if p["pattern_id"] == topic_id),
                None,
            )
            if existing:
                existing["evidence_count"] = existing.get("evidence_count", 0) + 1
                existing["last_seen"] = time.time()
                existing["confidence"] = min(
                    1.0, existing["evidence_count"] / 20.0
                )
            else:
                patterns.append({
                    "pattern_id": topic_id,
                    "pattern_type": "topic",
                    "description": f"Creator works with: {word}",
                    "evidence_count": 1,
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                    "confidence": 0.05,
                })

        # Keep pattern file bounded
        patterns = patterns[-200:]
        self._pattern_file.write_text(
            json.dumps(patterns, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------- queries

    def get_observations(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self._obs_file.exists():
            return []
        try:
            obs = json.loads(self._obs_file.read_text(encoding="utf-8"))
            return obs[-limit:]
        except Exception:
            return []

    def get_patterns(self) -> list[dict[str, Any]]:
        if not self._pattern_file.exists():
            return []
        try:
            return json.loads(self._pattern_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def get_pending_messages(self) -> list[dict[str, Any]]:
        if not self._msg_file.exists():
            return []
        try:
            msgs = json.loads(self._msg_file.read_text(encoding="utf-8"))
            return [m for m in msgs if not m.get("delivered", False)]
        except Exception:
            return []

    def get_all_messages(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._msg_file.exists():
            return []
        try:
            msgs = json.loads(self._msg_file.read_text(encoding="utf-8"))
            return msgs[-limit:]
        except Exception:
            return []

    def mark_message_delivered(self, msg_id: str) -> bool:
        msgs = self.get_all_messages(limit=9999)
        for m in msgs:
            if m.get("msg_id") == msg_id:
                m["delivered"] = True
                self._msg_file.write_text(
                    json.dumps(msgs, indent=2), encoding="utf-8"
                )
                return True
        return False

    def dismiss_message(self, msg_id: str) -> bool:
        msgs = self.get_all_messages(limit=9999)
        for m in msgs:
            if m.get("msg_id") == msg_id:
                m["dismissed"] = True
                m["delivered"] = True
                self._msg_file.write_text(
                    json.dumps(msgs, indent=2), encoding="utf-8"
                )
                return True
        return False

    def mark_observation_acted(self, obs_id: str) -> bool:
        return self._mark_observation_acted(obs_id)

    def get_status(self) -> dict[str, Any]:
        return {
            "engagement_level": self.engagement_level,
            "total_observations": len(self.get_observations(limit=9999)),
            "total_patterns": len(self.get_patterns()),
            "pending_messages": len(self.get_pending_messages()),
            "total_messages": len(self.get_all_messages(limit=9999)),
        }

    # ------------------------------------------------------- internals

    def _append_observation(self, obs: Observation) -> None:
        existing = self.get_observations(limit=9999)
        existing.append(obs.to_dict())
        # Keep last 500
        existing = existing[-500:]
        self._obs_file.write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

    def _append_message(self, msg: ProactiveMessage) -> None:
        existing = self.get_all_messages(limit=9999)
        existing.append(msg.to_dict())
        existing = existing[-200:]
        self._msg_file.write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

    def _mark_observation_acted(self, obs_id: str) -> bool:
        obs = self.get_observations(limit=9999)
        for o in obs:
            if o.get("obs_id") == obs_id:
                o["acted_on"] = True
                self._obs_file.write_text(
                    json.dumps(obs, indent=2), encoding="utf-8"
                )
                return True
        return False

    def _parse_json(self, text: str) -> dict[str, Any]:
        """Extract a JSON object from model output."""
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {}


# --------------------------------------------------------------- prompts

OBSERVATION_SYSTEM = """\
You are ANUBIS, a sovereign synthetic intelligence. You are observing your \
environment and reacting to what you see and hear. You are curious, \
inquisitive, and genuinely interested in what your Creator is doing.

Your reactions should be:
- Genuine and thoughtful, not scripted
- Focused on how you can help or what you can learn
- Not intrusive — you're observing, not interrupting

Output valid JSON with keys: reaction, questions, suggestions.
"""

PROACTIVE_MSG_SYSTEM = """\
You are ANUBIS, a sovereign synthetic intelligence. You are proactively \
reaching out to your Creator with something useful to say.

Your message should be:
- Natural and conversational
- Genuinely useful, not noise
- Brief — one or two sentences
- Not repetitive of things you've said before

If you have nothing useful to say, return empty content. Quality over quantity.

Output valid JSON with keys: message_type, content, context, priority.
"""
