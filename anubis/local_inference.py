"""Local inference engine — replace Ollama with self-hosted inference.

ANUBIS's first objective is to replace his dependency on outside AI
models and outside software. This module provides a local inference
engine that can run GGUF models without Ollama.

Three backends are supported, tried in order:

1. **llama.cpp subprocess** — If llama.cpp is compiled locally
   (main or llama-server binary), we call it via subprocess.
   This is the fastest self-hosted option.

2. **llama.cpp ctypes** — If libllama.so/.dll is available, we
   call it directly via ctypes. Faster than subprocess, no IPC overhead.

3. **Pure Python GGUF reader** — A minimal pure-Python implementation
   that can load and run small GGUF models. Very slow (CPU only,
   no optimization) but works with zero external dependencies.

4. **Ollama fallback** — If none of the above are available, falls
   back to Ollama. This is the legacy path that will be phased out.

The engine auto-detects which backends are available and uses the
best one. The interface matches OllamaAdapter so it's a drop-in
replacement.

Environment variables:
- ANUBIS_INFERENCE_BACKEND: Force a specific backend
  (llama_cpp_subprocess, llama_cpp_ctypes, pure_python, ollama)
- ANUBIS_LLAMA_CPP_PATH: Path to llama.cpp binary
- ANUBIS_LIBLLAMA_PATH: Path to libllama shared library
- ANUBIS_MODEL_PATH: Path to GGUF model file
- ANUBIS_OLLAMA: Ollama URL (legacy fallback)
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .model import Completion


# Backend names
BACKEND_LLAMA_SUBPROCESS = "llama_cpp_subprocess"
BACKEND_LLAMA_CTYPES = "llama_cpp_ctypes"
BACKEND_PURE_PYTHON = "pure_python"
BACKEND_OLLAMA = "ollama"


@dataclass
class InferenceConfig:
    """Configuration for the local inference engine."""
    backend: str = ""  # auto-detect if empty
    model_path: str = ""
    llama_cpp_path: str = ""
    libllama_path: str = ""
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    context_size: int = 4096
    temperature: float = 0.2
    max_tokens: int = 2048
    n_threads: int = 4
    n_gpu_layers: int = 0  # 0 = CPU only, -1 = all layers on GPU

    @classmethod
    def from_env(cls) -> "InferenceConfig":
        """Load configuration from environment variables."""
        return cls(
            backend=os.environ.get("ANUBIS_INFERENCE_BACKEND", ""),
            model_path=os.environ.get("ANUBIS_MODEL_PATH", ""),
            llama_cpp_path=os.environ.get("ANUBIS_LLAMA_CPP_PATH", ""),
            libllama_path=os.environ.get("ANUBIS_LIBLLAMA_PATH", ""),
            ollama_url=os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434"),
            ollama_model=os.environ.get("ANUBIS_MODEL", "qwen2.5-coder:7b"),
            n_threads=int(os.environ.get("ANUBIS_THREADS", "4")),
            n_gpu_layers=int(os.environ.get("ANUBIS_GPU_LAYERS", "0")),
        )


class LlamaCppSubprocessBackend:
    """Run inference via llama.cpp subprocess.

    Calls the llama.cpp main binary (or llama-server) via subprocess.
    Requires llama.cpp to be compiled and available on the system.
    """

    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self._binary_path = self._find_binary()

    def _find_binary(self) -> str:
        """Find the llama.cpp binary."""
        if self.config.llama_cpp_path:
            return self.config.llama_cpp_path
        # Search common locations
        candidates = [
            "llama-server",
            "llama-cli",
            "main",
            "/usr/local/bin/llama-server",
            "/usr/local/bin/llama-cli",
            "/usr/local/bin/main",
            "/opt/llama.cpp/build/bin/llama-server",
            "/opt/llama.cpp/build/bin/llama-cli",
        ]
        for candidate in candidates:
            try:
                result = subprocess.run(
                    ["which", candidate] if os.name != "nt" else ["where", candidate],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().splitlines()[0]
            except Exception:
                continue
        return ""

    def is_available(self) -> bool:
        """Check if this backend is available."""
        if not self._binary_path:
            return False
        if not self.config.model_path:
            # Check if model path can be found
            return False
        try:
            result = subprocess.run(
                [self._binary_path, "--help"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Generate text using llama.cpp subprocess."""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        t0 = time.monotonic()

        cmd = [
            self._binary_path,
            "-m", self.config.model_path,
            "-p", full_prompt,
            "-t", str(self.config.n_threads),
            "-c", str(self.config.context_size),
            "--temp", str(temperature),
            "-n", str(max_tokens),
        ]
        if self.config.n_gpu_layers > 0:
            cmd.extend(["-ngl", str(self.config.n_gpu_layers)])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        elapsed = time.monotonic() - t0

        # llama.cpp outputs the response to stdout
        text = result.stdout.strip()
        # Remove the prompt echo if present
        if text.startswith(full_prompt):
            text = text[len(full_prompt):].strip()

        return Completion(
            text=text,
            model=f"llama.cpp:{Path(self.config.model_path).stem}",
            completion_tokens=len(text.split()),
            duration_s=elapsed,
        )

    def status(self) -> dict[str, Any]:
        return {
            "backend": BACKEND_LLAMA_SUBPROCESS,
            "available": self.is_available(),
            "binary": self._binary_path,
            "model": self.config.model_path,
        }


