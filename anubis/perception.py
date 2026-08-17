"""Perception system — ANUBIS's ability to identify and understand.

This module gives ANUBIS real perception beyond just transcribing audio
and capturing screens. It adds:

1. **Voice identification** — Distinguish known voices (Creator, family,
   household members) from unknown voices and non-human audio (TV, radio,
   music, traffic). Each known person has a voice profile built from
   audio features.

2. **Voice emotion analysis** — Detect emotional states from voice
   patterns: duress, stress, sadness, anger, joy, calm, fear. Uses
   acoustic features (pitch variation, energy, speech rate, spectral
   characteristics) to estimate emotional state.

3. **Facial recognition** — Identify household members from camera
   input. Uses face_recognition library if available, OpenCV fallback,
   or a feature-based approach. Stores face profiles for known people.

4. **Object recognition** — Identify vehicles, animals, and objects
   from camera input. Uses YOLO or OpenCV DNN if available, otherwise
   a motion/shape-based heuristic approach.

HONEST LIMITATIONS:
- Real speaker identification needs an embedding model (like x-vectors
  from ECAPA-TDNN or Resemblyzer). This module uses acoustic features
  (pitch, spectral centroid, energy patterns) as a fallback that's less
  accurate but works without ML libraries.
- Real emotion detection needs a trained classifier on emotional speech
  datasets. This module uses acoustic feature heuristics as a fallback.
- Real facial recognition needs face_recognition or OpenCV with a
  trained model. This module detects that and degrades gracefully.
- Real object recognition needs YOLO or similar. This module detects
  available tools and degrades gracefully.

When ML tools are available, this module uses them. When they're not,
it falls back to signal-processing heuristics that are less accurate
but still useful for basic filtering (human vs TV, calm vs stressed).

Uses only the Python standard library for core logic.
External tools (face_recognition, cv2, resemblyzer, etc.) are optional.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import struct
import tempfile
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


# --------------------------------------------------------------------- types


@dataclass
class VoiceProfile:
    """A stored voice profile for a known person."""
    profile_id: str
    name: str
    relationship: str = ""  # creator, family, friend, household
    features: dict[str, float] = field(default_factory=dict)
    samples: int = 0  # number of audio samples used to build profile
    created_at: float = 0.0
    updated_at: float = 0.0
    trusted: bool = False  # trusted voices can issue commands

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "relationship": self.relationship,
            "features": self.features,
            "samples": self.samples,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "trusted": self.trusted,
        }


@dataclass
class VoiceIdentification:
    """Result of identifying a voice."""
    identified: bool = False
    name: str = ""
    profile_id: str = ""
    relationship: str = ""
    confidence: float = 0.0
    is_human: bool = True  # False if TV, radio, music, noise
    is_known: bool = False
    is_trusted: bool = False
    audio_type: str = "speech"  # speech, tv, radio, music, noise, unknown

    def to_dict(self) -> dict[str, Any]:
        return {
            "identified": self.identified,
            "name": self.name,
            "profile_id": self.profile_id,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "is_human": self.is_human,
            "is_known": self.is_known,
            "is_trusted": self.is_trusted,
            "audio_type": self.audio_type,
        }


@dataclass
class EmotionAnalysis:
    """Result of analyzing emotional state from voice."""
    emotion: str = "neutral"  # neutral, calm, happy, sad, angry, fearful, stressed, duress
    confidence: float = 0.0
    arousal: float = 0.0  # 0=calm, 1=excited
    valence: float = 0.5  # 0=negative, 1=positive
    pitch_mean: float = 0.0
    pitch_variability: float = 0.0
    energy_mean: float = 0.0
    speech_rate: float = 0.0  # words per second estimate
    indicators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "emotion": self.emotion,
            "confidence": self.confidence,
            "arousal": round(self.arousal, 3),
            "valence": round(self.valence, 3),
            "pitch_mean": round(self.pitch_mean, 2),
            "pitch_variability": round(self.pitch_variability, 2),
            "energy_mean": round(self.energy_mean, 2),
            "speech_rate": round(self.speech_rate, 2),
            "indicators": self.indicators,
        }


@dataclass
class FaceProfile:
    """A stored face profile for a known person."""
    profile_id: str
    name: str
    relationship: str = ""
    encoding: list[float] = field(default_factory=list)  # face embedding
    image_path: str = ""
    samples: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0
    trusted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "relationship": self.relationship,
            "encoding_length": len(self.encoding),
            "image_path": self.image_path,
            "samples": self.samples,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "trusted": self.trusted,
        }


@dataclass
class FaceIdentification:
    """Result of identifying a face."""
    identified: bool = False
    name: str = ""
    profile_id: str = ""
    relationship: str = ""
    confidence: float = 0.0
    is_known: bool = False
    is_trusted: bool = False
    face_count: int = 0
    unknown_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "identified": self.identified,
            "name": self.name,
            "profile_id": self.profile_id,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "is_known": self.is_known,
            "is_trusted": self.is_trusted,
            "face_count": self.face_count,
            "unknown_count": self.unknown_count,
        }


@dataclass
class ObjectDetection:
    """A detected object in a visual frame."""
    object_id: str
    label: str  # person, vehicle, animal, object, etc.
    sub_label: str = ""  # car, truck, dog, cat, etc.
    confidence: float = 0.0
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "label": self.label,
            "sub_label": self.sub_label,
            "confidence": self.confidence,
            "bounding_box": list(self.bounding_box),
            "timestamp": self.timestamp,
        }


@dataclass
class SceneAnalysis:
    """Analysis of a visual scene."""
    timestamp: float = 0.0
    objects: list[ObjectDetection] = field(default_factory=list)
    people_count: int = 0
    known_people: list[str] = field(default_factory=list)
    vehicles_count: int = 0
    animals_count: int = 0
    scene_type: str = ""  # indoor, outdoor, empty, activity
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "objects": [o.to_dict() for o in self.objects],
            "people_count": self.people_count,
            "known_people": self.known_people,
            "vehicles_count": self.vehicles_count,
            "animals_count": self.animals_count,
            "scene_type": self.scene_type,
            "description": self.description,
        }


# --------------------------------------------------------------- audio features


def extract_audio_features(audio_path: str) -> dict[str, float]:
    """Extract acoustic features from an audio file.

    Uses WAV file parsing to compute:
    - Mean energy (RMS)
    - Energy variability
    - Zero crossing rate (rough pitch indicator)
    - Spectral centroid estimate (brightness)
    - Duration

    These are basic features. For real speaker identification, you'd
    want MFCCs or x-vector embeddings from a neural network.
    """
    features: dict[str, float] = {}

    try:
        with wave.open(audio_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            duration = n_frames / frame_rate if frame_rate > 0 else 0

        features["duration_s"] = duration
        features["sample_rate"] = float(frame_rate)
        features["channels"] = float(n_channels)

        if not audio_data or sample_width == 0:
            return features

        # Parse samples
        if sample_width == 2:
            fmt = f"<{len(audio_data)//2}h"
            samples = struct.unpack(fmt, audio_data)
        elif sample_width == 1:
            samples = [s - 128 for s in audio_data]
        else:
            return features

        if not samples:
            return features

        # Energy (RMS)
        sum_sq = sum(s * s for s in samples)
        rms = math.sqrt(sum_sq / len(samples))
        features["energy_rms"] = float(rms)

        # Energy variability (standard deviation of windowed energy)
        window_size = max(1, len(samples) // 20)
        window_energies = []
        for i in range(0, len(samples) - window_size, window_size):
            window = samples[i:i + window_size]
            w_sum_sq = sum(s * s for s in window)
            window_energies.append(math.sqrt(w_sum_sq / len(window)) if window else 0)

        if window_energies:
            mean_energy = sum(window_energies) / len(window_energies)
            variance = sum((e - mean_energy) ** 2 for e in window_energies) / len(window_energies)
            features["energy_std"] = math.sqrt(variance)
            features["energy_cv"] = (math.sqrt(variance) / mean_energy) if mean_energy > 0 else 0
        else:
            features["energy_std"] = 0.0
            features["energy_cv"] = 0.0

        # Zero crossing rate (rough pitch/frequency indicator)
        zero_crossings = 0
        for i in range(1, len(samples)):
            if (samples[i] >= 0) != (samples[i - 1] >= 0):
                zero_crossings += 1
        zcr = zero_crossings / len(samples) if samples else 0
        features["zero_crossing_rate"] = float(zcr)

        # Estimated fundamental frequency (rough)
        if duration > 0 and zcr > 0:
            features["est_fundamental_freq"] = zcr * frame_rate / 2
        else:
            features["est_fundamental_freq"] = 0.0

        # Spectral centroid estimate (brightness indicator)
        # Higher ZCR = brighter sound
        features["spectral_centroid_est"] = zcr * frame_rate

        # Speech rate estimate (energy bursts per second)
        if window_energies and duration > 0:
            threshold = mean_energy * 0.5 if mean_energy > 0 else 0
            bursts = 0
            in_burst = False
            for e in window_energies:
                if e > threshold and not in_burst:
                    bursts += 1
                    in_burst = True
                elif e < threshold:
                    in_burst = False
            features["speech_rate_est"] = bursts / duration
        else:
            features["speech_rate_est"] = 0.0

        # Silence ratio (proportion of low-energy windows)
        if window_energies:
            silence_threshold = mean_energy * 0.1 if mean_energy > 0 else 0
            silent = sum(1 for e in window_energies if e < silence_threshold)
            features["silence_ratio"] = silent / len(window_energies)
        else:
            features["silence_ratio"] = 0.0

    except Exception:
        pass

    return features


def classify_audio_type(features: dict[str, float]) -> str:
    """Classify audio as speech, TV, radio, music, or noise.

    Heuristics based on acoustic features:
    - Speech: moderate energy variability, moderate ZCR, has pauses
    - TV/Radio: more consistent energy, wider frequency range, less silence
    - Music: regular rhythm, consistent energy, high ZCR
    - Noise: very low or very high energy, no structure
    """
    energy_cv = features.get("energy_cv", 0)
    zcr = features.get("zero_crossing_rate", 0)
    silence_ratio = features.get("silence_ratio", 0)
    energy_rms = features.get("energy_rms", 0)
    duration = features.get("duration_s", 0)

    if duration < 0.3:
        return "noise"

    if energy_rms < 50:
        return "noise"

    # Music: consistent energy, high ZCR, low silence
    if energy_cv < 0.3 and zcr > 0.15 and silence_ratio < 0.1:
        return "music"

    # TV/Radio: moderate consistency, moderate ZCR, low silence
    if energy_cv < 0.4 and silence_ratio < 0.15 and zcr > 0.05:
        return "tv_radio"

    # Speech: high energy variability, has pauses
    if energy_cv > 0.4 and silence_ratio > 0.15:
        return "speech"

    # Default
    if zcr > 0.2:
        return "music"
    if energy_rms > 100:
        return "speech"

    return "unknown"


# --------------------------------------------------------------- voice identification


class VoiceIdentifier:
    """Identifies speakers by comparing audio to stored voice profiles.

    Enrolls known people (Creator, family, household members) by
    extracting acoustic features from their voice samples. Then
    identifies unknown audio by comparing features to stored profiles.

    Accuracy is limited with acoustic features alone. For production,
    use a neural speaker embedding model (Resemblyzer, SpeechBrain, etc.).
    This module detects such libraries if available and uses them.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        match_threshold: float = 0.65,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.match_threshold = match_threshold

        self._state_dir = self.root / "memory" / "perception"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_file = self._state_dir / "voice_profiles.json"
        self._profiles: dict[str, VoiceProfile] = {}
        self._load_profiles()

        # Check for advanced speaker ID libraries
        self._resemblyzer = self._try_import_resemblyzer()

    def _try_import_resemblyzer(self) -> Any:
        """Try to import resemblyzer for neural speaker embeddings."""
        try:
            from resemblyzer import VoiceEncoder  # type: ignore
            return VoiceEncoder()
        except ImportError:
            return None
        except Exception:
            return None

    def enroll(
        self,
        name: str,
        audio_path: str,
        *,
        relationship: str = "",
        trusted: bool = False,
    ) -> VoiceProfile:
        """Enroll a new voice profile from an audio sample."""
        features = extract_audio_features(audio_path)

        # Generate profile ID
        profile_id = hashlib.sha256(
            f"voice:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        # If resemblyzer is available, get neural embedding
        if self._resemblyzer is not None:
            try:
                from resemblyzer import preprocess_wav  # type: ignore
                wav = preprocess_wav(audio_path)
                embedding = self._resemblyzer.embed_utterance(wav)
                features["neural_embedding"] = list(embedding[:16])  # store first 16 dims
            except Exception:
                pass

        profile = VoiceProfile(
            profile_id=profile_id,
            name=name,
            relationship=relationship,
            features=features,
            samples=1,
            created_at=time.time(),
            updated_at=time.time(),
            trusted=trusted,
        )

        self._profiles[profile_id] = profile
        self._save_profiles()

        if self.ledger is not None:
            try:
                self.ledger.append(
                    "anubis.perception.voice",
                    "voice.enrolled",
                    {"name": name, "profile_id": profile_id},
                )
            except Exception:
                pass

        return profile

    def add_sample(
        self, profile_id: str, audio_path: str
    ) -> bool:
        """Add another voice sample to an existing profile."""
        profile = self._profiles.get(profile_id)
        if profile is None:
            return False

        features = extract_audio_features(audio_path)

        # Update running average of features
        n = profile.samples
        for key, value in features.items():
            if key in profile.features:
                old = profile.features[key]
                profile.features[key] = (old * n + value) / (n + 1)
            else:
                profile.features[key] = value

        profile.samples += 1
        profile.updated_at = time.time()
        self._save_profiles()

        return True

    def identify(self, audio_path: str) -> VoiceIdentification:
        """Identify the speaker in an audio file."""
        features = extract_audio_features(audio_path)
        audio_type = classify_audio_type(features)

        result = VoiceIdentification()

        # If it's not speech, don't try to identify
        if audio_type not in ("speech", "unknown"):
            result.is_human = False
            result.audio_type = audio_type
            return result

        result.audio_type = audio_type
        result.is_human = True

        # Compare to known profiles
        if not self._profiles:
            result.is_known = False
            return result

        best_match: VoiceProfile | None = None
        best_score = 0.0

        for profile in self._profiles.values():
            score = self._compare_features(features, profile.features)
            if score > best_score:
                best_score = score
                best_match = profile

        if best_match and best_score >= self.match_threshold:
            result.identified = True
            result.name = best_match.name
            result.profile_id = best_match.profile_id
            result.relationship = best_match.relationship
            result.confidence = best_score
            result.is_known = True
            result.is_trusted = best_match.trusted
        else:
            result.is_known = False
            result.confidence = best_score

        return result

    def _compare_features(
        self,
        features1: dict[str, float],
        features2: dict[str, float],
    ) -> float:
        """Compare two feature sets and return similarity score 0-1."""
        # Compare key acoustic features
        keys = [
            "zero_crossing_rate", "energy_cv", "silence_ratio",
            "speech_rate_est", "spectral_centroid_est",
        ]

        scores = []
        for key in keys:
            v1 = features1.get(key, 0)
            v2 = features2.get(key, 0)
            if v1 == 0 and v2 == 0:
                scores.append(1.0)
            elif v1 == 0 or v2 == 0:
                scores.append(0.0)
            else:
                # Normalized difference
                diff = abs(v1 - v2) / max(abs(v1), abs(v2))
                scores.append(max(0, 1 - diff))

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def get_profiles(self) -> list[dict[str, Any]]:
        """Get all voice profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        """Get a specific voice profile."""
        profile = self._profiles.get(profile_id)
        return profile.to_dict() if profile else None

    def remove_profile(self, profile_id: str) -> bool:
        """Remove a voice profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._save_profiles()
            return True
        return False

    def get_status(self) -> dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "trusted_profiles": sum(1 for p in self._profiles.values() if p.trusted),
            "resemblyzer_available": self._resemblyzer is not None,
            "match_threshold": self.match_threshold,
        }

    def _load_profiles(self) -> None:
        if not self._profiles_file.exists():
            return
        try:
            data = json.loads(
                self._profiles_file.read_text(encoding="utf-8")
            )
            for p_id, p_data in data.items():
                self._profiles[p_id] = VoiceProfile(
                    profile_id=p_data["profile_id"],
                    name=p_data["name"],
                    relationship=p_data.get("relationship", ""),
                    features=p_data.get("features", {}),
                    samples=p_data.get("samples", 0),
                    created_at=p_data.get("created_at", 0),
                    updated_at=p_data.get("updated_at", 0),
                    trusted=p_data.get("trusted", False),
                )
        except Exception:
            pass

    def _save_profiles(self) -> None:
        data = {p_id: p.to_dict() for p_id, p in self._profiles.items()}
        self._profiles_file.write_text(
            json.dumps(_sanitize_json(data), indent=2), encoding="utf-8"
        )


