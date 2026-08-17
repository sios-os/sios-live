"""Sensory system — ANUBIS's ears, eyes, and voice.

This module makes ANUBIS fully always-on, like a person in the room:
- **Ears**: Ambient listening — always hears, understands context, acts on
  relevant speech without needing a wake word
- **Eyes**: Periodic screen capture and analysis
- **Voice**: Auto-speak for proactive messages, opinions, and responses

The sensory system runs as background threads alongside the scheduler.
ANUBIS hears everything in the room, classifies it, and decides what to
act on. He can add items to lists, offer opinions, or respond to direct
address — all without being summoned.

LISTENING MODES:
- **ambient**: Always listening, classifying speech, acting on relevant
  content. This is the default and the main mode. ANUBIS is like a
  person in the room who hears everything and responds when appropriate.
- **wake_word**: Only responds when his name is spoken. Useful for
  privacy-sensitive situations or when the Creator wants quiet.
- **conversation**: Active conversation mode — every utterance is treated
  as direct address. Used when ANUBIS is actively conversing.
- **privacy**: Listening paused entirely. ANUBIS can't hear anything.

AMBIENT SPEECH CLASSIFICATION:
When ANUBIS hears speech, he classifies it as:
- **direct_address**: Spoken TO ANUBIS (contains his name or is a
  question/command directed at him) → respond conversationally
- **self_talk**: Creator talking to themselves, thinking out loud →
  listen, learn, act on actionable content (e.g., "I need milk" → list)
- **conversation**: Creator talking to someone else → listen, learn
  context, don't interrupt unless something is directly relevant
- **noise**: Non-speech audio → ignore

AMBIENT ACTIONS:
ANUBIS can act on ambient speech without being asked:
- "I need to get milk after work" → adds to shopping list
- "I should call mom tomorrow" → creates reminder
- "This code is terrible" → offers to help refactor
- "I wonder if..." → may offer relevant knowledge
- "ANUBIS, what do you think?" → responds conversationally

He doesn't act on everything — he uses judgment about what's worth
responding to vs what's just thinking out loud. The model classifies
whether action is needed.

AUDIO PIPELINE:
1. Continuous recording in short chunks (2-3 seconds)
2. Energy detection — skip silence
3. If speech detected, transcribe
4. Classify speech (direct_address, self_talk, conversation, noise)
5. If direct_address → conversation handler → voice response
6. If self_talk with actionable content → extract action → confirm
7. If conversation → learn context, maybe offer relevant info
8. If noise → ignore

SCREEN PIPELINE:
1. Periodic screen capture (every N seconds)
2. OCR or description generation (if model available)
3. Feed to observer/proactive engagement
4. Generate observations and reactions

VOICE PIPELINE:
1. Proactive messages are queued
2. Background thread speaks them aloud
3. Rate-limited to avoid talking over the Creator
4. Can be muted/paused

All three systems degrade gracefully when tools aren't available:
- No microphone → text-only input
- No screen capture → no visual observation
- No TTS → text-only output

Uses only the Python standard library where possible.
External tools (arecord, espeak, scrot, etc.) are detected at runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


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
class AudioEvent:
    """An audio event detected by the listening system."""
    event_id: str
    event_type: str  # direct_address, self_talk, conversation, noise, silence
    timestamp: float = 0.0
    transcript: str = ""
    duration_s: float = 0.0
    energy: float = 0.0
    acted_on: bool = False
    action_taken: str = ""  # what ANUBIS did in response
    confidence: float = 0.0  # classification confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "transcript": self.transcript,
            "duration_s": self.duration_s,
            "energy": self.energy,
            "acted_on": self.acted_on,
            "action_taken": self.action_taken,
            "confidence": self.confidence,
        }


@dataclass
class AmbientAction:
    """An action ANUBIS takes based on ambient speech.

    Examples:
    - "I need milk" → action_type="add_to_list", content="milk"
    - "Call mom tomorrow" → action_type="create_reminder", content="call mom tomorrow"
    - "This code is terrible" → action_type="offer_help", content="refactor"
    """
    action_id: str
    action_type: str  # add_to_list, create_reminder, offer_help, offer_info, respond, note
    trigger_text: str  # what was said
    content: str  # what ANUBIS extracted
    response: str = ""  # what ANUBIS said/did
    confidence: float = 0.0
    timestamp: float = 0.0
    confirmed: bool = False  # did the Creator confirm/accept

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "trigger_text": self.trigger_text,
            "content": self.content,
            "response": self.response,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "confirmed": self.confirmed,
        }


@dataclass
class ScreenObservation:
    """A screen observation captured by the visual system."""
    obs_id: str
    timestamp: float = 0.0
    capture_path: str = ""
    description: str = ""  # text description or OCR result
    changes_detected: bool = False
    previous_description: str = ""
    acted_on: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "obs_id": self.obs_id,
            "timestamp": self.timestamp,
            "capture_path": self.capture_path,
            "description": self.description,
            "changes_detected": self.changes_detected,
            "previous_description": self.previous_description,
            "acted_on": self.acted_on,
        }


@dataclass
class SpeechRequest:
    """A request to speak something aloud."""
    req_id: str
    text: str
    priority: str = "normal"  # low, normal, high, immediate
    source: str = ""  # proactive, response, alert, system
    created_at: float = 0.0
    spoken: bool = False
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "text": self.text,
            "priority": self.priority,
            "source": self.source,
            "created_at": self.created_at,
            "spoken": self.spoken,
            "skipped": self.skipped,
        }


# --------------------------------------------------------------- audio ears


# Listening modes
MODE_AMBIENT = "ambient"       # Always listening, classifying, acting
MODE_WAKE_WORD = "wake_word"   # Only responds to wake word
MODE_CONVERSATION = "conversation"  # Every utterance is direct address
MODE_SLEEP = "sleep"           # Listening but only for wake-up voice commands
MODE_PRIVACY = "privacy"       # Listening paused entirely

# Speech classification types
SPEECH_DIRECT_ADDRESS = "direct_address"  # Spoken TO ANUBIS
SPEECH_SELF_TALK = "self_talk"            # Creator thinking out loud
SPEECH_CONVERSATION = "conversation"      # Creator talking to someone else
SPEECH_NOISE = "noise"                    # Non-speech audio


# ---------------------------------------------------------------
# voice command router
# ---------------------------------------------------------------

@dataclass
class VoiceCommand:
    """A registered voice command."""
    command_id: str
    phrases: list[str]           # exact phrases or substrings to match
    handler: Callable[[str], Any]
    description: str = ""
    # Which speech types trigger this command
    match_direct_address: bool = True   # "ANUBIS, goodnight"
    match_ambient: bool = True          # "goodnight" (said in ambient mode)
    match_self_talk: bool = True        # "I should say goodnight"
    match_conversation: bool = False    # talking to someone else
    # Whether to suppress the normal chat response when triggered
    suppress_chat: bool = True
    # Whether this command works in privacy mode (e.g., "good morning" to wake up)
    works_in_privacy: bool = False

    def matches(self, text: str, speech_type: str, in_privacy: bool) -> bool:
        """Check if this command matches the given text."""
        if in_privacy and not self.works_in_privacy:
            return False
        # Check speech type — ambient speech is classified as CONVERSATION
        # by the AudioListener, so match_ambient covers both CONVERSATION
        # and SELF_TALK (things said in ambient mode without the wake word)
        if speech_type == SPEECH_DIRECT_ADDRESS and not self.match_direct_address:
            return False
        if speech_type == SPEECH_SELF_TALK and not (self.match_self_talk or self.match_ambient):
            return False
        if speech_type == SPEECH_CONVERSATION and not (self.match_conversation or self.match_ambient):
            return False
        if speech_type == SPEECH_NOISE:
            return False
        # Check phrase match (case-insensitive, word-boundary aware)
        # Use regex word boundaries so "alarm" doesn't match "cancel alarm"
        import re
        text_lower = text.lower().strip()
        for phrase in self.phrases:
            pattern = r'\b' + re.escape(phrase.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return True
        return False


class VoiceCommandRouter:
    """Routes specific spoken phrases to handlers before they reach chat.

    This lets the Creator say things like "goodnight", "wake me up",
    or "good morning" and have them trigger actions directly, without
    going through the LLM chat handler.

    The router is checked FIRST in the speech processing pipeline.
    If a command matches, its handler is called and the normal
    chat/ambient processing is skipped (unless suppress_chat is False).

    Commands are matched case-insensitively as substrings. This means
    "goodnight" matches "goodnight", "ANUBIS, goodnight", "I'm going
    to say goodnight now", etc.

    Privacy mode handling:
    - Most commands are disabled in privacy mode (ANUBIS isn't listening)
    - Commands with works_in_privacy=True still fire (e.g., "good morning"
      needs to work when ANUBIS is in privacy mode during sleep)
    - The AudioListener doesn't process audio in privacy mode at all,
      so works_in_privacy is mainly for the SensorySystem wrapper which
      may process text from other sources (phone app, typed input)
    """

    def __init__(self) -> None:
        self._commands: list[VoiceCommand] = []

    def register(
        self,
        command_id: str,
        phrases: list[str],
        handler: Callable[[str], Any],
        *,
        description: str = "",
        match_direct_address: bool = True,
        match_ambient: bool = True,
        match_self_talk: bool = True,
        match_conversation: bool = False,
        suppress_chat: bool = True,
        works_in_privacy: bool = False,
    ) -> VoiceCommand:
        """Register a voice command."""
        cmd = VoiceCommand(
            command_id=command_id,
            phrases=phrases,
            handler=handler,
            description=description,
            match_direct_address=match_direct_address,
            match_ambient=match_ambient,
            match_self_talk=match_self_talk,
            match_conversation=match_conversation,
            suppress_chat=suppress_chat,
            works_in_privacy=works_in_privacy,
        )
        self._commands.append(cmd)
        return cmd

    def unregister(self, command_id: str) -> bool:
        """Remove a registered command."""
        before = len(self._commands)
        self._commands = [c for c in self._commands if c.command_id != command_id]
        return len(self._commands) < before

    def match(self, text: str, speech_type: str, in_privacy: bool = False) -> VoiceCommand | None:
        """Find the best matching command for the given text.

        Returns the matching VoiceCommand or None.
        When multiple commands match, the one with the longest matching
        phrase wins (so "cancel alarm" beats "alarm").
        """
        import re
        best_cmd: VoiceCommand | None = None
        best_len: int = 0
        text_lower = text.lower().strip()
        for cmd in self._commands:
            if in_privacy and not cmd.works_in_privacy:
                continue
            # Check speech type
            if speech_type == SPEECH_DIRECT_ADDRESS and not cmd.match_direct_address:
                continue
            if speech_type == SPEECH_SELF_TALK and not (cmd.match_self_talk or cmd.match_ambient):
                continue
            if speech_type == SPEECH_CONVERSATION and not (cmd.match_conversation or cmd.match_ambient):
                continue
            if speech_type == SPEECH_NOISE:
                continue
            # Check phrase match — track longest match
            for phrase in cmd.phrases:
                pattern = r'\b' + re.escape(phrase.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    if len(phrase) > best_len:
                        best_len = len(phrase)
                        best_cmd = cmd
                    break  # this command matched, no need to check other phrases
        return best_cmd

    def route(self, text: str, speech_type: str, in_privacy: bool = False) -> tuple[bool, Any]:
        """Try to route text to a voice command.

        Returns (matched, result):
        - (True, result) if a command matched and was executed
        - (False, None) if no command matched
        """
        cmd = self.match(text, speech_type, in_privacy)
        if cmd is None:
            return (False, None)
        try:
            result = cmd.handler(text)
            return (True, result)
        except Exception as exc:
            return (True, {"error": str(exc)})

    def list_commands(self) -> list[dict[str, Any]]:
        """List all registered commands."""
        return [
            {
                "command_id": c.command_id,
                "phrases": c.phrases,
                "description": c.description,
                "suppress_chat": c.suppress_chat,
                "works_in_privacy": c.works_in_privacy,
            }
            for c in self._commands
        ]

    @property
    def count(self) -> int:
        return len(self._commands)


class AudioListener:
    """Always-on ambient audio listening.

    ANUBIS is like a person in the room. He hears everything, understands
    context, and acts on what's relevant — without needing a wake word.

    In AMBIENT mode (default):
    - All speech is transcribed and classified
    - Direct address (name spoken, or question/command directed at him) → responds
    - Self-talk ("I need milk after work") → extracts actions, adds to lists
    - Conversation with others → learns context, may offer relevant info
    - Noise → ignored

    In WAKE_WORD mode:
    - Only responds when his name is spoken
    - Still records ambient speech for context learning

    In CONVERSATION mode:
    - Every utterance is treated as direct address
    - Used during active back-and-forth conversation

    In PRIVACY mode:
    - Listening paused entirely
    - No audio is recorded or processed

    Requires: arecord (Linux) or similar audio capture tool
    Optional: whisper or vosk for transcription, model for classification
    """

    def __init__(
        self,
        root: str | Path,
        *,
        wake_word: str = "demon",
        mode: str = MODE_AMBIENT,
        chunk_duration_s: float = 2.0,
        active_listen_duration_s: float = 10.0,
        energy_threshold: float = 100.0,
        model: ModelLike | None = None,
        on_direct_address: Callable[[str], None] | None = None,
        on_ambient_speech: Callable[[str, str], None] | None = None,
        on_actionable: Callable[[str, str], None] | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.wake_word = wake_word.lower()
        self.mode = mode
        self.chunk_duration = chunk_duration_s
        self.active_listen_duration = active_listen_duration_s
        self.energy_threshold = energy_threshold
        self.model = model
        self.on_direct_address = on_direct_address
        self.on_ambient_speech = on_ambient_speech
        self.on_actionable = on_actionable
        self.ledger = ledger

        self._arecord = shutil.which("arecord") is not None
        self._whisper = shutil.which("whisper") is not None or shutil.which("whisper.cpp") is not None
        self._vosk = shutil.which("vosk-transcribe") is not None
        self._sox = shutil.which("sox") is not None

        self._listening = False
        self._in_conversation = False  # tracking active conversation
        self._conversation_last_utterance = 0.0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._muted = False

        self._state_dir = self.root / "memory" / "sensory"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._events_file = self._state_dir / "audio_events.jsonl"
        self._actions_file = self._state_dir / "ambient_actions.jsonl"

        # Patterns for quick classification without model
        self._action_patterns = [
            ("add_to_list", ["i need to get", "i need", "add to", "put on",
                             "don't forget to get", "remember to get",
                             "pick up", "buy", "grocery", "shopping"]),
            ("create_reminder", ["remind me", "i should", "i need to",
                                 "don't forget", "remember to",
                                 "call ", "email ", "schedule",
                                 "tomorrow", "next week", "before"]),
            ("note", ["i should note", "note that", "write down",
                      "important:", "key point:"]),
            ("offer_help", ["this code is", "this is broken", "this doesn't",
                            "i can't figure out", "why is this",
                            "how do i", "what if i"]),
        ]

    def is_available(self) -> bool:
        """Check if audio listening is available."""
        return self._arecord and (self._whisper or self._vosk)

    def start(self) -> bool:
        """Start continuous listening. Returns True if started."""
        if not self.is_available():
            return False
        if self._thread and self._thread.is_alive():
            return True
        self._stop_event.clear()
        self._listening = True
        self._thread = threading.Thread(
            target=self._listen_loop, daemon=True,
            name="anubis-audio-listener",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop listening."""
        self._stop_event.set()
        self._listening = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None

    def mute(self) -> None:
        """Temporarily stop processing audio (still recording)."""
        self._muted = True

    def unmute(self) -> None:
        """Resume processing audio."""
        self._muted = False

    def set_mode(self, mode: str) -> bool:
        """Set listening mode."""
        if mode not in (MODE_AMBIENT, MODE_WAKE_WORD, MODE_CONVERSATION, MODE_SLEEP, MODE_PRIVACY):
            return False
        self.mode = mode
        return True

    def get_mode(self) -> str:
        """Get current listening mode."""
        return self.mode

    @property
    def is_listening(self) -> bool:
        return self._listening and not self._muted and self.mode != MODE_PRIVACY

    @property
    def is_in_conversation(self) -> bool:
        """Check if ANUBIS is in active conversation mode."""
        return self._in_conversation

    def set_wake_word(self, word: str) -> None:
        """Set the wake word."""
        self.wake_word = word.lower()

    # --------------------------------------------------- main loop

    def _listen_loop(self) -> None:
        """Main listening loop — runs in background thread."""
        while not self._stop_event.is_set():
            if self._muted or self.mode == MODE_PRIVACY:
                self._stop_event.wait(1.0)
                continue
            try:
                self._listen_chunk()
            except Exception:
                self._stop_event.wait(1.0)

    def _listen_chunk(self) -> None:
        """Record and process one audio chunk."""
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, dir=str(self._state_dir)
        ) as f:
            audio_path = f.name

        try:
            # Record chunk
            subprocess.run(
                ["arecord", "-d", str(int(self.chunk_duration)),
                 "-f", "cd", "-r", "16000", audio_path],
                capture_output=True, timeout=self.chunk_duration + 5,
            )

            # Check energy
            energy = self._get_audio_energy(audio_path)
            if energy < self.energy_threshold:
                return  # silence, skip

            # Transcribe
            transcript = self._transcribe(audio_path)
            if not transcript:
                return

            # Process based on mode
            self._process_speech(transcript, energy)

        except Exception:
            pass
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    # --------------------------------------------------- speech processing

    def _process_speech(self, transcript: str, energy: float) -> None:
        """Process transcribed speech based on current mode."""
        if self.mode == MODE_CONVERSATION:
            # Every utterance is direct address
            self._handle_direct_address(transcript, energy)
            return

        if self.mode == MODE_WAKE_WORD:
            # Only respond to wake word
            if self.wake_word in transcript.lower():
                self._handle_direct_address(transcript, energy)
            else:
                # Still record for context
                self._record_event(SPEECH_CONVERSATION, transcript, energy)
            return

        if self.mode == MODE_SLEEP:
            # Sleep mode — only route to voice commands, skip everything else
            # This lets the Creator say "good morning" or "wake me up" to
            # wake ANUBIS, but ANUBIS ignores all other speech (snoring,
            # sleep talking, TV, partner, etc.)
            self._handle_sleep_speech(transcript, energy)
            return

        # AMBIENT mode — classify and act
        speech_type = self._classify_speech(transcript)

        if speech_type == SPEECH_DIRECT_ADDRESS:
            self._handle_direct_address(transcript, energy)
        elif speech_type == SPEECH_SELF_TALK:
            self._handle_self_talk(transcript, energy)
        elif speech_type == SPEECH_CONVERSATION:
            self._handle_ambient_conversation(transcript, energy)
        # noise is ignored

    def _handle_sleep_speech(self, transcript: str, energy: float) -> None:
        """Handle speech during sleep mode.

        In sleep mode, ANUBIS only listens for wake-up voice commands
        (good morning, wake me up, cancel alarm, etc.). All other speech
        is silently ignored — no classification, no observer, no proactive,
        no LLM chat. This protects privacy during sleep while still
        allowing the Creator to wake ANUBIS with their voice.
        """
        # Try routing as direct address — voice commands with
        # works_in_privacy=True will match here
        if self.on_direct_address:
            # The SensorySystem._handle_direct_address checks the voice
            # command router first, so we route through it
            self.on_direct_address(transcript)
        # If no match, silently drop — do NOT record, classify, or log
        # This is important for sleep privacy

    def _classify_speech(self, transcript: str) -> str:
        """Classify speech as direct_address, self_talk, conversation, or noise.

        Uses heuristics first, model if available for refinement.
        """
        text = transcript.lower().strip()

        # Check for direct address — name is spoken
        if self.wake_word in text:
            return SPEECH_DIRECT_ADDRESS

        # Check for direct address patterns — questions/commands
        # Use word-boundary matching to avoid false positives
        import re
        direct_patterns = [
            r"\bwhat do you think\b", r"\bwhat do you say\b",
            r"\bcan you\b", r"\bcould you\b", r"\bwould you\b",
            r"\bplease\b", r"\bhey\b", r"\bdo this\b",
            r"\banswer me\b", r"\btell me\b", r"\bshow me\b",
            r"\bhelp me\b",
        ]
        if any(re.search(p, text) for p in direct_patterns):
            # Could be directed at ANUBIS even without name
            if self.model is not None:
                # Use model to refine
                refined = self._model_classify(text)
                if refined:
                    return refined
            return SPEECH_DIRECT_ADDRESS

        # Check for self-talk — thinking out loud, actionable content
        self_talk_patterns = [
            "i need", "i should", "i have to", "i need to",
            "don't forget", "remember to", "i wonder",
            "maybe i should", "i think i", "i'm going to",
        ]
        if any(p in text for p in self_talk_patterns):
            return SPEECH_SELF_TALK

        # Check for actionable content even without self-talk markers
        action_type = self._detect_action_type(text)
        if action_type:
            return SPEECH_SELF_TALK

        # If it's short and not classifiable, likely noise
        if len(text.split()) < 3:
            return SPEECH_NOISE

        # Default: conversation (Creator talking to someone else)
        return SPEECH_CONVERSATION

    def _model_classify(self, text: str) -> str | None:
        """Use model to classify speech more accurately."""
        if self.model is None:
            return None
        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": SPEECH_CLASSIFIER_SYSTEM},
                    {"role": "user", "content": (
                        f"Classify this speech as one of: "
                        f"direct_address, self_talk, conversation, noise\n\n"
                        f"Speech: \"{text}\"\n\n"
                        f"ANUBIS's name is: {self.wake_word}\n"
                        f"Respond with just the classification word."
                    )},
                ],
                temperature=0.1,
                max_tokens=10,
                timeout=10.0,
            )
            result = completion.text.strip().lower()
            if "direct" in result:
                return SPEECH_DIRECT_ADDRESS
            elif "self" in result or "talk" in result:
                return SPEECH_SELF_TALK
            elif "conversation" in result:
                return SPEECH_CONVERSATION
            elif "noise" in result:
                return SPEECH_NOISE
        except Exception:
            pass
        return None

    # --------------------------------------------------- handlers

    def _handle_direct_address(self, transcript: str, energy: float) -> None:
        """Handle speech directed at ANUBIS."""
        # Extract command after name if present
        text = transcript
        idx = text.lower().find(self.wake_word)
        if idx != -1:
            after = text[idx + len(self.wake_word):].strip(" ,")
            if after:
                text = after

        self._record_event(SPEECH_DIRECT_ADDRESS, transcript, energy,
                          action="responding")
        self._in_conversation = True
        self._conversation_last_utterance = time.time()

        if self.on_direct_address:
            self.on_direct_address(text)

    def _handle_self_talk(self, transcript: str, energy: float) -> None:
        """Handle Creator thinking out loud — may contain actionable content.

        ANUBIS listens, learns, and may act without being asked.
        """
        text = transcript.lower()

        # Detect if there's an actionable item
        action_type = self._detect_action_type(text)

        if action_type:
            # Extract the actionable content
            action_content = self._extract_action_content(transcript, action_type)

            # Record the action
            action = AmbientAction(
                action_id=hashlib.sha256(
                    f"action:{action_type}:{time.time()}".encode()
                ).hexdigest()[:16],
                action_type=action_type,
                trigger_text=transcript,
                content=action_content,
                confidence=0.7,
                timestamp=time.time(),
            )
            self._record_action(action)

            self._record_event(SPEECH_SELF_TALK, transcript, energy,
                              action=f"{action_type}: {action_content}")

            # Notify callback
            if self.on_actionable:
                self.on_actionable(action_type, action_content)
        else:
            # Just self-talk, no action — learn from it
            self._record_event(SPEECH_SELF_TALK, transcript, energy)

        if self.on_ambient_speech:
            self.on_ambient_speech(SPEECH_SELF_TALK, transcript)

    def _handle_ambient_conversation(self, transcript: str, energy: float) -> None:
        """Handle Creator talking to someone else — learn context."""
        self._record_event(SPEECH_CONVERSATION, transcript, energy)

        if self.on_ambient_speech:
            self.on_ambient_speech(SPEECH_CONVERSATION, transcript)

    # --------------------------------------------------- action detection

    def _detect_action_type(self, text: str) -> str:
        """Detect if speech contains actionable content.

        Returns action type or empty string.
        """
        text_lower = text.lower()
        for action_type, patterns in self._action_patterns:
            if any(p in text_lower for p in patterns):
                return action_type
        return ""

    def _extract_action_content(self, transcript: str, action_type: str) -> str:
        """Extract the actionable content from speech.

        e.g., "I need to get milk after work" → "milk after work"
        """
        text = transcript.strip()
        text_lower = text.lower()

        # Try to extract the content after the trigger phrase
        for _, patterns in self._action_patterns:
            for pattern in patterns:
                idx = text_lower.find(pattern)
                if idx != -1:
                    after = text[idx + len(pattern):].strip(" ,")
                    if after:
                        return after

        # If no pattern matched but action was detected, return full text
        return text

    # --------------------------------------------------- recording

    def _record_event(
        self, event_type: str, transcript: str, energy: float,
        *, action: str = "", confidence: float = 0.0
    ) -> None:
        event = AudioEvent(
            event_id=hashlib.sha256(
                f"audio:{event_type}:{time.time()}".encode()
            ).hexdigest()[:16],
            event_type=event_type,
            timestamp=time.time(),
            transcript=transcript,
            energy=energy,
            action_taken=action,
            confidence=confidence,
        )
        try:
            with open(self._events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception:
            pass

        if self.ledger is not None:
            try:
                self.ledger.append(
                    "anubis.sensory.audio",
                    f"audio.{event_type}",
                    {"transcript_length": len(transcript),
                     "action": action},
                )
            except Exception:
                pass

    def _record_action(self, action: AmbientAction) -> None:
        try:
            with open(self._actions_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(action.to_dict()) + "\n")
        except Exception:
            pass

    # --------------------------------------------------- audio utilities

    def _get_audio_energy(self, audio_path: str) -> float:
        """Estimate audio energy from file."""
        try:
            if self._sox:
                result = subprocess.run(
                    ["sox", audio_path, "-n", "stat"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stderr.split("\n"):
                    if "RMS amplitude" in line or "Maximum amplitude" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            return abs(float(parts[1].strip())) * 1000
            return float(os.path.getsize(audio_path))
        except Exception:
            return 0.0

    def _transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        if self._whisper:
            return self._transcribe_whisper(audio_path)
        elif self._vosk:
            return self._transcribe_vosk(audio_path)
        return ""

    def _transcribe_whisper(self, audio_path: str) -> str:
        try:
            cmd = shutil.which("whisper") or shutil.which("whisper.cpp")
            result = subprocess.run(
                [cmd, audio_path, "--model", "tiny", "--language", "en"],
                capture_output=True, text=True, timeout=30,
            )
            lines = result.stdout.strip().splitlines()
            text_lines = [
                l for l in lines
                if not l.startswith("[") and not l.startswith("--")
            ]
            return " ".join(text_lines).strip()
        except Exception:
            return ""

    def _transcribe_vosk(self, audio_path: str) -> str:
        try:
            result = subprocess.run(
                ["vosk-transcribe", audio_path],
                capture_output=True, text=True, timeout=30,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    # --------------------------------------------------- queries

    def get_events(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent audio events."""
        if not self._events_file.exists():
            return []
        try:
            lines = self._events_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_actions(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent ambient actions ANUBIS took."""
        if not self._actions_file.exists():
            return []
        try:
            lines = self._actions_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "available": self.is_available(),
            "listening": self.is_listening,
            "mode": self.mode,
            "in_conversation": self._in_conversation,
            "muted": self._muted,
            "wake_word": self.wake_word,
            "arecord": self._arecord,
            "whisper": self._whisper,
            "vosk": self._vosk,
            "total_events": len(self.get_events(limit=9999)),
            "total_actions": len(self.get_actions(limit=9999)),
        }


# --------------------------------------------------------------- visual eyes


class ScreenWatcher:
    """Continuous screen monitoring.

    Periodically captures the screen and generates descriptions.
    Changes are detected and fed to the observer/proactive system.

    Requires: scrot or import (Linux) or screencapture (macOS)
    Optional: tesseract for OCR, model for description generation
    """

    def __init__(
        self,
        root: str | Path,
        *,
        capture_interval_s: float = 30.0,
        on_change: Callable[[str, str], None] | None = None,
        model: ModelLike | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.capture_interval = capture_interval_s
        self.on_change = on_change
        self.model = model
        self.ledger = ledger

        # Detect available screen capture tools
        self._scrot = shutil.which("scrot") is not None
        self._import = shutil.which("import") is not None  # ImageMagick
        self._screencapture = shutil.which("screencapture") is not None  # macOS
        self._tesseract = shutil.which("tesseract") is not None

        self._watching = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_description: str = ""
        self._capture_count: int = 0

        self._state_dir = self.root / "memory" / "sensory"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._captures_dir = self._state_dir / "captures"
        self._captures_dir.mkdir(parents=True, exist_ok=True)
        self._observations_file = self._state_dir / "screen_observations.jsonl"

    def is_available(self) -> bool:
        """Check if screen capture is available."""
        return self._scrot or self._import or self._screencapture

    def start(self) -> bool:
        """Start continuous screen watching. Returns True if started."""
        if not self.is_available():
            return False
        if self._thread and self._thread.is_alive():
            return True
        self._stop_event.clear()
        self._watching = True
        self._thread = threading.Thread(
            target=self._watch_loop, daemon=True,
            name="anubis-screen-watcher",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop watching."""
        self._stop_event.set()
        self._watching = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None

    @property
    def is_watching(self) -> bool:
        return self._watching

    def _watch_loop(self) -> None:
        """Main watching loop — runs in background thread."""
        while not self._stop_event.is_set():
            try:
                self._capture_and_analyze()
            except Exception:
                pass  # watcher must never crash
            self._stop_event.wait(self.capture_interval)

    def _capture_and_analyze(self) -> None:
        """Capture screen and analyze for changes."""
        # Capture screen
        capture_path = self._captures_dir / f"screen_{int(time.time())}.png"
        if not self._capture_screen(str(capture_path)):
            return

        self._capture_count += 1

        # Generate description
        description = self._describe_screen(str(capture_path))
        if not description:
            # Clean up if we couldn't describe
            try:
                capture_path.unlink()
            except Exception:
                pass
            return

        # Detect changes
        changed = description != self._last_description
        if changed and self._last_description:
            # Significant change detected
            obs = ScreenObservation(
                obs_id=hashlib.sha256(
                    f"screen:{time.time()}".encode()
                ).hexdigest()[:16],
                timestamp=time.time(),
                capture_path=str(capture_path),
                description=description,
                changes_detected=True,
                previous_description=self._last_description,
            )
            self._record_observation(obs)

            if self.on_change:
                self.on_change(description, self._last_description)

        self._last_description = description

        # Clean up old captures (keep last 10)
        captures = sorted(self._captures_dir.glob("screen_*.png"))
        for old in captures[:-10]:
            try:
                old.unlink()
            except Exception:
                pass

    def _capture_screen(self, path: str) -> bool:
        """Capture the screen to a file."""
        try:
            if self._scrot:
                subprocess.run(
                    ["scrot", path], capture_output=True, timeout=10,
                )
                return os.path.exists(path)
            elif self._import:
                subprocess.run(
                    ["import", "-window", "root", path],
                    capture_output=True, timeout=10,
                )
                return os.path.exists(path)
            elif self._screencapture:
                subprocess.run(
                    ["screencapture", path], capture_output=True, timeout=10,
                )
                return os.path.exists(path)
        except Exception:
            pass
        return False

    def _describe_screen(self, image_path: str) -> str:
        """Generate a text description of the screen.

        Uses OCR (tesseract) if available, otherwise tries the model
        for image description (if the model supports vision).
        """
        # Try OCR first
        if self._tesseract:
            try:
                result = subprocess.run(
                    ["tesseract", image_path, "-", "--psm", "6"],
                    capture_output=True, text=True, timeout=15,
                )
                text = result.stdout.strip()
                if text:
                    # Truncate and clean
                    text = text[:2000]
                    return f"[OCR] {text}"
            except Exception:
                pass

        # Try model-based description (if model supports vision)
        # This would require a vision-capable model
        # For now, return a placeholder
        return f"[Screen capture at {time.strftime('%H:%M:%S')}]"

    def _record_observation(self, obs: ScreenObservation) -> None:
        try:
            with open(self._observations_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(obs.to_dict()) + "\n")
        except Exception:
            pass

        if self.ledger is not None:
            try:
                self.ledger.append(
                    "anubis.sensory.screen",
                    "screen.change_detected",
                    {"description_length": len(obs.description)},
                )
            except Exception:
                pass

    def capture_once(self) -> str | None:
        """Capture screen once and return description."""
        capture_path = self._captures_dir / f"manual_{int(time.time())}.png"
        if not self._capture_screen(str(capture_path)):
            return None
        return self._describe_screen(str(capture_path))

    def get_observations(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent screen observations."""
        if not self._observations_file.exists():
            return []
        try:
            lines = self._observations_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "available": self.is_available(),
            "watching": self.is_watching,
            "capture_interval_s": self.capture_interval,
            "total_captures": self._capture_count,
            "scrot": self._scrot,
            "import": self._import,
            "screencapture": self._screencapture,
            "tesseract": self._tesseract,
            "total_observations": len(self.get_observations(limit=9999)),
        }


# --------------------------------------------------------------- voice output


class VoiceSpeaker:
    """Auto-speak system for proactive messages.

    Queues messages and speaks them aloud using TTS.
    Rate-limited to avoid talking over the Creator.
    Priority-based: immediate messages skip the queue.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        voice_output: Any | None = None,
        min_interval_s: float = 5.0,
        max_queue_size: int = 20,
        enabled: bool = True,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.voice_output = voice_output
        self.min_interval = min_interval_s
        self.max_queue_size = max_queue_size
        self.enabled = enabled
        self.ledger = ledger

        self._queue: list[SpeechRequest] = []
        self._last_spoke: float = 0.0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._total_spoken: int = 0
        self._total_skipped: int = 0

        self._state_dir = self.root / "memory" / "sensory"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "speech_history.jsonl"

    def is_available(self) -> bool:
        """Check if voice output is available."""
        if not self.enabled:
            return False
        if self.voice_output is not None:
            return self.voice_output.is_available()
        # Check for espeak directly
        return (
            shutil.which("espeak-ng") is not None
            or shutil.which("espeak") is not None
        )

    def start(self) -> bool:
        """Start the speaker background thread."""
        if self._thread and self._thread.is_alive():
            return True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._speak_loop, daemon=True,
            name="anubis-voice-speaker",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the speaker."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None

    def speak(self, text: str, *, priority: str = "normal",
              source: str = "") -> str:
        """Queue text to be spoken. Returns request ID."""
        if not self.enabled:
            return ""

        req = SpeechRequest(
            req_id=hashlib.sha256(
                f"speak:{text[:50]}:{time.time()}".encode()
            ).hexdigest()[:16],
            text=text,
            priority=priority,
            source=source,
            created_at=time.time(),
        )

        with self._lock:
            if priority == "immediate":
                # Speak immediately, interrupt queue
                self._speak_now(req)
            else:
                if len(self._queue) >= self.max_queue_size:
                    # Drop oldest low-priority item
                    self._queue.pop(0)
                self._queue.append(req)

        return req.req_id

    def speak_now(self, text: str, source: str = "") -> bool:
        """Speak text immediately, bypassing the queue."""
        if not self.is_available():
            return False
        req = SpeechRequest(
            req_id=hashlib.sha256(
                f"speak_now:{time.time()}".encode()
            ).hexdigest()[:16],
            text=text,
            priority="immediate",
            source=source,
            created_at=time.time(),
        )
        return self._speak_now(req)

    def mute(self) -> None:
        """Stop speaking (queued messages are kept)."""
        self.enabled = False

    def unmute(self) -> None:
        """Resume speaking."""
        self.enabled = True

    def clear_queue(self) -> int:
        """Clear pending speech. Returns count cleared."""
        with self._lock:
            count = len(self._queue)
            for req in self._queue:
                req.skipped = True
            self._queue.clear()
            return count

    def _speak_loop(self) -> None:
        """Main speaker loop — runs in background thread."""
        while not self._stop_event.is_set():
            if not self.enabled:
                self._stop_event.wait(1.0)
                continue

            # Check rate limit
            now = time.time()
            if now - self._last_spoke < self.min_interval:
                self._stop_event.wait(1.0)
                continue

            # Get next message
            with self._lock:
                if not self._queue:
                    continue
                # Sort by priority (immediate > high > normal > low)
                priority_order = {"immediate": 0, "high": 1, "normal": 2, "low": 3}
                self._queue.sort(key=lambda r: priority_order.get(r.priority, 2))
                req = self._queue.pop(0)

            self._speak_now(req)
            self._last_spoke = time.time()

    def _speak_now(self, req: SpeechRequest) -> bool:
        """Speak a single request immediately."""
        if not self.is_available():
            req.skipped = True
            return False

        # Clean text for speech
        clean = req.text
        for char in ["*", "#", "`", "[", "]", "(", ")"]:
            clean = clean.replace(char, "")
        clean = clean.strip()

        if not clean:
            req.skipped = True
            return False

        success = False
        if self.voice_output is not None:
            success = self.voice_output.speak(clean)
        else:
            # Direct espeak
            try:
                cmd = shutil.which("espeak-ng") or shutil.which("espeak")
                if cmd:
                    subprocess.run(
                        [cmd, "-v", "en", "-s", "175", clean],
                        capture_output=True, timeout=30,
                    )
                    success = True
            except Exception:
                success = False

        req.spoken = success
        if not success:
            req.skipped = True
            self._total_skipped += 1
        else:
            self._total_spoken += 1

        # Record in history
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(req.to_dict()) + "\n")
        except Exception:
            pass

        if self.ledger is not None:
            try:
                self.ledger.append(
                    "anubis.sensory.voice",
                    "voice.spoken" if success else "voice.skipped",
                    {"source": req.source, "priority": req.priority},
                )
            except Exception:
                pass

        return success

    def get_queue(self) -> list[dict[str, Any]]:
        """Get current speech queue."""
        with self._lock:
            return [r.to_dict() for r in self._queue]

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get speech history."""
        if not self._history_file.exists():
            return []
        try:
            lines = self._history_file.read_text(
                encoding="utf-8"
            ).strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "available": self.is_available(),
            "enabled": self.enabled,
            "queue_size": len(self._queue),
            "total_spoken": self._total_spoken,
            "total_skipped": self._total_skipped,
            "last_spoke": self._last_spoke,
            "min_interval_s": self.min_interval,
        }


# --------------------------------------------------------------- integration


class SensorySystem:
    """Unified sensory system — integrates ears, eyes, and voice.

    This is the top-level sensory manager that coordinates all three
    systems and connects them to the observer, proactive engagement,
    and conversation handler.

    ANUBIS is like a person in the room:
    - He hears everything and classifies it
    - He acts on actionable speech without being asked
    - He responds when spoken to directly
    - He offers opinions and help when appropriate
    - He watches the screen and reacts to changes
    - He speaks aloud rather than just displaying text
    """

    ACTOR = "anubis.sensory"

    def __init__(
        self,
        root: str | Path,
        *,
        wake_word: str = "demon",
        mode: str = MODE_AMBIENT,
        model: ModelLike | None = None,
        voice_output: Any | None = None,
        observer: Any | None = None,
        proactive: Any | None = None,
        on_conversation: Callable[[str], str] | None = None,
        on_action: Callable[[str, str], str] | None = None,
        voice_command_router: VoiceCommandRouter | None = None,
        voice_interpreter: Any | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.model = model
        self.observer = observer
        self.proactive = proactive
        self.on_conversation = on_conversation
        self.on_action = on_action
        self.voice_command_router = voice_command_router
        self.voice_interpreter = voice_interpreter
        self.ledger = ledger

        # Create subsystems
        self.ears = AudioListener(
            root,
            wake_word=wake_word,
            mode=mode,
            model=model,
            on_direct_address=self._handle_direct_address,
            on_ambient_speech=self._handle_ambient_speech,
            on_actionable=self._handle_actionable,
            ledger=ledger,
        )
        self.eyes = ScreenWatcher(
            root,
            on_change=self._handle_screen_change,
            model=model,
            ledger=ledger,
        )
        self.voice = VoiceSpeaker(
            root,
            voice_output=voice_output,
            ledger=ledger,
        )

        self._running = False

    def start(self) -> dict[str, bool]:
        """Start all sensory systems. Returns status of each."""
        results = {
            "ears": self.ears.start(),
            "eyes": self.eyes.start(),
            "voice": self.voice.start(),
        }
        self._running = any(results.values())
        return results

    def stop(self) -> None:
        """Stop all sensory systems."""
        self.ears.stop()
        self.eyes.stop()
        self.voice.stop()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    # --------------------------------------------------- audio handlers

    def _handle_direct_address(self, text: str) -> None:
        """Handle speech directed at ANUBIS — respond conversationally."""
        # Check voice command router FIRST — before chat
        if self.voice_command_router is not None:
            in_privacy = self.ears.mode == MODE_PRIVACY
            matched, result = self.voice_command_router.route(
                text, SPEECH_DIRECT_ADDRESS, in_privacy=in_privacy,
            )
            if matched:
                cmd = self.voice_command_router.match(text, SPEECH_DIRECT_ADDRESS, in_privacy)
                # Feed to observer
                if self.observer is not None:
                    try:
                        self.observer._make_observation(
                            source="audio",
                            event_type="voice_command",
                            content=f"Voice command: {text[:200]}",
                            severity="info",
                        )
                    except Exception:
                        pass
                # If the command suppresses chat, we're done
                if cmd and cmd.suppress_chat:
                    # Speak the result if it's a string
                    if isinstance(result, str) and result:
                        self.voice.speak(result, priority="high", source="voice_command")
                    elif isinstance(result, dict) and result.get("message"):
                        self.voice.speak(result["message"], priority="high", source="voice_command")
                    return
                # If not suppressed, fall through to chat

        # Universal voice command interpreter — tries to parse as command
        if self.voice_interpreter is not None:
            try:
                interp = self.voice_interpreter.interpret_and_execute(text)
                if interp.get("executed"):
                    spoken = interp.get("spoken", "")
                    if spoken:
                        self.voice.speak(spoken, priority="high", source="voice_command")
                    # Feed to observer
                    if self.observer is not None:
                        try:
                            self.observer._make_observation(
                                source="audio",
                                event_type="voice_command_interpreted",
                                content=f"Interpreted command: {text[:200]}",
                                severity="info",
                            )
                        except Exception:
                            pass
                    return
                # If not executed, fall through to chat
            except Exception:
                pass  # Fall through to chat on any error

        # Feed to observer
        if self.observer is not None:
            try:
                self.observer._make_observation(
                    source="audio",
                    event_type="direct_address",
                    content=f"Creator said: {text[:200]}",
                    severity="info",
                )
            except Exception:
                pass

        # Feed to proactive
        if self.proactive is not None:
            try:
                self.proactive.observe(
                    "audio", f"Creator spoke: {text}",
                    auto_react=True,
                )
            except Exception:
                pass

        # Process as conversation
        if self.on_conversation:
            response = self.on_conversation(text)
            if response:
                self.voice.speak(response, priority="high", source="response")

    def _handle_ambient_speech(self, speech_type: str, text: str) -> None:
        """Handle ambient speech — Creator talking, not necessarily to ANUBIS.

        ANUBIS listens and learns. He may offer input if it's relevant.
        """
        # Check voice command router — catches "goodnight" in ambient mode
        if self.voice_command_router is not None:
            in_privacy = self.ears.mode == MODE_PRIVACY
            matched, result = self.voice_command_router.route(
                text, speech_type, in_privacy=in_privacy,
            )
            if matched:
                cmd = self.voice_command_router.match(text, speech_type, in_privacy)
                if self.observer is not None:
                    try:
                        self.observer._make_observation(
                            source="audio",
                            event_type="voice_command",
                            content=f"Ambient voice command: {text[:200]}",
                            severity="info",
                        )
                    except Exception:
                        pass
                if cmd and cmd.suppress_chat:
                    if isinstance(result, str) and result:
                        self.voice.speak(result, priority="high", source="voice_command")
                    elif isinstance(result, dict) and result.get("message"):
                        self.voice.speak(result["message"], priority="high", source="voice_command")
                    return

        # Feed to observer for context learning
        if self.observer is not None:
            try:
                self.observer._make_observation(
                    source="audio",
                    event_type=speech_type,
                    content=f"Ambient speech: {text[:200]}",
                    severity="info",
                )
            except Exception:
                pass

        # Feed to proactive for pattern learning
        if self.proactive is not None:
            try:
                self.proactive.observe(
                    "audio", text, auto_react=False,
                )
            except Exception:
                pass

    def _handle_actionable(self, action_type: str, content: str) -> None:
        """Handle actionable ambient speech — ANUBIS acts without being asked.

        Examples:
        - "I need milk" → action_type="add_to_list", content="milk"
        - "Call mom tomorrow" → action_type="create_reminder"
        """
        # If there's an action handler, use it
        if self.on_action:
            response = self.on_action(action_type, content)
            if response:
                # Speak confirmation quietly
                self.voice.speak(
                    response, priority="normal", source="ambient_action"
                )
        else:
            # Default: acknowledge quietly
            ack = self._default_action_acknowledgment(action_type, content)
            if ack:
                self.voice.speak(ack, priority="low", source="ambient_action")

    def _default_action_acknowledgment(
        self, action_type: str, content: str
    ) -> str:
        """Generate a default acknowledgment for an ambient action."""
        if action_type == "add_to_list":
            return f"Added '{content}' to your list."
        elif action_type == "create_reminder":
            return f"I'll remind you to {content}."
        elif action_type == "note":
            return f"Noted: {content}."
        elif action_type == "offer_help":
            return f"I can help with that if you'd like."
        return ""

    # --------------------------------------------------- screen handler

    def _handle_screen_change(
        self, description: str, previous: str
    ) -> None:
        """Handle screen change detection."""
        # Feed to observer
        if self.observer is not None:
            try:
                self.observer._make_observation(
                    source="screen",
                    event_type="change",
                    content=f"Screen changed: {description[:200]}",
                    severity="info",
                )
            except Exception:
                pass

        # Feed to proactive
        if self.proactive is not None:
            try:
                self.proactive.observe(
                    "screen", description, auto_react=True,
                )
            except Exception:
                pass

    # --------------------------------------------------- public API

    def speak(self, text: str, *, priority: str = "normal",
              source: str = "") -> str:
        """Speak something aloud."""
        return self.voice.speak(text, priority=priority, source=source)

    def set_wake_word(self, word: str) -> None:
        """Set the wake word."""
        self.ears.set_wake_word(word)

    def set_mode(self, mode: str) -> bool:
        """Set listening mode: ambient, wake_word, conversation, privacy."""
        return self.ears.set_mode(mode)

    def get_mode(self) -> str:
        """Get current listening mode."""
        return self.ears.get_mode()

    def mute_audio(self) -> None:
        """Stop listening."""
        self.ears.mute()

    def unmute_audio(self) -> None:
        """Resume listening."""
        self.ears.unmute()

    def mute_voice(self) -> None:
        """Stop speaking."""
        self.voice.mute()

    def unmute_voice(self) -> None:
        """Resume speaking."""
        self.voice.unmute()

    def privacy_mode(self) -> None:
        """Enter privacy mode — stop listening entirely."""
        self.ears.set_mode(MODE_PRIVACY)

    def sleep_mode(self) -> None:
        """Enter sleep mode — listen only for wake-up voice commands."""
        self.ears.set_mode(MODE_SLEEP)

    def ambient_mode(self) -> None:
        """Return to ambient mode — always listening."""
        self.ears.set_mode(MODE_AMBIENT)

    def get_actions(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent ambient actions ANUBIS took."""
        return self.ears.get_actions(limit=limit)

    def get_status(self) -> dict[str, Any]:
        """Get full sensory system status."""
        return {
            "running": self._running,
            "ears": self.ears.get_status(),
            "eyes": self.eyes.get_status(),
            "voice": self.voice.get_status(),
        }


# --------------------------------------------------------------- prompts

SPEECH_CLASSIFIER_SYSTEM = """\
You are ANUBIS's speech classification system. You classify overheard \
speech into one of four categories:

- direct_address: The speaker is talking TO ANUBIS (uses his name, or is \
  clearly asking him a question or giving him a command)
- self_talk: The speaker is thinking out loud, talking to themselves, \
  or mentioning something they need to do (e.g., "I need to get milk")
- conversation: The speaker is talking to someone else in the room
- noise: Non-speech audio, music, TV sounds, etc.

Respond with just the classification word, nothing else.
"""
