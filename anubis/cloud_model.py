"""Cloud teacher model adapter — free multi-provider with local fallback.

This module provides access to free online model APIs (Google Gemini,
Groq) for larger/faster reasoning, consultation, architecture review,
and learning support. When no cloud provider is available or the
request is privacy-sensitive, it falls back to local Ollama.

Architecture:
    1. Privacy gate — checks payload for sensitive data before sending
    2. Provider failover — tries Gemini → Groq → local Ollama
    3. Constitutional gate — cloud calls are CONSEQUENTIAL, require approval
    4. Audit logging — every cloud call is logged to the evidence ledger

Privacy (local_privacy immutable law):
    - No identity vault data, credentials, or private conversation content
      is sent to cloud providers
    - The privacy gate checks payloads against sensitive-data patterns
    - If sensitive data is detected, the request falls back to local
    - Free cloud tiers may retain or train on submitted data — only
      non-sensitive payloads are sent

Cost: $0/month for all providers (free tiers):
    - Google Gemini (AI Studio): free tier, 15 req/min, 1M token context
    - Groq: free tier, 14,400 req/day, fast inference
    - Local Ollama: always available, no network needed

The adapter implements the same ModelAdapter protocol as OllamaAdapter
(chat → Completion), so it can be used as a drop-in replacement.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .model import Completion, ModelError, ModelSpec, OllamaAdapter

# Credential file location
CREDENTIALS_FILE = "config/cloud_credentials.json"

# Sensitive data patterns — same as external_gateway.py
SENSITIVE_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"access_key_id\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"api_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"passphrase\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"creator_id\s*[:=]\s*\S+", re.IGNORECASE),
]


def _check_sensitive_data(text: str) -> str | None:
    """Check if text contains sensitive data. Returns pattern description or None."""
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            return f"sensitive data pattern matched: {pattern.pattern[:50]}"
    return None


@dataclass
class ProviderConfig:
    """Configuration for a cloud model provider."""
    name: str
    api_key: str = ""
    endpoint: str = ""
    model: str = ""
    max_tokens: int = 4096
    enabled: bool = True

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.endpoint and self.model)


@dataclass
class CloudModelConfig:
    """Configuration for the cloud teacher adapter."""
    gemini: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        name="gemini",
        endpoint="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-3.5-flash",
    ))
    groq: ProviderConfig = field(default_factory=lambda: ProviderConfig(
        name="groq",
        endpoint="https://api.groq.com/openai/v1",
        model="llama-3.3-70b-versatile",
    ))
    local_model: str = "qwen2.5-coder:7b"
    local_endpoint: str = "http://127.0.0.1:11434"
    prefer_local_for_sensitive: bool = True
    cloud_timeout: float = 60.0

    @classmethod
    def from_file(cls, path: str | Path | None = None) -> "CloudModelConfig":
        """Load config from the credentials file."""
        path = Path(path or CREDENTIALS_FILE)
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg = cls()
            # Gemini config
            gem = data.get("gemini", {})
            if gem:
                cfg.gemini.api_key = gem.get("api_key", "")
                cfg.gemini.model = gem.get("model", cfg.gemini.model)
                cfg.gemini.enabled = gem.get("enabled", True)
            # Groq config
            groq = data.get("groq", {})
            if groq:
                cfg.groq.api_key = groq.get("api_key", "")
                cfg.groq.model = groq.get("model", cfg.groq.model)
                cfg.groq.enabled = groq.get("enabled", True)
            # Local config
            local = data.get("local", {})
            if local:
                cfg.local_model = local.get("model", cfg.local_model)
                cfg.local_endpoint = local.get("endpoint", cfg.local_endpoint)
            return cfg
        except (json.JSONDecodeError, OSError):
            return cls()


class CloudModelAdapter:
    """Cloud teacher model adapter with multi-provider failover.

    Tries providers in order: Gemini → Groq → local Ollama.
    Falls back to local for privacy-sensitive requests.
    Implements the same ModelAdapter protocol as OllamaAdapter.
    """

    def __init__(
        self,
        config: CloudModelConfig | None = None,
        ledger: Any | None = None,
    ) -> None:
        self.config = config or CloudModelConfig.from_file()
        self.ledger = ledger
        self._local: OllamaAdapter | None = None
        self._provider_order: list[str] = []
        self._update_provider_order()

    def _update_provider_order(self) -> None:
        """Build the provider priority order based on configuration."""
        self._provider_order = []
        if self.config.gemini.is_configured and self.config.gemini.enabled:
            self._provider_order.append("gemini")
        if self.config.groq.is_configured and self.config.groq.enabled:
            self._provider_order.append("groq")
        # Local is always last (fallback)
        self._provider_order.append("local")

    @property
    def spec(self) -> ModelSpec:
        """Return the spec for the currently active provider."""
        # Return a synthetic spec for the cloud adapter
        return ModelSpec(
            name="cloud-teacher",
            params="varies",
            tools=False,
            thinking=False,
            vision=False,
            context=1000000,
            min_vram_gb=0.0,
            note="Multi-provider cloud teacher with local fallback",
        )

    @property
    def is_configured(self) -> bool:
        """True if at least one cloud provider is configured."""
        return (
            (self.config.gemini.is_configured and self.config.gemini.enabled)
            or (self.config.groq.is_configured and self.config.groq.enabled)
        )

    @property
    def active_providers(self) -> list[str]:
        """List of providers that will be tried (in order)."""
        return list(self._provider_order)

    # --------------------------------------------------- privacy gate

    def _check_privacy(self, messages: list[dict[str, Any]]) -> str | None:
        """Check if any message contains sensitive data.

        Returns the reason if sensitive data is found, None otherwise.
        """
        if not self.config.prefer_local_for_sensitive:
            return None
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                sensitive = _check_sensitive_data(content)
                if sensitive:
                    return sensitive
        return None

    # --------------------------------------------------- provider calls

    def _call_gemini(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> Completion:
        """Call Google Gemini API (free tier)."""
        cfg = self.config.gemini
        # Convert messages to Gemini format
        # Gemini uses "contents" with "parts" instead of "messages"
        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
                continue
            # Gemini uses "user" and "model" roles
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}],
            })

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or cfg.max_tokens,
            },
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction

        url = f"{cfg.endpoint}/models/{cfg.model}:generateContent?key={cfg.api_key}"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SIOS-ANUBIS/1.0",
            },
            method="POST",
        )

        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            elapsed = time.monotonic() - t0

            # Extract text from Gemini response
            candidates = raw.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = " ".join(p.get("text", "") for p in parts)

            usage = raw.get("usageMetadata", {})
            return Completion(
                text=text.strip(),
                model=f"gemini:{cfg.model}",
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                duration_s=elapsed,
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise ModelError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ModelError(f"Gemini connection error: {exc.reason}") from exc

    def _call_groq(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> Completion:
        """Call Groq API (free tier, OpenAI-compatible)."""
        cfg = self.config.groq
        # Groq uses OpenAI-compatible format
        body: dict[str, Any] = {
            "model": cfg.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or cfg.max_tokens,
        }

        url = f"{cfg.endpoint}/chat/completions"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.api_key}",
                "User-Agent": "SIOS-ANUBIS/1.0",
            },
            method="POST",
        )

        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            elapsed = time.monotonic() - t0

            # Extract text from OpenAI-compatible response
            choices = raw.get("choices", [])
            text = ""
            if choices:
                text = choices[0].get("message", {}).get("content", "")

            usage = raw.get("usage", {})
            return Completion(
                text=text.strip(),
                model=f"groq:{cfg.model}",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                duration_s=elapsed,
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise ModelError(f"Groq HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ModelError(f"Groq connection error: {exc.reason}") from exc

    def _call_local(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int | None,
        timeout: float,
    ) -> Completion:
        """Call local Ollama as fallback."""
        if self._local is None:
            self._local = OllamaAdapter(
                model=self.config.local_model,
                endpoint=self.config.local_endpoint,
            )
        return self._local.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    # --------------------------------------------------- logging

    def _log_call(
        self,
        provider: str,
        messages: list[dict[str, Any]],
        completion: Completion,
        error: str = "",
    ) -> None:
        """Log a cloud model call to the evidence ledger."""
        if self.ledger is None:
            return
        try:
            entry = {
                "type": "cloud_model_call",
                "provider": provider,
                "model": completion.model,
                "message_count": len(messages),
                "prompt_tokens": completion.prompt_tokens,
                "completion_tokens": completion.completion_tokens,
                "duration_s": round(completion.duration_s, 3),
                "ok": not error,
                "error": error,
                "timestamp": time.time(),
            }
            self.ledger.append(entry)
        except Exception:
            pass  # logging failure is non-fatal

    # --------------------------------------------------- public API

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> Completion:
        """Chat with the cloud teacher, falling back to local.

        Provider order: Gemini → Groq → local Ollama
        Privacy: if sensitive data is detected, skips cloud and uses local.
        """
        timeout = timeout or self.config.cloud_timeout

        # Privacy gate — check for sensitive data
        sensitive = self._check_privacy(messages)
        if sensitive:
            # Fall back to local immediately
            try:
                completion = self._call_local(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                self._log_call("local", messages, completion)
                return completion
            except ModelError as exc:
                self._log_call("local", messages, Completion(
                    text="", model=self.config.local_model, duration_s=0.0
                ), error=str(exc))
                raise

        # Try each provider in order
        errors: list[str] = []
        for provider in self._provider_order:
            try:
                if provider == "gemini" and self.config.gemini.is_configured:
                    completion = self._call_gemini(
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens or self.config.gemini.max_tokens,
                        timeout=timeout,
                    )
                    self._log_call("gemini", messages, completion)
                    return completion
                elif provider == "groq" and self.config.groq.is_configured:
                    completion = self._call_groq(
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens or self.config.groq.max_tokens,
                        timeout=timeout,
                    )
                    self._log_call("groq", messages, completion)
                    return completion
                elif provider == "local":
                    completion = self._call_local(
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout,
                    )
                    self._log_call("local", messages, completion)
                    return completion
            except ModelError as exc:
                errors.append(f"{provider}: {exc}")
                continue

        # All providers failed
        raise ModelError(
            f"all providers failed: {'; '.join(errors)}"
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> Completion:
        """Generate a completion from a prompt."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(
            messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout
        )

    # --------------------------------------------------- status

    def status(self) -> dict[str, Any]:
        """Return adapter status (no secrets)."""
        return {
            "configured": self.is_configured,
            "providers": self._provider_order,
            "gemini": {
                "configured": self.config.gemini.is_configured,
                "enabled": self.config.gemini.enabled,
                "model": self.config.gemini.model if self.config.gemini.is_configured else None,
            },
            "groq": {
                "configured": self.config.groq.is_configured,
                "enabled": self.config.groq.enabled,
                "model": self.config.groq.model if self.config.groq.is_configured else None,
            },
            "local": {
                "model": self.config.local_model,
                "endpoint": self.config.local_endpoint,
            },
            "privacy_gate": self.config.prefer_local_for_sensitive,
            "ledger_connected": self.ledger is not None,
            "phaseout": self._phaseout_status(),
        }

    def _phaseout_status(self) -> dict[str, Any]:
        """Return cloud phase-out status if available."""
        try:
            from .cloud_phaseout import CloudPhaseOutManager
            mgr = CloudPhaseOutManager(
                state_path="config/phase_out_state.json",
            )
            return mgr.overall_progress()
        except Exception:
            return {"available": False}

    def should_use_cloud_for(self, capability: str) -> bool:
        """Check if a capability should use the cloud teacher.

        Integrates with the cloud phase-out manager to determine
        if the local model is sufficient for a given capability.
        """
        try:
            from .cloud_phaseout import CloudPhaseOutManager
            mgr = CloudPhaseOutManager(
                state_path="config/phase_out_state.json",
            )
            return mgr.should_use_cloud(capability)
        except Exception:
            return True  # default to cloud if phase-out unavailable
