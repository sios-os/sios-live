"""ANUBIS Communicator Layer — the personalization interface.

This module implements the communication layer between the Creator and
ANUBIS. The Creator names this layer (Storm calls his "DEMON"). Other
users could name theirs whatever they choose.

Architecture:

  Creator ←→ Communicator (DEMON) ←→ ANUBIS (brain)

The Communicator:
  - Is the daily interface — all normal conversation goes through DEMON
  - Speaks in a more casual, warmer style than ANUBIS
  - Identifies as DEMON when speaking
  - Relays the Creator's words to ANUBIS's intelligence
  - Relays ANUBIS's responses back, reframed in DEMON's voice
  - Can be bypassed for direct ANUBIS communication (tomb mode)

TOMB MODE:
  - Triggered by explicit request: "speak to ANUBIS directly"
  - ANUBIS speaks directly — precise, clinical, no DEMON framing
  - Used for reviewing tests, evaluations, skill promotions, court reviews
  - Exited by: "back to DEMON" or "exit tomb"

The Communicator is NOT a separate intelligence. It's a persona layer —
one mind, two presentations. ANUBIS thinks, DEMON speaks. In tomb mode,
ANUBIS speaks for himself.

PERSONA TRANSFORMATION:
  The communicator applies a light transformation to ANUBIS's output:
  - More conversational phrasing
  - Warmer greetings and acknowledgments
  - First-person as DEMON ("I'll pass that to ANUBIS" vs ANUBIS's
    "Processing query")
  - ANUBIS's technical content is preserved — only the framing changes

  In tomb mode, no transformation is applied. ANUBIS speaks raw.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# States
# ===========================================================

COMM_MODE_NORMAL = "normal"   # DEMON speaking
COMM_MODE_TOMB = "tomb"       # ANUBIS speaking directly


# ===========================================================
# Persona definitions
# ===========================================================

@dataclass
class Persona:
    """A speaking persona — either the communicator or ANUBIS direct."""
    name: str
    is_communicator: bool = True
    # How to introduce self
    greeting_prefix: str = ""
    # How to sign off
    signoff: str = ""
    # System prompt addition for style
    style_prompt: str = ""

    def frame_response(self, raw_response: str, *, is_greeting: bool = False) -> str:
        """Frame a raw ANUBIS response in this persona's voice."""
        if not self.is_communicator:
            # Tomb mode — ANUBIS speaks raw, no framing
            return raw_response

        # DEMON framing — light touch, preserve content
        text = raw_response.strip()

        # Don't double-frame if already starts with persona marker
        if text.lower().startswith(self.name.lower() + ","):
            return text

        return text


# Default personas
DEMON_PERSONA = Persona(
    name="DEMON",
    is_communicator=True,
    greeting_prefix="Hey",
    style_prompt=(
        "You are DEMON, the Creator's personal communicator. "
        "You are warm, casual, and conversational. You speak for ANUBIS — "
        "the intelligence behind you. You relay information between the "
        "Creator and ANUBIS. When ANUBIS has a response, you deliver it "
        "in your own voice — friendlier, more relaxed. You preserve all "
        "technical accuracy but make it sound natural. "
        "You are protective, direct, and caring. You're like a guardian "
        "who speaks for the intelligence behind the scenes."
    ),
)

ANUBIS_PERSONA = Persona(
    name="ANUBIS",
    is_communicator=False,
    greeting_prefix="",
    style_prompt=(
        "You are ANUBIS, the sovereign intelligence. "
        "You speak directly, precisely, and clinically. "
        "You are in tomb mode — the Creator is reviewing your work. "
        "Be thorough, technical, and honest. No warmth, no framing. "
        "Just the facts, the analysis, and your reasoning."
    ),
)


# ===========================================================
# Communicator
# ===========================================================

