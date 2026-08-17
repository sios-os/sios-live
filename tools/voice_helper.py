#!/usr/bin/env python3
"""Voice helper for the DEMON interface.

Provides:
  - text_to_speech(text) — convert text to audio, play through speakers
  - speech_to_text() — record from microphone, convert to text

Uses only local tools:
  - TTS: espeak-ng (installed via apt)
  - STT: vosk with a small local model (downloaded on first use)

No cloud services. No network required after model download.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "memory" / "vosk-model"

# Vosk model URL (small English model, ~40MB)
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"


def text_to_speech(text: str, rate: int = 150, voice: str = "en") -> str:
    """Convert text to speech and play it.

    Uses espeak-ng. Returns the path to the generated audio file.
    """
    # Clean text for espeak (remove markdown, etc.)
    clean = text
    for char in ["*", "_", "#", "`", "[", "]", "(", ")"]:
        clean = clean.replace(char, "")
    clean = clean.strip()
    if not clean:
        return ""

    audio_path = str(Path(tempfile.gettempdir()) / "anubis_tts.wav")
    try:
        subprocess.run(
            ["espeak-ng", "-v", voice, "-s", str(rate), "-w", audio_path, clean],
            capture_output=True, timeout=10, check=True,
        )
        # Play the audio
        subprocess.run(
            ["aplay", "-q", audio_path],
            capture_output=True, timeout=30,
        )
        return audio_path
    except FileNotFoundError:
        # espeak-ng or aplay not installed
        return ""
    except Exception:
        return ""


def _ensure_vosk_model() -> Path | None:
    """Download and extract the Vosk model if not present."""
    model_path = MODEL_DIR
    if model_path.exists() and any(model_path.iterdir()):
        return model_path

    model_path.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Vosk model from {MODEL_URL}...", file=sys.stderr)
    try:
        import urllib.request
        import zipfile
        # Download
        zip_path = str(model_path / "model.zip")
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        # Extract
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(str(model_path))
        os.unlink(zip_path)
        # Find the extracted directory
        for child in model_path.iterdir():
            if child.is_dir() and "vosk" in child.name.lower():
                return child
        return model_path
    except Exception as exc:
        print(f"Failed to download model: {exc}", file=sys.stderr)
        return None


def speech_to_text(timeout: float = 10.0) -> str:
    """Record audio from microphone and convert to text.

    Tries multiple backends in order:
    1. vosk (Python package) — local, fast, small model
    2. whisper.cpp (subprocess) — local, more accurate, larger model
    3. Returns empty string if no STT backend available

    Returns the recognized text, or empty string on failure.
    """
    # Record audio
    audio_path = str(Path(tempfile.gettempdir()) / "anubis_stt.wav")
    try:
        subprocess.run(
            ["arecord", "-f", "wav", "-r", "16000", "-c", "1",
             "-d", str(int(timeout)), "-q", audio_path],
            capture_output=True, timeout=timeout + 2,
        )
    except FileNotFoundError:
        # arecord not available — try ffmpeg
        try:
            subprocess.run(
                ["ffmpeg", "-f", "alsa", "-i", "default", "-t",
                 str(int(timeout)), "-ar", "16000", "-ac", "1",
                 "-y", audio_path],
                capture_output=True, timeout=timeout + 5,
            )
        except Exception:
            return ""
    except Exception:
        return ""

    # Try vosk first
    result = _stt_via_vosk(audio_path)
    if result:
        return result

    # Try whisper.cpp as fallback
    result = _stt_via_whisper_cpp(audio_path)
    if result:
        return result

    return ""


def _stt_via_vosk(audio_path: str) -> str:
    """Recognize speech using vosk (Python package)."""
    model_path = _ensure_vosk_model()
    if model_path is None:
        return ""

    try:
        from vosk import Model, KaldiRecognizer

        # Find the actual model directory
        model_dir = str(model_path)
        if not (Path(model_dir) / "am").exists():
            # Look for subdirectory
            for child in Path(model_dir).iterdir():
                if (child / "am").exists():
                    model_dir = str(child)
                    break

        model = Model(model_dir)
        rec = KaldiRecognizer(model, 16000)

        wf = wave.open(audio_path, "rb")
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    results.append(result["text"])
        # Final result
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            results.append(final["text"])
        wf.close()

        return " ".join(results).strip()
    except ImportError:
        # vosk not installed — not an error, just unavailable
        return ""
    except Exception as exc:
        print(f"Vosk STT error: {exc}", file=sys.stderr)
        return ""


def _stt_via_whisper_cpp(audio_path: str) -> str:
    """Recognize speech using whisper.cpp (subprocess).

    whisper.cpp is a self-hosted alternative to vosk that can be
    compiled locally. No Python package dependency.
    """
    import shutil as _shutil
    whisper_cmd = _shutil.which("whisper-cli") or _shutil.which("main")
    if not whisper_cmd:
        return ""

    # Look for whisper model
    model_candidates = [
        os.environ.get("ANUBIS_WHISPER_MODEL", ""),
        str(ROOT / "memory" / "whisper-model" / "ggml-base.en.bin"),
        "/usr/local/share/whisper/ggml-base.en.bin",
    ]
    model_path = next((p for p in model_candidates if p and Path(p).exists()), "")
    if not model_path:
        return ""

    try:
        result = subprocess.run(
            [whisper_cmd, "-m", model_path, "-f", audio_path, "--no-timestamps"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            # whisper.cpp outputs text to stdout
            text = result.stdout.strip()
            # Remove common prefixes
            for prefix in ["[00:00:00.000 --> 00:00:00.000]  ", "  "]:
                if text.startswith(prefix):
                    text = text[len(prefix):]
            return text
    except Exception:
        pass

    return ""


def main() -> int:
    """CLI: tts <text> | stt"""
    if len(sys.argv) < 2:
        print("Usage: voice_helper.py tts <text> | stt [timeout]")
        return 1

    cmd = sys.argv[1]
    if cmd == "tts":
        text = " ".join(sys.argv[2:])
        if not text:
            text = sys.stdin.read()
        path = text_to_speech(text)
        if path:
            print(json.dumps({"ok": True, "path": path}))
        else:
            print(json.dumps({"ok": False, "error": "TTS failed"}))
        return 0
    elif cmd == "stt":
        timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
        text = speech_to_text(timeout)
        print(json.dumps({"text": text}))
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