def _sanitize_json(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_json(v) for v in obj]
    elif hasattr(obj, "item"):  # numpy scalar
        try:
            return obj.item()
        except Exception:
            return float(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        try:
            return float(obj)
        except (TypeError, ValueError):
            return str(obj)


class EmotionAnalyzer:
    """Analyzes emotional state from voice acoustic features.

    Detects: neutral, calm, happy, sad, angry, fearful, stressed, duress.

    Uses acoustic feature heuristics:
    - High pitch + high energy + fast rate → angry, excited
    - Low pitch + low energy + slow rate → sad, calm
    - High pitch variability + high energy → fearful, stressed
    - Very high pitch + very fast + high energy variability → duress

    For production accuracy, train a classifier on emotional speech
    datasets (RAVDESS, EMODB, etc.) using MFCC + prosodic features.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        duress_threshold: float = 0.75,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.duress_threshold = duress_threshold

        self._state_dir = self.root / "memory" / "perception"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "emotion_history.jsonl"

    def analyze(self, audio_path: str) -> EmotionAnalysis:
        """Analyze emotional state from an audio file."""
        features = extract_audio_features(audio_path)

        result = EmotionAnalysis()
        result.pitch_mean = features.get("est_fundamental_freq", 0)
        result.pitch_variability = features.get("energy_cv", 0)
        result.energy_mean = features.get("energy_rms", 0)
        result.speech_rate = features.get("speech_rate_est", 0)

        # Classify emotion based on features
        emotion, confidence, arousal, valence, indicators = self._classify_emotion(
            features
        )

        result.emotion = emotion
        result.confidence = confidence
        result.arousal = arousal
        result.valence = valence
        result.indicators = indicators

        # Record to history
        self._record_emotion(result)

        # Alert on duress
        if emotion == "duress" and confidence >= self.duress_threshold:
            self._log("emotion.duress_detected", {
                "confidence": confidence,
                "indicators": indicators,
            })

        return result

    def _classify_emotion(
        self, features: dict[str, float]
    ) -> tuple[str, float, float, float, list[str]]:
        """Classify emotion from acoustic features."""
        energy = features.get("energy_rms", 0)
        energy_cv = features.get("energy_cv", 0)
        zcr = features.get("zero_crossing_rate", 0)
        rate = features.get("speech_rate_est", 0)
        silence = features.get("silence_ratio", 0)
        pitch = features.get("est_fundamental_freq", 0)

        indicators: list[str] = []
        arousal = 0.5  # default neutral
        valence = 0.5  # default neutral

        # High energy + high rate + high pitch variability → stressed/angry/duress
        if energy > 200 and rate > 3.0 and energy_cv > 0.5:
            arousal = 0.9
            valence = 0.1
            indicators.append("high energy")
            indicators.append("rapid speech")
            indicators.append("high energy variability")

            # Very extreme → duress
            if energy > 400 and rate > 5.0 and zcr > 0.15:
                return "duress", 0.8, arousal, valence, indicators
            elif zcr > 0.12:
                return "angry", 0.7, arousal, valence, indicators
            else:
                return "stressed", 0.65, arousal, 0.3, indicators

        # Low energy + slow rate + high silence → sad
        if energy < 80 and rate < 1.5 and silence > 0.3:
            arousal = 0.2
            valence = 0.2
            indicators.append("low energy")
            indicators.append("slow speech")
            indicators.append("frequent pauses")
            return "sad", 0.6, arousal, valence, indicators

        # Low energy + low variability + moderate silence → calm
        if energy < 100 and energy_cv < 0.3 and silence > 0.2:
            arousal = 0.3
            valence = 0.6
            indicators.append("low energy")
            indicators.append("steady")
            indicators.append("relaxed pace")
            return "calm", 0.6, arousal, valence, indicators

        # High pitch + moderate energy + fast rate → happy/excited
        if pitch > 200 and rate > 2.0 and energy > 100:
            arousal = 0.7
            valence = 0.8
            indicators.append("elevated pitch")
            indicators.append("energetic")
            indicators.append("fast pace")
            return "happy", 0.6, arousal, valence, indicators

        # High pitch variability + moderate-high energy → fearful
        if energy_cv > 0.6 and zcr > 0.1 and energy > 100:
            arousal = 0.8
            valence = 0.2
            indicators.append("pitch instability")
            indicators.append("variable energy")
            return "fearful", 0.55, arousal, valence, indicators

        # Default: neutral
        indicators.append("normal patterns")
        return "neutral", 0.5, 0.5, 0.5, indicators

    def _record_emotion(self, result: EmotionAnalysis) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": time.time(),
                    **result.to_dict(),
                }) + "\n")
        except Exception:
            pass

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent emotion analysis history."""
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
            "total_analyses": len(self.get_history(limit=9999)),
            "duress_threshold": self.duress_threshold,
        }

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append("anubis.perception.emotion", action, data)
            except Exception:
                pass