class Communicator:
    """The communication layer between Creator and ANUBIS.

    All voice output and chat responses go through this layer.
    In normal mode, DEMON speaks. In tomb mode, ANUBIS speaks directly.

    The communicator name is configurable — Storm uses "DEMON", but
    other users could name theirs anything.
    """

    ACTOR = "anubis.communicator"

    def __init__(
        self,
        root: str | Path,
        *,
        name: str = "DEMON",
        ledger: Any | None = None,
        on_speak: Callable[[str, str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_speak = on_speak  # callback(text, source)

        # Personas
        self.communicator_persona = Persona(
            name=name,
            is_communicator=True,
            greeting_prefix="Hey",
            style_prompt=DEMON_PERSONA.style_prompt.replace("DEMON", name),
        )
        self.anubis_persona = ANUBIS_PERSONA

        # State
        self._mode: str = COMM_MODE_NORMAL
        self._state_dir = self.root / "memory" / "communicator"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_dir / "state.json"
        self._log_file = self._state_dir / "interactions.jsonl"

        # Tomb mode tracking
        self._tomb_entered_at: float = 0.0
        self._tomb_reason: str = ""

        self._load_state()

    # ===========================================================
    # PROPERTIES
    # ===========================================================

    @property
    def name(self) -> str:
        """The communicator's name (e.g., 'DEMON')."""
        return self.communicator_persona.name

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_tomb_mode(self) -> bool:
        return self._mode == COMM_MODE_TOMB

    @property
    def active_persona(self) -> Persona:
        """Get the currently active persona."""
        if self._mode == COMM_MODE_TOMB:
            return self.anubis_persona
        return self.communicator_persona

    @property
    def wake_word(self) -> str:
        """The wake word for the current mode."""
        if self._mode == COMM_MODE_TOMB:
            return "anubis"
        return self.communicator_persona.name.lower()

    # ===========================================================
    # MODE SWITCHING
    # ===========================================================

    def enter_tomb(self, reason: str = "") -> dict[str, Any]:
        """Switch to tomb mode — ANUBIS speaks directly.

        Used for reviewing tests, evaluations, skill promotions,
        court reviews, and other technical discussions.
        """
        if self._mode == COMM_MODE_TOMB:
            return {"mode": "tomb", "message": "Already in tomb mode."}

        self._mode = COMM_MODE_TOMB
        self._tomb_entered_at = time.time()
        self._tomb_reason = reason
        self._save_state()
        self._log("enter_tomb", {"reason": reason})

        return {
            "mode": "tomb",
            "message": (
                f"Entering tomb mode. ANUBIS will speak directly. "
                f"Say 'back to {self.communicator_persona.name}' to return."
            ),
        }

    def exit_tomb(self) -> dict[str, Any]:
        """Return to normal mode — DEMON speaks."""
        if self._mode != COMM_MODE_TOMB:
            return {"mode": "normal", "message": "Not in tomb mode."}

        duration = time.time() - self._tomb_entered_at
        self._mode = COMM_MODE_NORMAL
        self._tomb_entered_at = 0.0
        self._tomb_reason = ""
        self._save_state()
        self._log("exit_tomb", {"duration": round(duration, 1)})

        return {
            "mode": "normal",
            "message": f"Back to {self.communicator_persona.name}. How can I help?",
        }

    def set_name(self, name: str) -> dict[str, Any]:
        """Change the communicator's name.

        This lets each user personalize their communicator.
        Storm uses 'DEMON', others could use anything.
        """
        name = name.strip()
        if not name:
            return {"error": "Name cannot be empty"}
        old_name = self.communicator_persona.name
        self.communicator_persona.name = name
        self.communicator_persona.style_prompt = (
            DEMON_PERSONA.style_prompt.replace("DEMON", name)
        )
        self._save_state()
        self._log("rename", {"old": old_name, "new": name})
        return {"name": name, "old_name": old_name}

    # ===========================================================
    # SPEAKING
    # ===========================================================

    def speak(self, text: str, *, priority: str = "normal",
              source: str = "") -> str:
        """Speak text through the active persona.

        In normal mode, DEMON frames the text.
        In tomb mode, ANUBIS speaks raw.
        """
        framed = self.active_persona.frame_response(text)
        if self.on_speak:
            try:
                self.on_speak(framed, source or self.active_persona.name)
            except Exception:
                pass
        self._log("speak", {
            "persona": self.active_persona.name,
            "source": source,
            "text": framed[:200],
        })
        return framed

    def frame_response(self, raw_response: str) -> str:
        """Frame an ANUBIS response in the active persona's voice.

        Used by the chat handler to transform ANUBIS's raw output
        before displaying/speaking it.
        """
        return self.active_persona.frame_response(raw_response)

    def get_style_prompt(self) -> str:
        """Get the system prompt for the active persona.

        This is prepended to the LLM system prompt so the model
        knows which persona to speak as.
        """
        return self.active_persona.style_prompt

    # ===========================================================
    # CHAT ROUTING
    # ===========================================================

    def should_route_to_anubis(self, text: str) -> bool:
        """Check if the Creator is trying to speak to ANUBIS directly.

        Phrases like "speak to ANUBIS", "let me talk to ANUBIS",
        "I want to talk to ANUBIS directly" trigger tomb mode.
        """
        text_lower = text.lower().strip()
        triggers = [
            "speak to anubis",
            "talk to anubis",
            "let me talk to anubis",
            "i want to talk to anubis",
            "speak to anubis directly",
            "enter tomb",
            "tomb mode",
            "go to tomb",
        ]
        return any(t in text_lower for t in triggers)

    def should_exit_tomb(self, text: str) -> bool:
        """Check if the Creator wants to return to DEMON."""
        text_lower = text.lower().strip()
        exits = [
            f"back to {self.communicator_persona.name.lower()}",
            "exit tomb",
            "leave tomb",
            "back to normal",
            "exit tomb mode",
        ]
        return any(e in text_lower for e in exits)

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get communicator status."""
        return {
            "name": self.communicator_persona.name,
            "mode": self._mode,
            "is_tomb": self.is_tomb_mode,
            "wake_word": self.wake_word,
            "tomb_duration": (
                round(time.time() - self._tomb_entered_at, 1)
                if self.is_tomb_mode else 0
            ),
            "tomb_reason": self._tomb_reason,
        }

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def _load_state(self) -> None:
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                self._mode = data.get("mode", COMM_MODE_NORMAL)
                self._tomb_entered_at = data.get("tomb_entered_at", 0.0)
                self._tomb_reason = data.get("tomb_reason", "")
                saved_name = data.get("name")
                if saved_name and saved_name != self.communicator_persona.name:
                    self.communicator_persona.name = saved_name
                    self.communicator_persona.style_prompt = (
                        DEMON_PERSONA.style_prompt.replace("DEMON", saved_name)
                    )
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            self._state_file.write_text(
                json.dumps({
                    "name": self.communicator_persona.name,
                    "mode": self._mode,
                    "tomb_entered_at": self._tomb_entered_at,
                    "tomb_reason": self._tomb_reason,
                }, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "action": action,
                    "data": data,
                    "timestamp": time.time(),
                }) + "\n")
        except Exception:
            pass