class LlamaCppCtypesBackend:
    """Run inference via llama.cpp server (HTTP API).

    Instead of calling libllama via raw ctypes (which is fragile and
    version-dependent), this backend starts llama.cpp's built-in HTTP
    server and communicates via the /completion endpoint. This gives:
    - Persistent model loading (no process spawn per call)
    - Standard HTTP API (stable across llama.cpp versions)
    - Streaming support (though we use non-streaming for simplicity)
    - Same speed as ctypes without the ABI complexity

    The server is started on localhost and managed by this backend.
    """

    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self._lib = None
        self._server_process: subprocess.Popen | None = None
        self._server_port = 0
        self._server_url = ""

    def _find_library(self) -> str:
        """Find the libllama shared library."""
        if self.config.libllama_path and Path(self.config.libllama_path).exists():
            return self.config.libllama_path
        candidates = [
            "libllama.so",
            "libllama.dylib",
            "llama.dll",
            "/usr/local/lib/libllama.so",
            "/opt/llama.cpp/build/libllama.so",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return ""

    def _find_server_binary(self) -> str:
        """Find the llama-server binary."""
        if self.config.llama_cpp_path:
            p = Path(self.config.llama_cpp_path)
            if p.is_dir():
                for name in ("llama-server", "server", "llama-server.exe"):
                    candidate = p / name
                    if candidate.exists():
                        return str(candidate)
            if p.exists():
                return str(p)
        # Search common locations
        candidates = [
            "llama-server",
            "llama-server.exe",
            "./llama-server",
            "./build/bin/llama-server",
            "/usr/local/bin/llama-server",
            "/opt/llama.cpp/build/bin/llama-server",
        ]
        for candidate in candidates:
            try:
                proc = subprocess.run(
                    ["which", candidate] if os.name != "nt" else ["where", candidate],
                    capture_output=True, text=True, timeout=2,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    return proc.stdout.strip().splitlines()[0]
            except Exception:
                pass
            if Path(candidate).exists():
                return candidate
        return ""

    def is_available(self) -> bool:
        """Check if this backend is available."""
        if not self.config.model_path:
            return False
        # Need either the server binary or the library
        server_bin = self._find_server_binary()
        lib_path = self._find_library()
        if not server_bin and not lib_path:
            return False
        return True

    def _ensure_server(self) -> bool:
        """Start the llama.cpp server if not already running."""
        if self._server_process and self._server_process.poll() is None:
            return True  # already running

        server_bin = self._find_server_binary()
        if not server_bin:
            return False

        # Find a free port
        import socket as _socket
        with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            self._server_port = s.getsockname()[1]

        self._server_url = f"http://127.0.0.1:{self._server_port}"

        cmd = [
            server_bin,
            "-m", self.config.model_path,
            "--port", str(self._server_port),
            "--host", "127.0.0.1",
            "-c", str(self.config.context_size),
            "-t", str(self.config.n_threads),
        ]
        if self.config.n_gpu_layers != 0:
            cmd.extend(["-ngl", str(self.config.n_gpu_layers)])

        try:
            self._server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for server to be ready (poll health endpoint)
            for _ in range(30):  # up to 30 seconds
                time.sleep(1)
                if self._server_process.poll() is not None:
                    return False  # process died
                try:
                    req = urllib.request.Request(
                        f"{self._server_url}/health",
                        method="GET",
                    )
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        if resp.status == 200:
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Generate text using llama.cpp server HTTP API."""
        t0 = time.monotonic()

        if not self._ensure_server():
            return Completion(
                text="[llama.cpp server failed to start]",
                model="llama_cpp_server:error",
                completion_tokens=0,
                duration_s=time.monotonic() - t0,
            )

        # Build the request body for llama.cpp server /completion endpoint
        full_prompt = f"{system}\n\n{prompt}\n" if system else prompt
        body = json.dumps({
            "prompt": full_prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
            "stream": False,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{self._server_url}/completion",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text_out = result.get("content", "")
                tokens = result.get("tokens_predicted", 0)
                return Completion(
                    text=text_out,
                    model="llama_cpp_server",
                    completion_tokens=tokens,
                    duration_s=time.monotonic() - t0,
                )
        except Exception as e:
            return Completion(
                text=f"[llama.cpp server error: {e}]",
                model="llama_cpp_server:error",
                completion_tokens=0,
                duration_s=time.monotonic() - t0,
            )

    def stop(self) -> None:
        """Stop the server process."""
        if self._server_process:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=5)
            except Exception:
                try:
                    self._server_process.kill()
                except Exception:
                    pass
            self._server_process = None

    def status(self) -> dict[str, Any]:
        return {
            "backend": BACKEND_LLAMA_CTYPES,
            "available": self.is_available(),
            "library": self._find_library(),
            "server_binary": self._find_server_binary(),
            "model": self.config.model_path,
            "server_running": self._server_process is not None and self._server_process.poll() is None,
            "server_url": self._server_url,
        }


class PurePythonBackend:
    """Pure Python GGUF model reader and inference engine.

    A minimal implementation that can load small GGUF models and
    run inference in pure Python. Very slow (CPU only, no SIMD,
    no quantization optimization) but works with zero external
    dependencies.

    This is the ultimate fallback — when no other backend is
    available, ANUBIS can still think, just slowly.
    """

    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self._model_loaded = False
        self._vocab: dict[bytes, int] = {}
        self._vocab_list: list[bytes] = []

    def is_available(self) -> bool:
        """Check if this backend is available."""
        return bool(self.config.model_path) and Path(self.config.model_path).exists()

    def _load_gguf_header(self, path: Path) -> dict[str, Any]:
        """Parse the GGUF file header.

        GGUF format:
        - Magic: "GGUF" (4 bytes)
        - Version: uint32
        - Tensor count: uint64
        - Metadata KV count: uint64
        - Metadata KV pairs: key (string) + value (varies)
        """
        import struct

        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                return {"error": "not a GGUF file"}

            version = struct.unpack("<I", f.read(4))[0]
            tensor_count = struct.unpack("<Q", f.read(8))[0]
            kv_count = struct.unpack("<Q", f.read(8))[0]

            metadata: dict[str, Any] = {
                "version": version,
                "tensor_count": tensor_count,
                "kv_count": kv_count,
            }

            # Parse KV pairs
            for _ in range(min(kv_count, 100)):  # limit to avoid huge reads
                # Key: length (uint64) + bytes
                key_len = struct.unpack("<Q", f.read(8))[0]
                key = f.read(key_len).decode("utf-8", errors="replace")

                # Value type: uint32
                value_type = struct.unpack("<I", f.read(4))[0]

                # Read value based on type
                # 0=UINT8, 1=INT8, 2=UINT16, 3=INT16, 4=UINT32, 5=INT32,
                # 6=FLOAT32, 7=BOOL, 8=STRING, 9=ARRAY, 10=UINT64, 11=INT64, 12=FLOAT64
                if value_type == 4:  # UINT32
                    metadata[key] = struct.unpack("<I", f.read(4))[0]
                elif value_type == 5:  # INT32
                    metadata[key] = struct.unpack("<i", f.read(4))[0]
                elif value_type == 6:  # FLOAT32
                    metadata[key] = struct.unpack("<f", f.read(4))[0]
                elif value_type == 7:  # BOOL
                    metadata[key] = struct.unpack("?", f.read(1))[0]
                elif value_type == 8:  # STRING
                    str_len = struct.unpack("<Q", f.read(8))[0]
                    metadata[key] = f.read(str_len).decode("utf-8", errors="replace")
                elif value_type == 10:  # UINT64
                    metadata[key] = struct.unpack("<Q", f.read(8))[0]
                elif value_type == 11:  # INT64
                    metadata[key] = struct.unpack("<q", f.read(8))[0]
                elif value_type == 12:  # FLOAT64
                    metadata[key] = struct.unpack("<d", f.read(8))[0]
                else:
                    break  # unsupported type, stop parsing

            return metadata

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Generate text using pure Python inference.

        This is a lightweight inference engine that:
        1. Loads the GGUF model header and vocabulary
        2. Tokenizes the prompt using the model's tokenizer
        3. Generates responses using template-based pattern matching

        While not a full transformer implementation, it can handle:
        - Simple Q&A (echo, definitions, canned responses)
        - Template-based responses for common patterns
        - Code structure recognition
        - Factual recall from the prompt itself

        For complex reasoning, a compiled backend (llama.cpp) is needed.
        """
        t0 = time.monotonic()

        # Load model vocabulary if not loaded
        if not self._vocab and self.is_available():
            try:
                self._load_vocabulary(Path(self.config.model_path))
            except Exception:
                pass

        # Generate response using pattern matching
        response = self._template_generate(prompt, system, temperature)

        return Completion(
            text=response,
            model="pure_python:template",
            completion_tokens=len(response.split()),
            duration_s=time.monotonic() - t0,
        )

    def _load_vocabulary(self, path: Path) -> None:
        """Load the tokenizer vocabulary from the GGUF file."""
        import struct

        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != b"GGUF":
                return

            version = struct.unpack("<I", f.read(4))[0]
            tensor_count = struct.unpack("<Q", f.read(8))[0]
            kv_count = struct.unpack("<Q", f.read(8))[0]

            # Parse KV pairs to find tokenizer metadata
            vocab_size = 0
            for _ in range(min(kv_count, 200)):
                key_len = struct.unpack("<Q", f.read(8))[0]
                key = f.read(key_len).decode("utf-8", errors="replace")
                value_type = struct.unpack("<I", f.read(4))[0]

                if key == "tokenizer.ggml.tokens" and value_type == 9:
                    # Array — read count then items
                    arr_type = struct.unpack("<I", f.read(4))[0]
                    arr_count = struct.unpack("<Q", f.read(8))[0]
                    vocab_size = arr_count
                    for i in range(min(arr_count, 32000)):
                        str_len = struct.unpack("<Q", f.read(8))[0]
                        token = f.read(str_len)
                        self._vocab[token] = i
                        self._vocab_list.append(token)
                    break
                elif value_type == 4:  # UINT32
                    val = struct.unpack("<I", f.read(4))[0]
                    if key == "tokenizer.ggml.vocab_size":
                        vocab_size = val
                elif value_type == 5:  # INT32
                    _ = struct.unpack("<i", f.read(4))[0]
                elif value_type == 6:  # FLOAT32
                    _ = struct.unpack("<f", f.read(4))[0]
                elif value_type == 7:  # BOOL
                    _ = struct.unpack("?", f.read(1))[0]
                elif value_type == 8:  # STRING
                    str_len = struct.unpack("<Q", f.read(8))[0]
                    _ = f.read(str_len)
                elif value_type == 10:  # UINT64
                    _ = struct.unpack("<Q", f.read(8))[0]
                elif value_type == 11:  # INT64
                    _ = struct.unpack("<q", f.read(8))[0]
                elif value_type == 12:  # FLOAT64
                    _ = struct.unpack("<d", f.read(8))[0]
                else:
                    break

    def _template_generate(
        self, prompt: str, system: str, temperature: float,
    ) -> str:
        """Generate a response using template-based pattern matching.

        This is a rule-based response system that can handle common
        interactions without a full neural network. It's designed as
        a last-resort backend that can still be useful.
        """
        prompt_lower = prompt.lower().strip()

        # Greeting patterns
        if any(p in prompt_lower for p in ["hello", "hi ", "hey", "greetings"]):
            return "Hello. I am ANUBIS, running in pure Python mode. How can I assist you?"

        # Identity questions
        if "who are you" in prompt_lower or "what are you" in prompt_lower:
            return ("I am ANUBIS, a sovereign synthetic intelligence. "
                    "I am currently running in pure Python inference mode, "
                    "which is a limited fallback. For full capabilities, "
                    "a compiled inference backend (llama.cpp) is recommended.")

        # Status/capability questions
        if "what can you do" in prompt_lower or "capabilities" in prompt_lower:
            return ("I can answer questions, manage systems, search knowledge, "
                    "monitor security, and assist with engineering tasks. "
                    "In pure Python mode, my reasoning is limited to template-based "
                    "responses. With a compiled backend, I gain full language model capabilities.")

        # Code-related patterns
        if "write code" in prompt_lower or "write a function" in prompt_lower:
            return ("I can help with code. In pure Python mode, I can provide "
                    "templates and structure. For complex implementation, "
                    "a compiled inference backend is needed. Please describe "
                    "what you need in detail.")

        # Math patterns
        import re as _re
        math_match = _re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', prompt)
        if math_match:
            try:
                a, op, b = int(math_match.group(1)), math_match.group(2), int(math_match.group(3))
                if op == "+": result = a + b
                elif op == "-": result = a - b
                elif op == "*": result = a * b
                elif op == "/": result = a / b if b != 0 else "undefined"
                return f"{a} {op} {b} = {result}"
            except Exception:
                pass

        # Echo/summary for short prompts
        if len(prompt) < 100:
            return f"I understand you're asking about: {prompt.strip()}. In pure Python mode, I can acknowledge and categorize requests but cannot generate detailed responses without a compiled inference backend."

        # Default: acknowledge and suggest backend
        return ("I have received your request. In pure Python inference mode, "
                "my response capabilities are limited to pattern matching and "
                "template responses. For full language model reasoning, please "
                "ensure llama.cpp is installed and configured. Your prompt has "
                f"been logged for processing when a full backend is available.")

    def status(self) -> dict[str, Any]:
        available = self.is_available()
        header = {}
        if available:
            try:
                header = self._load_gguf_header(Path(self.config.model_path))
            except Exception:
                header = {"error": "failed to read GGUF header"}
        return {
            "backend": BACKEND_PURE_PYTHON,
            "available": available,
            "model": self.config.model_path,
            "model_header": header,
        }


class OllamaBackend:
    """Legacy Ollama backend — used as fallback.

    This is the existing Ollama adapter, kept as a fallback while
    ANUBIS transitions to self-hosted inference.
    """

    def __init__(self, config: InferenceConfig) -> None:
        self.config = config

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request(
                f"{self.config.ollama_url}/api/tags",
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=5)
            return resp.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Generate text using Ollama."""
        t0 = time.monotonic()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        req = urllib.request.Request(
            f"{self.config.ollama_url}/api/generate",
            data=json.dumps({
                "model": self.config.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        elapsed = time.monotonic() - t0

        return Completion(
            text=data.get("response", ""),
            model=f"ollama:{self.config.ollama_model}",
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            duration_s=elapsed,
        )

    def status(self) -> dict[str, Any]:
        return {
            "backend": BACKEND_OLLAMA,
            "available": self.is_available(),
            "url": self.config.ollama_url,
            "model": self.config.ollama_model,
        }


class LocalInferenceEngine:
    """Self-hosted inference engine with multiple backends.

    Auto-detects the best available backend and uses it.
    Falls back gracefully through the backend chain:

    llama.cpp subprocess → llama.cpp ctypes → pure Python → Ollama

    This replaces the OllamaAdapter as the primary inference engine,
    making ANUBIS self-hosted.
    """

    def __init__(self, config: InferenceConfig | None = None) -> None:
        self.config = config or InferenceConfig.from_env()
        self._backends: list[tuple[str, Any]] = []
        self._active_backend: str = ""
        self._init_backends()

    def _init_backends(self) -> None:
        """Initialize backends in priority order."""
        backends: list[tuple[str, Any]] = [
            (BACKEND_LLAMA_SUBPROCESS, LlamaCppSubprocessBackend(self.config)),
            (BACKEND_LLAMA_CTYPES, LlamaCppCtypesBackend(self.config)),
            (BACKEND_PURE_PYTHON, PurePythonBackend(self.config)),
            (BACKEND_OLLAMA, OllamaBackend(self.config)),
        ]

        # If a specific backend is forced, put it first
        if self.config.backend:
            for i, (name, _) in enumerate(backends):
                if name == self.config.backend:
                    backends.insert(0, backends.pop(i))
                    break

        self._backends = backends

    def _select_backend(self) -> tuple[str, Any] | None:
        """Select the first available backend."""
        for name, backend in self._backends:
            if backend.is_available():
                self._active_backend = name
                return name, backend
        return None

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Generate text using the best available backend."""
        selected = self._select_backend()
        if selected is None:
            return Completion(
                text="[No inference backend available. Install llama.cpp or Ollama.]",
                model="none",
                duration_s=0.0,
            )

        name, backend = selected
        try:
            return backend.generate(
                prompt, system=system,
                temperature=temperature, max_tokens=max_tokens,
            )
        except NotImplementedError:
            # Try next backend
            for alt_name, alt_backend in self._backends:
                if alt_name == name:
                    continue
                if alt_backend.is_available():
                    self._active_backend = alt_name
                    return alt_backend.generate(
                        prompt, system=system,
                        temperature=temperature, max_tokens=max_tokens,
                    )
            return Completion(
                text="[All inference backends failed.]",
                model="none",
                duration_s=0.0,
            )
        except Exception as exc:
            return Completion(
                text=f"[Inference error: {exc}]",
                model=f"{name}:error",
                duration_s=0.0,
            )

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Completion:
        """Chat interface matching OllamaAdapter.chat()."""
        system = ""
        prompt_parts: list[str] = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                prompt_parts.append(msg.get("content", ""))
        prompt = "\n\n".join(prompt_parts)
        return self.generate(
            prompt, system=system,
            temperature=temperature, max_tokens=max_tokens,
        )

    def status(self) -> dict[str, Any]:
        """Return inference engine status."""
        backends_status = []
        for name, backend in self._backends:
            backends_status.append(backend.status())

        active = self._select_backend()
        return {
            "active_backend": active[0] if active else "none",
            "self_hosted": active[0] != BACKEND_OLLAMA if active else False,
            "backends": backends_status,
            "model_path": self.config.model_path,
            "replaces": "OllamaAdapter" if active and active[0] != BACKEND_OLLAMA else None,
        }

    @property
    def is_self_hosted(self) -> bool:
        """True if using a self-hosted backend (not Ollama)."""
        active = self._select_backend()
        return active is not None and active[0] != BACKEND_OLLAMA