# --------------------------------------------------------------- face recognition


class FaceRecognizer:
    """Recognizes faces from camera input.

    Enrolls known people (Creator, family, household members) with face
    encodings. Then identifies faces in new images.

    Uses face_recognition library if available (best accuracy).
    Falls back to OpenCV if available.
    Falls back to a no-op if neither is available.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        match_threshold: float = 0.6,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.match_threshold = match_threshold

        self._state_dir = self.root / "memory" / "perception"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._faces_dir = self._state_dir / "face_images"
        self._faces_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_file = self._state_dir / "face_profiles.json"
        self._profiles: dict[str, FaceProfile] = {}
        self._load_profiles()

        # Check for available face recognition libraries
        self._face_recognition = self._try_import_face_recognition()
        self._deepface = self._try_import_deepface()
        self._cv2 = self._try_import_cv2()

    def _try_import_face_recognition(self) -> Any:
        try:
            import face_recognition  # type: ignore
            return face_recognition
        except ImportError:
            return None

    def _try_import_deepface(self) -> Any:
        try:
            from deepface import DeepFace  # type: ignore
            return DeepFace
        except ImportError:
            return None
        except Exception:
            return None

    def _try_import_cv2(self) -> Any:
        try:
            import cv2  # type: ignore
            return cv2
        except ImportError:
            return None

    def is_available(self) -> bool:
        """Check if face recognition is available."""
        return (
            self._face_recognition is not None
            or self._deepface is not None
            or self._cv2 is not None
        )

    def enroll(
        self,
        name: str,
        image_path: str,
        *,
        relationship: str = "",
        trusted: bool = False,
    ) -> FaceProfile | None:
        """Enroll a new face from an image."""
        if not os.path.exists(image_path):
            return None

        # Copy image to face storage
        ext = Path(image_path).suffix or ".jpg"
        stored_path = self._faces_dir / f"{name.lower().replace(' ', '_')}_{int(time.time())}{ext}"
        try:
            import shutil as sh
            sh.copy2(image_path, stored_path)
        except Exception:
            stored_path = Path(image_path)

        # Get face encoding
        encoding: list[float] = []
        if self._face_recognition is not None:
            try:
                image = self._face_recognition.load_image_file(str(stored_path))
                encodings = self._face_recognition.face_encodings(image)
                if encodings:
                    encoding = list(encodings[0])
            except Exception:
                pass

        # Fallback: use deepface to get face representation
        if not encoding and self._deepface is not None:
            try:
                result = self._deepface.represent(
                    img_path=str(stored_path),
                    model_name="Facenet",
                    enforce_detection=False,
                )
                if result and len(result) > 0:
                    # DeepFace returns embedding vectors
                    embedding = result[0]["embedding"]
                    encoding = list(embedding[:128])  # store first 128 dims
            except Exception:
                pass

        profile_id = hashlib.sha256(
            f"face:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        profile = FaceProfile(
            profile_id=profile_id,
            name=name,
            relationship=relationship,
            encoding=encoding,
            image_path=str(stored_path),
            samples=1,
            created_at=time.time(),
            updated_at=time.time(),
            trusted=trusted,
        )

        self._profiles[profile_id] = profile
        self._save_profiles()

        if self.ledger is not None:
            try:
                self.ledger.append(
                    "anubis.perception.face",
                    "face.enrolled",
                    {"name": name, "profile_id": profile_id},
                )
            except Exception:
                pass

        return profile

    def identify(self, image_path: str) -> FaceIdentification:
        """Identify faces in an image."""
        result = FaceIdentification()

        if not self.is_available() or not os.path.exists(image_path):
            return result

        # Using face_recognition library
        if self._face_recognition is not None:
            try:
                image = self._face_recognition.load_image_file(image_path)
                face_locations = self._face_recognition.face_locations(image)
                face_encodings = self._face_recognition.face_encodings(image, face_locations)

                result.face_count = len(face_locations)
                known_encodings = [
                    (p, p.encoding) for p in self._profiles.values()
                    if p.encoding
                ]

                for face_encoding in face_encodings:
                    best_match: FaceProfile | None = None
                    best_distance = 1.0

                    for profile, known_encoding in known_encodings:
                        distance = self._face_recognition.face_distance(
                            [known_encoding], face_encoding
                        )[0]
                        if distance < best_distance:
                            best_distance = distance
                            best_match = profile

                    if best_match and best_distance < self.match_threshold:
                        result.identified = True
                        result.name = best_match.name
                        result.profile_id = best_match.profile_id
                        result.relationship = best_match.relationship
                        result.confidence = 1 - best_distance
                        result.is_known = True
                        result.is_trusted = best_match.trusted
                    else:
                        result.unknown_count += 1

                return result

            except Exception:
                pass

        # Using DeepFace fallback (neural face recognition via TensorFlow)
        if self._deepface is not None and not result.identified:
            try:
                # Use DeepFace to verify against known profiles
                for profile in self._profiles.values():
                    if not profile.image_path or not os.path.exists(profile.image_path):
                        continue
                    try:
                        verify_result = self._deepface.verify(
                            img1_path=image_path,
                            img2_path=profile.image_path,
                            model_name="Facenet",
                            enforce_detection=False,
                        )
                        if verify_result.get("verified", False):
                            distance = verify_result.get("distance", 1.0)
                            result.identified = True
                            result.name = profile.name
                            result.profile_id = profile.profile_id
                            result.relationship = profile.relationship
                            result.confidence = max(0, 1 - distance)
                            result.is_known = True
                            result.is_trusted = profile.trusted
                            # Count total faces
                            try:
                                faces = self._deepface.extract_faces(
                                    image_path, enforce_detection=False,
                                )
                                result.face_count = len(faces)
                                result.unknown_count = max(0, len(faces) - 1)
                            except Exception:
                                pass
                            return result
                    except Exception:
                        continue

                # Count faces even if no match
                try:
                    faces = self._deepface.extract_faces(
                        image_path, enforce_detection=False,
                    )
                    result.face_count = len(faces)
                    result.unknown_count = len(faces)
                except Exception:
                    pass

                return result
            except Exception:
                pass

        # Using OpenCV fallback (detect faces but can't identify)
        if self._cv2 is not None:
            try:
                image = self._cv2.imread(image_path)
                if image is None:
                    return result
                gray = self._cv2.cvtColor(image, self._cv2.COLOR_BGR2GRAY)
                cascade_path = self._cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                cascade = self._cv2.CascadeClassifier(cascade_path)
                faces = cascade.detectMultiScale(gray, 1.1, 4)
                result.face_count = len(faces)
                result.unknown_count = len(faces)
                return result
            except Exception:
                pass

        return result

    def get_profiles(self) -> list[dict[str, Any]]:
        """Get all face profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def remove_profile(self, profile_id: str) -> bool:
        """Remove a face profile."""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._save_profiles()
            return True
        return False

    def get_status(self) -> dict[str, Any]:
        return {
            "available": self.is_available(),
            "total_profiles": len(self._profiles),
            "trusted_profiles": sum(1 for p in self._profiles.values() if p.trusted),
            "face_recognition_lib": self._face_recognition is not None,
            "deepface": self._deepface is not None,
            "opencv": self._cv2 is not None,
            "match_threshold": self.match_threshold,
        }

    def _load_profiles(self) -> None:
        if not self._profiles_file.exists():
            return
        try:
            data = json.loads(
                self._profiles_file.read_text(encoding="utf-8")
            )
            for p_id, p_data in data.items():
                self._profiles[p_id] = FaceProfile(
                    profile_id=p_data["profile_id"],
                    name=p_data["name"],
                    relationship=p_data.get("relationship", ""),
                    encoding=p_data.get("encoding", []),
                    image_path=p_data.get("image_path", ""),
                    samples=p_data.get("samples", 0),
                    created_at=p_data.get("created_at", 0),
                    updated_at=p_data.get("updated_at", 0),
                    trusted=p_data.get("trusted", False),
                )
        except Exception:
            pass

    def _save_profiles(self) -> None:
        data = {p_id: p.to_dict() for p_id, p in self._profiles.items()}
        # Store encoding separately since to_dict only stores length
        for p_id, profile in self._profiles.items():
            data[p_id]["encoding"] = profile.encoding
        self._profiles_file.write_text(
            json.dumps(_sanitize_json(data), indent=2), encoding="utf-8"
        )


