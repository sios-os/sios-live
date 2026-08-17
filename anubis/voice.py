"""Voice I/O for DEMON — TTS and STT using local models.

Uses espeak-ng for text-to-speech and whisper.cpp or vosk for
speech-to-text. All processing is local — no cloud.

If the tools aren't installed, voice features degrade gracefully
to text-only mode.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class VoiceOutput:
    """Text-to-speech using espeak-ng (local, no cloud)."""

    def __init__(self, enabled: bool = True, rate: int = 175, voice: str = "en") -> None:
        self.enabled = enabled
        self.rate = rate
        self.voice = voice
        self._available = shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    def speak(self, text: str) -> bool:
        """Speak text aloud. Returns True if successful."""
        if not self.enabled or not self._available:
            return False
        # Strip markdown for cleaner speech
        clean = text.replace("*", "").replace("#", "").replace("`", "")
        clean = clean.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
        try:
            cmd = shutil.which("espeak-ng") or shutil.which("espeak")
            subprocess.run(
                [cmd, "-v", self.voice, "-s", str(self.rate), clean],
                capture_output=True, timeout=30,
            )
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._available

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled


class VoiceInput:
    """Speech-to-text using local whisper or vosk.

    Records audio from microphone and transcribes it.
    Falls back to text input if no audio tools available.
    """

    def __init__(self, enabled: bool = True, engine: str = "auto") -> None:
        self.enabled = enabled
        self.engine = engine
        self._whisper_available = shutil.which("whisper") is not None or shutil.which("whisper.cpp") is not None
        self._vosk_available = shutil.which("vosk-transcribe") is not None
        self._arecord = shutil.which("arecord") is not None

    def is_available(self) -> bool:
        return self._whisper_available or self._vosk_available

    def listen(self, duration: int = 5) -> str:
        """Record audio and transcribe. Returns transcribed text or empty string."""
        if not self.enabled or not self._arecord:
            return ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                audio_path = f.name
            # Record
            subprocess.run(
                ["arecord", "-d", str(duration), "-f", "cd", audio_path],
                capture_output=True, timeout=duration + 5,
            )
            # Transcribe
            if self._whisper_available:
                return self._transcribe_whisper(audio_path)
            elif self._vosk_available:
                return self._transcribe_vosk(audio_path)
            return ""
        except Exception:
            return ""
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def _transcribe_whisper(self, audio_path: str) -> str:
        try:
            result = subprocess.run(
                ["whisper", audio_path, "--model", "tiny", "--language", "en"],
                capture_output=True, text=True, timeout=30,
            )
            # Extract text from output
            lines = result.stdout.strip().splitlines()
            text_lines = [l for l in lines if not l.startswith("[") and not l.startswith("--")]
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

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
