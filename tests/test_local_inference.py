"""Tests for the local inference engine backends."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.local_inference import (
    InferenceConfig, LlamaCppSubprocessBackend, LlamaCppCtypesBackend,
    PurePythonBackend, OllamaBackend, LocalInferenceEngine,
    BACKEND_LLAMA_SUBPROCESS, BACKEND_LLAMA_CTYPES,
    BACKEND_PURE_PYTHON, BACKEND_OLLAMA,
)


class TestInferenceConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = InferenceConfig()
        self.assertEqual(cfg.backend, "")
        self.assertEqual(cfg.context_size, 4096)
        self.assertEqual(cfg.temperature, 0.2)

    def test_from_env(self):
        with patch.dict("os.environ", {
            "ANUBIS_INFERENCE_BACKEND": "pure_python",
            "ANUBIS_MODEL_PATH": "/tmp/model.gguf",
            "ANUBIS_THREADS": "8",
        }):
            cfg = InferenceConfig.from_env()
            self.assertEqual(cfg.backend, "pure_python")
            self.assertEqual(cfg.model_path, "/tmp/model.gguf")
            self.assertEqual(cfg.n_threads, 8)


class TestLlamaCppCtypesBackend(unittest.TestCase):
    def setUp(self):
        self.config = InferenceConfig(model_path="/fake/model.gguf")

    def test_find_library_empty(self):
        backend = LlamaCppCtypesBackend(self.config)
        # On a clean system, no library should be found
        result = backend._find_library()
        # Could be empty or a path if llama.cpp is installed
        self.assertIsInstance(result, str)

    def test_is_available_no_model(self):
        config = InferenceConfig(model_path="")
        backend = LlamaCppCtypesBackend(config)
        self.assertFalse(backend.is_available())

    def test_is_available_no_binary(self):
        config = InferenceConfig(
            model_path="/fake/model.gguf",
            llama_cpp_path="/nonexistent/path",
            libllama_path="/nonexistent/lib.so",
        )
        backend = LlamaCppCtypesBackend(config)
        self.assertFalse(backend.is_available())

    def test_status(self):
        backend = LlamaCppCtypesBackend(self.config)
        status = backend.status()
        self.assertEqual(status["backend"], BACKEND_LLAMA_CTYPES)
        self.assertIn("available", status)
        self.assertIn("model", status)

    def test_generate_without_server(self):
        backend = LlamaCppCtypesBackend(self.config)
        # Should return an error completion, not crash
        with patch.object(backend, "_ensure_server", return_value=False):
            result = backend.generate("Hello")
            self.assertIn("failed", result.text.lower())

    def test_stop_when_not_running(self):
        backend = LlamaCppCtypesBackend(self.config)
        # Should not crash when nothing is running
        backend.stop()


class TestPurePythonBackend(unittest.TestCase):
    def setUp(self):
        self.config = InferenceConfig(model_path="")

    def test_is_available_no_model(self):
        backend = PurePythonBackend(self.config)
        self.assertFalse(backend.is_available())

    def test_status_no_model(self):
        backend = PurePythonBackend(self.config)
        status = backend.status()
        self.assertEqual(status["backend"], BACKEND_PURE_PYTHON)
        self.assertFalse(status["available"])

    def test_generate_greeting(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Hello there")
        self.assertIn("ANUBIS", result.text)
        self.assertEqual(result.model, "pure_python:template")

    def test_generate_identity(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Who are you?")
        self.assertIn("ANUBIS", result.text)
        self.assertIn("pure python", result.text.lower())

    def test_generate_capabilities(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("What can you do?")
        self.assertIn("knowledge", result.text.lower())

    def test_generate_math(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("What is 5 + 3?")
        self.assertIn("8", result.text)

    def test_generate_math_subtraction(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("What is 10 - 4?")
        self.assertIn("6", result.text)

    def test_generate_math_multiplication(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("What is 7 * 6?")
        self.assertIn("42", result.text)

    def test_generate_math_division(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("What is 20 / 5?")
        self.assertIn("4", result.text)

    def test_generate_code_request(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Write code for a web server")
        self.assertIn("code", result.text.lower())

    def test_generate_default(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Tell me about quantum physics and the nature of reality")
        self.assertIn("pure Python", result.text)
        self.assertIn("backend", result.text.lower())

    def test_generate_with_system(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Hello", system="You are a helpful assistant")
        self.assertTrue(len(result.text) > 0)

    def test_generate_has_duration(self):
        backend = PurePythonBackend(self.config)
        result = backend.generate("Hello")
        self.assertGreaterEqual(result.duration_s, 0.0)


class TestLocalInferenceEngine(unittest.TestCase):
    def test_init_auto_detect(self):
        engine = LocalInferenceEngine()
        # Should not crash
        status = engine.status()
        self.assertIn("active_backend", status)

    def test_is_self_hosted(self):
        engine = LocalInferenceEngine()
        # is_self_hosted depends on which backend is active
        self.assertIsInstance(engine.is_self_hosted, bool)

    def test_generate_falls_back_gracefully(self):
        engine = LocalInferenceEngine()
        # Should return something even if no backend is available
        result = engine.generate("Hello")
        self.assertTrue(len(result.text) > 0)

    def test_chat_with_messages(self):
        engine = LocalInferenceEngine()
        messages = [{"role": "user", "content": "Hello"}]
        result = engine.chat(messages)
        self.assertTrue(len(result.text) > 0)

    def test_status_has_backends(self):
        engine = LocalInferenceEngine()
        status = engine.status()
        self.assertIn("backends", status)


if __name__ == "__main__":
    unittest.main()