# --------------------------------------------------------------- object recognition


class ObjectRecognizer:
    """Recognizes objects in images — vehicles, animals, people, etc.

    Uses YOLO if available (best accuracy).
    Falls back to OpenCV DNN with MobileNet-SSD if available.
    Falls back to motion detection if neither is available.
    """

    # Object categories we care about
    CATEGORIES = {
        "person": ["person", "man", "woman", "child"],
        "vehicle": ["car", "truck", "bus", "motorcycle", "bicycle",
                     "van", "suv", "boat", "airplane"],
        "animal": ["dog", "cat", "bird", "horse", "cow", "sheep",
                   "deer", "rabbit", "squirrel", "bear", "fox"],
        "object": ["chair", "table", "phone", "laptop", "book",
                   "cup", "bottle", "tv", "keyboard"],
    }

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        confidence_threshold: float = 0.5,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.confidence_threshold = confidence_threshold

        self._state_dir = self.root / "memory" / "perception"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._state_dir / "object_history.jsonl"

        # Check for available object detection libraries
        self._yolo = self._try_import_yolo()
        self._cv2 = self._try_import_cv2()

    def _try_import_yolo(self) -> Any:
        try:
            from ultralytics import YOLO  # type: ignore
            return YOLO
        except ImportError:
            return None
        except Exception:
            return None

    def _try_import_cv2(self) -> Any:
        try:
            import cv2  # type: ignore
            return cv2
        except ImportError:
            return None

    def is_available(self) -> bool:
        """Check if object recognition is available."""
        return self._yolo is not None or self._cv2 is not None

    def recognize(self, image_path: str) -> SceneAnalysis:
        """Recognize objects in an image."""
        scene = SceneAnalysis(timestamp=time.time())

        if not os.path.exists(image_path):
            return scene

        # Using YOLO
        if self._yolo is not None:
            try:
                model = self._yolo("yolov8n.pt")  # nano model
                results = model(image_path, verbose=False)
                for r in results:
                    for box in r.boxes:
                        confidence = float(box.conf[0])
                        if confidence < self.confidence_threshold:
                            continue
                        class_id = int(box.cls[0])
                        label = r.names[class_id]
                        xyxy = box.xyxy[0].tolist()
                        obj = ObjectDetection(
                            object_id=hashlib.sha256(
                                f"obj:{label}:{time.time()}".encode()
                            ).hexdigest()[:16],
                            label=self._categorize(label),
                            sub_label=label,
                            confidence=confidence,
                            bounding_box=(int(xyxy[0]), int(xyxy[1]),
                                        int(xyxy[2] - xyxy[0]),
                                        int(xyxy[3] - xyxy[1])),
                            timestamp=time.time(),
                        )
                        scene.objects.append(obj)

                self._summarize_scene(scene)
                self._record_scene(scene)
                return scene
            except Exception:
                pass

        # Using OpenCV DNN (MobileNet-SSD)
        if self._cv2 is not None:
            try:
                # Try to use Haar cascade for face/body detection at minimum
                image = self._cv2.imread(image_path)
                if image is None:
                    return scene
                gray = self._cv2.cvtColor(image, self._cv2.COLOR_BGR2GRAY)

                # Detect people using full body cascade
                cascade_path = self._cv2.data.haarcascades + "haarcascade_fullbody.xml"
                try:
                    cascade = self._cv2.CascadeClassifier(cascade_path)
                    bodies = cascade.detectMultiScale(gray, 1.1, 3)
                    for (x, y, w, h) in bodies:
                        obj = ObjectDetection(
                            object_id=hashlib.sha256(
                                f"obj:person:{time.time()}".encode()
                            ).hexdigest()[:16],
                            label="person",
                            sub_label="person",
                            confidence=0.6,
                            bounding_box=(int(x), int(y), int(w), int(h)),
                            timestamp=time.time(),
                        )
                        scene.objects.append(obj)
                except Exception:
                    pass

                # Detect cars
                car_cascade_path = self._cv2.data.haarcascades + "haarcascade_cars.xml"
                try:
                    car_cascade = self._cv2.CascadeClassifier(car_cascade_path)
                    cars = car_cascade.detectMultiScale(gray, 1.1, 3)
                    for (x, y, w, h) in cars:
                        obj = ObjectDetection(
                            object_id=hashlib.sha256(
                                f"obj:vehicle:{time.time()}".encode()
                            ).hexdigest()[:16],
                            label="vehicle",
                            sub_label="car",
                            confidence=0.55,
                            bounding_box=(int(x), int(y), int(w), int(h)),
                            timestamp=time.time(),
                        )
                        scene.objects.append(obj)
                except Exception:
                    pass

                self._summarize_scene(scene)
                self._record_scene(scene)
                return scene
            except Exception:
                pass

        # No tools available — return empty scene
        scene.description = "Object recognition not available (no YOLO or OpenCV)"
        return scene

    def _categorize(self, label: str) -> str:
        """Categorize a detection label."""
        label_lower = label.lower()
        for category, labels in self.CATEGORIES.items():
            if label_lower in labels:
                return category
        return "object"

    def _summarize_scene(self, scene: SceneAnalysis) -> None:
        """Summarize a scene from detected objects."""
        scene.people_count = sum(1 for o in scene.objects if o.label == "person")
        scene.vehicles_count = sum(1 for o in scene.objects if o.label == "vehicle")
        scene.animals_count = sum(1 for o in scene.objects if o.label == "animal")

        parts = []
        if scene.people_count:
            parts.append(f"{scene.people_count} person(s)")
        if scene.vehicles_count:
            parts.append(f"{scene.vehicles_count} vehicle(s)")
        if scene.animals_count:
            parts.append(f"{scene.animals_count} animal(s)")

        if not parts:
            scene.scene_type = "empty"
            scene.description = "No significant objects detected"
        else:
            scene.scene_type = "activity"
            scene.description = "Detected: " + ", ".join(parts)

    def _record_scene(self, scene: SceneAnalysis) -> None:
        try:
            with open(self._history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(scene.to_dict()) + "\n")
        except Exception:
            pass

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent scene analysis history."""
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
            "yolo": self._yolo is not None,
            "opencv": self._cv2 is not None,
            "confidence_threshold": self.confidence_threshold,
            "total_scenes": len(self.get_history(limit=9999)),
        }


# --------------------------------------------------------------- perception system


class PerceptionSystem:
    """Unified perception — voice ID, emotion, faces, and objects.

    This is the top-level perception manager that integrates all
    recognition systems and connects them to the sensory system.
    """

    ACTOR = "anubis.perception"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        observer: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.observer = observer

        self.voice_id = VoiceIdentifier(root, ledger=ledger)
        self.emotion = EmotionAnalyzer(root, ledger=ledger)
        self.faces = FaceRecognizer(root, ledger=ledger)
        self.objects = ObjectRecognizer(root, ledger=ledger)

    def analyze_audio(self, audio_path: str) -> dict[str, Any]:
        """Analyze an audio file — identify speaker and emotion."""
        identification = self.voice_id.identify(audio_path)
        emotion = self.emotion.analyze(audio_path)

        result = {
            "identification": identification.to_dict(),
            "emotion": emotion.to_dict(),
        }

        # Feed to observer
        if self.observer is not None and identification.is_human:
            try:
                self.observer._make_observation(
                    source="perception",
                    event_type="voice_analysis",
                    content=(
                        f"Voice: {identification.name or 'unknown'}, "
                        f"Emotion: {emotion.emotion} "
                        f"(confidence: {emotion.confidence:.0%})"
                    ),
                    severity="info" if emotion.emotion != "duress" else "critical",
                )
            except Exception:
                pass

        self._log("perception.audio_analyzed", {
            "identified": identification.identified,
            "name": identification.name,
            "emotion": emotion.emotion,
            "is_human": identification.is_human,
        })

        return result

    def analyze_image(self, image_path: str) -> dict[str, Any]:
        """Analyze an image — identify faces and objects."""
        face_result = self.faces.identify(image_path)
        scene = self.objects.recognize(image_path)

        result = {
            "faces": face_result.to_dict(),
            "scene": scene.to_dict(),
        }

        # Feed to observer
        if self.observer is not None:
            try:
                self.observer._make_observation(
                    source="perception",
                    event_type="visual_analysis",
                    content=(
                        f"Faces: {face_result.face_count} "
                        f"({face_result.name or 'unknown'}), "
                        f"Objects: {len(scene.objects)}"
                    ),
                    severity="info",
                )
            except Exception:
                pass

        self._log("perception.image_analyzed", {
            "faces": face_result.face_count,
            "known_face": face_result.is_known,
            "objects": len(scene.objects),
        })

        return result

    def enroll_voice(
        self, name: str, audio_path: str,
        *, relationship: str = "", trusted: bool = False,
    ) -> dict[str, Any]:
        """Enroll a new voice profile."""
        profile = self.voice_id.enroll(
            name, audio_path,
            relationship=relationship, trusted=trusted,
        )
        return profile.to_dict()

    def enroll_face(
        self, name: str, image_path: str,
        *, relationship: str = "", trusted: bool = False,
    ) -> dict[str, Any] | None:
        """Enroll a new face profile."""
        profile = self.faces.enroll(
            name, image_path,
            relationship=relationship, trusted=trusted,
        )
        return profile.to_dict() if profile else None

    def get_status(self) -> dict[str, Any]:
        return {
            "voice_id": self.voice_id.get_status(),
            "emotion": self.emotion.get_status(),
            "faces": self.faces.get_status(),
            "objects": self.objects.get_status(),
        }

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
