"""Swappable local-inference adapter.

Book 09 requires ANUBIS to remain "fully functional locally" and forbids
private user data from reaching external inference. This module therefore only
ever talks to a local endpoint; there is no cloud fallback path to accidentally
enable.

The adapter interface exists so the hardware upgrade (RTX 3060 6 GB ->
RTX 5060 Ti 16 GB) is a configuration change rather than a rewrite. Model
selection is data, not code: see MODELS below.

Dependency note: uses only the Python standard library. Book 13 requires
packages to be signed and provenance-tracked, and the constitutional kernel
flags `pip` as a permission-integrity hazard, so the core runtime deliberately
carries zero third-party dependencies.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

DEFAULT_ENDPOINT = os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434")


@dataclass(frozen=True)
class ModelSpec:
    """Capability declaration for a model.

    Recorded rather than assumed, because the self-development loop needs tool
    calling and must refuse to run on a model that cannot do it.
    """

    name: str
    params: str
    tools: bool
    thinking: bool
    vision: bool
    context: int
    min_vram_gb: float
    note: str = ""


# Verified against `ollama list` on this host.
MODELS: dict[str, ModelSpec] = {
    "qwen2.5-coder:7b": ModelSpec(
        "qwen2.5-coder:7b", "7B", tools=False, thinking=False, vision=False,
        context=32768, min_vram_gb=5.0,
        note="Code specialist. Fast (20 tok/s on 3060). No native tool calling "
             "but excellent at structured code generation. Primary for the "
             "self-development loop on 6 GB VRAM.",
    ),
    "llama3.1:8b": ModelSpec(
        "llama3.1:8b", "8B", tools=True, thinking=False, vision=False,
        context=131072, min_vram_gb=5.5,
        note="General purpose with reliable tool calling. Fallback when coder "
             "model struggles with non-code reasoning.",
    ),
    "qwen3:4b": ModelSpec(
        "qwen3:4b", "4B", tools=True, thinking=True, vision=False,
        context=262144, min_vram_gb=3.0,
        note="Fast path / fallback. Thinking model.",
    ),
    "qwen2.5-coder:14b": ModelSpec(
        "qwen2.5-coder:14b", "14B", tools=False, thinking=False, vision=False,
        context=32768, min_vram_gb=9.0,
        note="Stronger code specialist. Fits 16 GB VRAM. Post-upgrade target.",
    ),
    "qwen3.6:latest": ModelSpec(
        "qwen3.6:latest", "36B-MoE", tools=True, thinking=True, vision=True,
        context=262144, min_vram_gb=14.0,
        note="Post-upgrade target. MoE: activates a fraction of params per token.",
    ),
    "gemma3:4b": ModelSpec(
        "gemma3:4b", "4B", tools=False, thinking=False, vision=False,
        context=8192, min_vram_gb=3.0,
        note="No tool calling -- unusable for the self-development loop.",
    ),
}


class ModelError(Exception):
    pass


class CapabilityError(ModelError):
    """Raised when the selected model cannot do what the caller requires."""


@dataclass
class Completion:
    text: str
    thinking: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_s: float = 0.0

    @property
    def tokens_per_s(self) -> float:
        return self.completion_tokens / self.duration_s if self.duration_s else 0.0


class ModelAdapter(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Completion: ...

    @property
    def spec(self) -> ModelSpec: ...


class OllamaAdapter:
    """Local Ollama backend."""

    def __init__(
        self,
        model: str = "llama3.1:8b",
        endpoint: str = DEFAULT_ENDPOINT,
        *,
        require_tools: bool = False,
    ) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self._spec = MODELS.get(
            model,
            ModelSpec(model, "?", tools=False, thinking=False, vision=False,
                      context=8192, min_vram_gb=0.0, note="unregistered model"),
        )
        if require_tools and not self._spec.tools:
            raise CapabilityError(
                f"{model} does not support tool calling, which the "
                f"self-development loop requires. Use one of: "
                + ", ".join(n for n, s in MODELS.items() if s.tools)
            )

    @property
    def spec(self) -> ModelSpec:
        return self._spec

    # ------------------------------------------------------------- transport

    def _post(self, path: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise ModelError(f"ollama HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ModelError(
                f"cannot reach ollama at {self.endpoint}: {exc.reason}. "
                "Is the Ollama service running?"
            ) from exc
        except TimeoutError as exc:
            raise ModelError(f"ollama timed out after {timeout}s") from exc

    def _get(self, path: str, timeout: float = 10.0) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{self.endpoint}{path}", timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - surfaced as ModelError
            raise ModelError(f"ollama GET {path} failed: {exc}") from exc

    # ---------------------------------------------------------------- public

    def health(self) -> dict[str, Any]:
        """Confirm the endpoint is live and the model is present."""
        version = self._get("/api/version").get("version", "?")
        tags = self._get("/api/tags").get("models", [])
        available = [m["name"] for m in tags]
        return {
            "endpoint": self.endpoint,
            "version": version,
            "model": self.model,
            "model_present": self.model in available,
            "available": available,
        }

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Completion:
        if tools and not self._spec.tools:
            raise CapabilityError(f"{self.model} cannot use tools")

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if tools:
            body["tools"] = tools

        t0 = time.monotonic()
        raw = self._post("/api/chat", body, timeout)
        elapsed = time.monotonic() - t0

        msg = raw.get("message", {}) or {}
        return Completion(
            text=(msg.get("content") or "").strip(),
            thinking=(msg.get("thinking") or "").strip(),
            tool_calls=msg.get("tool_calls") or [],
            model=raw.get("model", self.model),
            prompt_tokens=raw.get("prompt_eval_count", 0) or 0,
            completion_tokens=raw.get("eval_count", 0) or 0,
            duration_s=elapsed,
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Completion:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(
            messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout
        )


# ------------------------------------------------------------------ selection

def select_model(vram_gb: float | None = None, *, need_tools: bool = False) -> str:
    """Pick the strongest registered model that fits the available VRAM.

    Called at startup so the same code picks qwen2.5-coder:7b on the 3060 today
    and qwen2.5-coder:14b or qwen3.6 on the 5060 Ti after the upgrade, with no edit.

    The self-development loop uses structured prompts, not Ollama's tool calling
    API, so need_tools defaults to False. Tool calling is only required for
    features that use the chat API with tools (e.g. DEMON conversational interface).
    """
    if vram_gb is None:
        vram_gb = detect_vram_gb() or 6.0
    candidates = [
        s for s in MODELS.values()
        if s.min_vram_gb <= vram_gb and (s.tools or not need_tools)
    ]
    if not candidates:
        raise CapabilityError(
            f"no registered model fits {vram_gb:.1f} GB VRAM with tools={need_tools}"
        )
    # Prefer the largest that fits; MoE counts by its VRAM floor.
    return max(candidates, key=lambda s: s.min_vram_gb).name


def detect_vram_gb() -> float | None:
    """Best-effort VRAM detection via nvidia-smi.

    Returns None when unavailable rather than guessing, so callers can decide.
    Note: uses subprocess, which the constitutional kernel flags as a hazard in
    *generated* code. That rule governs untrusted generated artifacts; this is
    reviewed first-party startup code, and it is not executed in a sandbox.
    """
    import shutil
    import subprocess

    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip().splitlines()
        return max(float(v.strip()) for v in out if v.strip()) / 1024.0
    except Exception:  # noqa: BLE001 - detection is advisory only
        return None


def build_adapter(
    model: str | None = None, *, require_tools: bool = False
) -> OllamaAdapter:
    """Factory used by the rest of the system.

    Honours ANUBIS_MODEL when set, otherwise auto-selects for the detected GPU.
    """
    chosen = model or os.environ.get("ANUBIS_MODEL") or select_model(
        need_tools=require_tools
    )
    return OllamaAdapter(chosen, require_tools=require_tools)
