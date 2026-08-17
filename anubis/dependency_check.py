"""Dependency manifest and self-check — track ANUBIS's self-reliance.

Monitors all external dependencies and reports which have been
replaced with self-hosted alternatives. This is the scoreboard
for Phase 2: replacing outside software.

Each dependency is tracked with:
- name: The dependency name
- type: "service", "pip_package", "system_binary", "model"
- status: "replaced", "optional", "active", "missing"
- replacement: What replaces it (if replaced)
- fallback: What happens if it's unavailable
- replaced_at: When it was replaced (timestamp)

The self-check runs at startup and reports the overall self-reliance
percentage: what percentage of dependencies have been replaced or
made optional.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class Dependency:
    """A single external dependency."""
    name: str
    type: str  # service, pip_package, system_binary, model
    status: str = "active"  # replaced, optional, active, missing
    replacement: str = ""
    fallback: str = ""
    replaced_at: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "replacement": self.replacement,
            "fallback": self.fallback,
            "replaced_at": self.replaced_at,
            "notes": self.notes,
        }


# The canonical dependency manifest
DEPENDENCY_MANIFEST: list[Dependency] = [
    # --- Services ---
    Dependency(
        name="Ollama",
        type="service",
        status="optional",
        replacement="anubis.local_inference.LocalInferenceEngine",
        fallback="Falls back to Ollama if no self-hosted backend available",
        notes="Local inference engine (llama.cpp/pure Python) replaces Ollama",
    ),
    # --- Models ---
    Dependency(
        name="nomic-embed-text",
        type="model",
        status="optional",
        replacement="anubis.custom_embeddings.EmbeddingModel",
        fallback="Falls back to nomic-embed-text via Ollama if custom model not trained",
        notes="Custom TF-IDF hash-projection embedding model",
    ),
    Dependency(
        name="qwen2.5-coder:7b",
        type="model",
        status="active",
        replacement="",
        fallback="",
        notes="Primary model — will be replaced by ANUBIS's own trained model",
    ),
    # --- Pip packages ---
    Dependency(
        name="paramiko",
        type="pip_package",
        status="replaced",
        replacement="stdlib subprocess + ssh command",
        fallback="Falls back to paramiko only if ssh binary unavailable",
        replaced_at=time.time(),
        notes="VPN setup now uses system ssh via subprocess",
    ),
    Dependency(
        name="vosk",
        type="pip_package",
        status="optional",
        replacement="whisper.cpp subprocess (self-hosted)",
        fallback="Returns empty string if no STT backend available",
        notes="Speech-to-text with vosk/whisper.cpp fallback chain",
    ),
    Dependency(
        name="unsloth",
        type="pip_package",
        status="optional",
        replacement="Standard HuggingFace training (slower but no extra dep)",
        fallback="Falls back to standard Transformers training",
        notes="2-5x training acceleration — optional, not required",
    ),
    # --- System binaries ---
    Dependency(
        name="espeak-ng",
        type="system_binary",
        status="optional",
        replacement="",
        fallback="TTS returns empty string if not installed",
        notes="Text-to-speech — optional, only for voice interface",
    ),
    Dependency(
        name="arecord",
        type="system_binary",
        status="optional",
        replacement="ffmpeg (alternative audio recording)",
        fallback="STT returns empty string if no recording tool available",
        notes="Audio recording for STT — optional",
    ),
    # --- Cloud services ---
    Dependency(
        name="Gemini API",
        type="service",
        status="optional",
        replacement="anubis.cloud_phaseout (gradual phase-out)",
        fallback="Local model used when capability is graduated",
        notes="Cloud teacher — being phased out as local model improves",
    ),
    Dependency(
        name="Groq API",
        type="service",
        status="optional",
        replacement="anubis.cloud_phaseout (gradual phase-out)",
        fallback="Local model used when capability is graduated",
        notes="Cloud teacher backup — being phased out",
    ),
    Dependency(
        name="iDrive E2",
        type="service",
        status="active",
        replacement="",
        fallback="Local backups if cloud sync unavailable",
        notes="Cloud backup — active but not critical",
    ),
    Dependency(
        name="Lambda Cloud GPU",
        type="service",
        status="optional",
        replacement="Local GPU training (when available)",
        fallback="Training deferred if no GPU available",
        notes="Cloud GPU for training — optional",
    ),
]


class DependencyChecker:
    """Check dependency status and report self-reliance progress.

    Runs a self-check at startup to verify which dependencies are
    available, which have been replaced, and which are still active.
    """

    def __init__(self, ledger: Ledger | None = None) -> None:
        self.ledger = ledger
        self._manifest = list(DEPENDENCY_MANIFEST)

    def check_pip_package(self, name: str) -> bool:
        """Check if a pip package is installed."""
        try:
            __import__(name)
            return True
        except ImportError:
            return False

    def check_system_binary(self, name: str) -> bool:
        """Check if a system binary is available."""
        return shutil.which(name) is not None

    def check_service(self, name: str) -> bool:
        """Check if a service is available (simplified)."""
        if name == "Ollama":
            try:
                import urllib.request
                url = os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434")
                req = urllib.request.Request(f"{url}/api/tags")
                resp = urllib.request.urlopen(req, timeout=3)
                return resp.status == 200
            except Exception:
                return False
        # Cloud services — check if credentials exist
        creds_path = Path("config/cloud_credentials.json")
        if not creds_path.exists():
            return False
        try:
            creds = json.loads(creds_path.read_text(encoding="utf-8"))
            if name == "Gemini API":
                return bool(creds.get("gemini", {}).get("api_key"))
            if name == "Groq API":
                return bool(creds.get("groq", {}).get("api_key"))
            if name == "iDrive E2":
                return bool(creds.get("idrive_e2", {}).get("access_key"))
            if name == "Lambda Cloud GPU":
                return bool(creds.get("lambda", {}).get("api_key"))
        except Exception:
            pass
        return False

    def check_model(self, name: str) -> bool:
        """Check if a model is available."""
        if name == "nomic-embed-text":
            # Check if custom embedding model exists
            custom_path = Path(
                os.environ.get("ANUBIS_CUSTOM_EMBED", "memory/custom_embed_model.json")
            )
            if custom_path.exists():
                return True  # custom model replaces it
            # Check if Ollama has it
            return self.check_service("Ollama")
        if name == "qwen2.5-coder:7b":
            # Check if Ollama has the model
            try:
                import urllib.request
                url = os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434")
                req = urllib.request.Request(f"{url}/api/tags")
                resp = urllib.request.urlopen(req, timeout=3)
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(name in m for m in models)
            except Exception:
                return False
        return False

    def run_self_check(self) -> dict[str, Any]:
        """Run a full self-check of all dependencies.

        Returns a report with:
        - total dependencies
        - replaced count
        - optional count
        - active count
        - self_reliance_pct
        - per-dependency status
        """
        results: list[dict[str, Any]] = []
        replaced = 0
        optional = 0
        active = 0
        missing = 0

        for dep in self._manifest:
            entry = dep.to_dict()

            # Check actual availability
            if dep.type == "pip_package":
                entry["installed"] = self.check_pip_package(dep.name)
            elif dep.type == "system_binary":
                entry["installed"] = self.check_system_binary(dep.name)
            elif dep.type == "service":
                entry["available"] = self.check_service(dep.name)
            elif dep.type == "model":
                entry["available"] = self.check_model(dep.name)

            # Count by status
            if dep.status == "replaced":
                replaced += 1
            elif dep.status == "optional":
                optional += 1
            elif dep.status == "active":
                active += 1
            elif dep.status == "missing":
                missing += 1

            results.append(entry)

        total = len(self._manifest)
        # Self-reliance = (replaced + optional) / total
        # "optional" means ANUBIS can function without it
        self_reliance = ((replaced + optional) / total * 100) if total > 0 else 0.0

        report = {
            "total_dependencies": total,
            "replaced": replaced,
            "optional": optional,
            "active": active,
            "missing": missing,
            "self_reliance_pct": round(self_reliance, 1),
            "dependencies": results,
            "checked_at": time.time(),
        }

        if self.ledger:
            self.ledger.append({
                "event": "dependency_self_check",
                "self_reliance_pct": round(self_reliance, 1),
                "replaced": replaced,
                "optional": optional,
                "active": active,
            })

        return report

    def status(self) -> dict[str, Any]:
        """Quick status without full check."""
        replaced = sum(1 for d in self._manifest if d.status == "replaced")
        optional = sum(1 for d in self._manifest if d.status == "optional")
        active = sum(1 for d in self._manifest if d.status == "active")
        total = len(self._manifest)
        return {
            "total": total,
            "replaced": replaced,
            "optional": optional,
            "active": active,
            "self_reliance_pct": round((replaced + optional) / total * 100, 1),
        }

    def get_dependency(self, name: str) -> Dependency | None:
        """Get a specific dependency by name."""
        for dep in self._manifest:
            if dep.name == name:
                return dep
        return None

    def mark_replaced(self, name: str, replacement: str) -> bool:
        """Mark a dependency as replaced.

        Call this when a dependency has been successfully replaced
        with a self-hosted alternative.
        """
        dep = self.get_dependency(name)
        if dep is None:
            return False
        dep.status = "replaced"
        dep.replacement = replacement
        dep.replaced_at = time.time()

        if self.ledger:
            self.ledger.append({
                "event": "dependency_replaced",
                "name": name,
                "replacement": replacement,
            })

        return True
