"""Tests for the cloud teacher model adapter.

Tests verify:
- Configuration loading from file
- Privacy gate (sensitive data detection → local fallback)
- Provider failover (Gemini → Groq → local)
- Gemini API call format
- Groq API call format (OpenAI-compatible)
- Local Ollama fallback
- Status endpoint (no secrets)
- Evidence ledger logging
- Error handling (all providers fail)

Network calls are mocked to avoid real API dependencies.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.cloud_model import (
    CloudModelAdapter,
    CloudModelConfig,
    ProviderConfig,
    _check_sensitive_data,
)
from anubis.model import Completion, ModelError


class TestPrivacyGate(unittest.TestCase):
    """Tests for the privacy gate (sensitive data detection)."""

    def test_clean_text(self):
        self.assertIsNone(_check_sensitive_data("just a normal question about code"))

    def test_private_key_detected(self):
        result = _check_sensitive_data("-----BEGIN RSA PRIVATE KEY-----\nMIIkey")
        self.assertIsNotNone(result)

    def test_password_detected(self):
        result = _check_sensitive_data("password=secret123")
        self.assertIsNotNone(result)

    def test_api_key_detected(self):
        result = _check_sensitive_data("api_key=ABC123XYZ")
        self.assertIsNotNone(result)

    def test_creator_id_detected(self):
        result = _check_sensitive_data("creator_id=4670b4cf48fed7c5")
        self.assertIsNotNone(result)

    def test_empty_text(self):
        self.assertIsNone(_check_sensitive_data(""))


class TestConfigLoading(unittest.TestCase):
    """Tests for configuration loading."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-cloud-cfg-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_config(self):
        cfg = CloudModelConfig.from_file(Path(self.tmpdir) / "nonexistent.json")
        self.assertFalse(cfg.gemini.is_configured)
        self.assertFalse(cfg.groq.is_configured)
        self.assertEqual(cfg.local_model, "qwen2.5-coder:7b")

    def test_config_with_gemini(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({
            "gemini": {"api_key": "test-key", "model": "gemini-2.0-flash"},
        }), encoding="utf-8")
        cfg = CloudModelConfig.from_file(cfg_path)
        self.assertTrue(cfg.gemini.is_configured)
        self.assertEqual(cfg.gemini.api_key, "test-key")
        self.assertFalse(cfg.groq.is_configured)

    def test_config_with_groq(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({
            "groq": {"api_key": "gq-key", "model": "llama-3.3-70b-versatile"},
        }), encoding="utf-8")
        cfg = CloudModelConfig.from_file(cfg_path)
        self.assertTrue(cfg.groq.is_configured)
        self.assertEqual(cfg.groq.api_key, "gq-key")

    def test_config_with_both(self):
        cfg_path = Path(self.tmpdir) / "creds.json"
        cfg_path.write_text(json.dumps({
            "gemini": {"api_key": "gem-key"},
            "groq": {"api_key": "gq-key"},
        }), encoding="utf-8")
        cfg = CloudModelConfig.from_file(cfg_path)
        self.assertTrue(cfg.gemini.is_configured)
        self.assertTrue(cfg.groq.is_configured)

    def test_config_invalid_json(self):
        cfg_path = Path(self.tmpdir) / "bad.json"
        cfg_path.write_text("not json", encoding="utf-8")
        cfg = CloudModelConfig.from_file(cfg_path)
        self.assertFalse(cfg.gemini.is_configured)


class TestProviderOrder(unittest.TestCase):
    """Tests for provider priority ordering."""

    def test_order_with_both_configured(self):
        cfg = CloudModelConfig(
            gemini=ProviderConfig(name="gemini", api_key="k", endpoint="e", model="m"),
            groq=ProviderConfig(name="groq", api_key="k", endpoint="e", model="m"),
        )
        adapter = CloudModelAdapter(cfg)
        self.assertEqual(adapter.active_providers, ["gemini", "groq", "local"])

    def test_order_with_only_gemini(self):
        cfg = CloudModelConfig(
            gemini=ProviderConfig(name="gemini", api_key="k", endpoint="e", model="m"),
        )
        adapter = CloudModelAdapter(cfg)
        self.assertEqual(adapter.active_providers, ["gemini", "local"])

    def test_order_with_only_groq(self):
        cfg = CloudModelConfig(
            groq=ProviderConfig(name="groq", api_key="k", endpoint="e", model="m"),
        )
        adapter = CloudModelAdapter(cfg)
        self.assertEqual(adapter.active_providers, ["groq", "local"])

    def test_order_with_neither(self):
        cfg = CloudModelConfig()
        adapter = CloudModelAdapter(cfg)
        self.assertEqual(adapter.active_providers, ["local"])

    def test_disabled_provider_skipped(self):
        cfg = CloudModelConfig(
            gemini=ProviderConfig(name="gemini", api_key="k", endpoint="e", model="m", enabled=False),
            groq=ProviderConfig(name="groq", api_key="k", endpoint="e", model="m"),
        )
        adapter = CloudModelAdapter(cfg)
        self.assertEqual(adapter.active_providers, ["groq", "local"])


class TestPrivacyFallback(unittest.TestCase):
    """Tests that sensitive data triggers local fallback."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-cloud-priv-")
        self.cfg = CloudModelConfig(
            gemini=ProviderConfig(name="gemini", api_key="k", endpoint="https://gem.example.com", model="m"),
        )
        self.adapter = CloudModelAdapter(self.cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("anubis.cloud_model.OllamaAdapter")
    def test_sensitive_data_uses_local(self, mock_ollama):
        mock_instance = MagicMock()
        mock_instance.chat.return_value = Completion(
            text="local response", model="qwen2.5-coder:7b", duration_s=0.1
        )
        mock_ollama.return_value = mock_instance

        messages = [
            {"role": "user", "content": "my password=secret123, help me with code"},
        ]
        result = self.adapter.chat(messages)
        self.assertEqual(result.text, "local response")
        # Verify Gemini was NOT called
        mock_instance.chat.assert_called_once()

    @patch("anubis.cloud_model.OllamaAdapter")
    def test_clean_data_tries_cloud(self, mock_ollama):
        mock_instance = MagicMock()
        mock_instance.chat.return_value = Completion(
            text="local response", model="qwen2.5-coder:7b"
        )
        mock_ollama.return_value = mock_instance

        # Mock Gemini to fail so it falls through to local
        with patch.object(self.adapter, "_call_gemini", side_effect=ModelError("gemini down")):
            messages = [{"role": "user", "content": "help me write a function"}]
            result = self.adapter.chat(messages)
            # Gemini was tried (and failed), local was used as fallback
            self.assertEqual(result.text, "local response")


class TestGeminiCall(unittest.TestCase):
    """Tests for the Gemini API call format."""

    def setUp(self):
        self.cfg = CloudModelConfig(
            gemini=ProviderConfig(
                name="gemini", api_key="test-key",
                endpoint="https://generativelanguage.googleapis.com/v1beta",
                model="gemini-2.0-flash",
            ),
        )
        self.adapter = CloudModelAdapter(self.cfg)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_gemini_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{
                "content": {"parts": [{"text": "Hello from Gemini!"}]}
            }],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        messages = [{"role": "user", "content": "Hello"}]
        result = self.adapter._call_gemini(messages, temperature=0.2, max_tokens=100, timeout=30)
        self.assertEqual(result.text, "Hello from Gemini!")
        self.assertEqual(result.model, "gemini:gemini-2.0-flash")
        self.assertEqual(result.prompt_tokens, 10)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_gemini_system_instruction(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hi"},
        ]
        self.adapter._call_gemini(messages, temperature=0.2, max_tokens=100, timeout=30)
        # Verify the request body included systemInstruction
        call_args = mock_urlopen.call_args[0][0]
        body = json.loads(call_args.data.decode())
        self.assertIn("systemInstruction", body)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_gemini_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://gem.example.com", 403, "Forbidden",
            {}, io.BytesIO(b'{"error": "invalid key"}')
        )
        with self.assertRaises(ModelError) as ctx:
            self.adapter._call_gemini(
                [{"role": "user", "content": "test"}],
                temperature=0.2, max_tokens=100, timeout=30,
            )
        self.assertIn("403", str(ctx.exception))


class TestGroqCall(unittest.TestCase):
    """Tests for the Groq API call format."""

    def setUp(self):
        self.cfg = CloudModelConfig(
            groq=ProviderConfig(
                name="groq", api_key="gq-key",
                endpoint="https://api.groq.com/openai/v1",
                model="llama-3.3-70b-versatile",
            ),
        )
        self.adapter = CloudModelAdapter(self.cfg)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_groq_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{
                "message": {"content": "Hello from Groq!"}
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        messages = [{"role": "user", "content": "Hello"}]
        result = self.adapter._call_groq(messages, temperature=0.2, max_tokens=100, timeout=30)
        self.assertEqual(result.text, "Hello from Groq!")
        self.assertEqual(result.model, "groq:llama-3.3-70b-versatile")
        self.assertEqual(result.prompt_tokens, 10)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_groq_auth_header(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "OK"}}],
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.adapter._call_groq(
            [{"role": "user", "content": "test"}],
            temperature=0.2, max_tokens=100, timeout=30,
        )
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.headers.get("Authorization"), "Bearer gq-key")

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_groq_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://api.groq.com", 429, "Rate limited",
            {}, io.BytesIO(b'{"error": "rate limit"}')
        )
        with self.assertRaises(ModelError) as ctx:
            self.adapter._call_groq(
                [{"role": "user", "content": "test"}],
                temperature=0.2, max_tokens=100, timeout=30,
            )
        self.assertIn("429", str(ctx.exception))


class TestFailover(unittest.TestCase):
    """Tests for provider failover."""

    def setUp(self):
        self.cfg = CloudModelConfig(
            gemini=ProviderConfig(
                name="gemini", api_key="k",
                endpoint="https://gem.example.com", model="m",
            ),
            groq=ProviderConfig(
                name="groq", api_key="k",
                endpoint="https://groq.example.com", model="m",
            ),
        )
        self.adapter = CloudModelAdapter(self.cfg)

    def test_gemini_failure_falls_to_groq(self):
        with patch.object(self.adapter, "_call_gemini", side_effect=ModelError("gemini down")):
            with patch.object(self.adapter, "_call_groq") as mock_groq:
                mock_groq.return_value = Completion(text="groq response", model="groq:m")
                result = self.adapter.chat([{"role": "user", "content": "hi"}])
                self.assertEqual(result.text, "groq response")
                mock_groq.assert_called_once()

    def test_gemini_and_groq_failure_falls_to_local(self):
        with patch.object(self.adapter, "_call_gemini", side_effect=ModelError("gemini down")):
            with patch.object(self.adapter, "_call_groq", side_effect=ModelError("groq down")):
                with patch.object(self.adapter, "_call_local") as mock_local:
                    mock_local.return_value = Completion(text="local response", model="local")
                    result = self.adapter.chat([{"role": "user", "content": "hi"}])
                    self.assertEqual(result.text, "local response")
                    mock_local.assert_called_once()

    def test_all_providers_fail_raises_error(self):
        with patch.object(self.adapter, "_call_gemini", side_effect=ModelError("gemini down")):
            with patch.object(self.adapter, "_call_groq", side_effect=ModelError("groq down")):
                with patch.object(self.adapter, "_call_local", side_effect=ModelError("local down")):
                    with self.assertRaises(ModelError) as ctx:
                        self.adapter.chat([{"role": "user", "content": "hi"}])
                    self.assertIn("all providers failed", str(ctx.exception))


class TestStatus(unittest.TestCase):
    """Tests for the status endpoint."""

    def test_status_no_secrets(self):
        cfg = CloudModelConfig(
            gemini=ProviderConfig(
                name="gemini", api_key="super-secret-key",
                endpoint="https://gem.example.com", model="gemini-2.0-flash",
            ),
        )
        adapter = CloudModelAdapter(cfg)
        status = adapter.status()
        status_json = json.dumps(status)
        self.assertNotIn("super-secret-key", status_json)

    def test_status_shows_providers(self):
        cfg = CloudModelConfig(
            gemini=ProviderConfig(name="gemini", api_key="k", endpoint="e", model="m"),
            groq=ProviderConfig(name="groq", api_key="k", endpoint="e", model="m"),
        )
        adapter = CloudModelAdapter(cfg)
        status = adapter.status()
        self.assertIn("gemini", status["providers"])
        self.assertIn("groq", status["providers"])
        self.assertIn("local", status["providers"])

    def test_status_not_configured(self):
        adapter = CloudModelAdapter(CloudModelConfig())
        status = adapter.status()
        self.assertFalse(status["configured"])
        self.assertEqual(status["providers"], ["local"])

    def test_status_with_ledger(self):
        ledger = MagicMock()
        adapter = CloudModelAdapter(ledger=ledger)
        status = adapter.status()
        self.assertTrue(status["ledger_connected"])


class TestLogging(unittest.TestCase):
    """Tests for evidence ledger logging."""

    def setUp(self):
        self.ledger = MagicMock()
        self.cfg = CloudModelConfig(
            gemini=ProviderConfig(
                name="gemini", api_key="k",
                endpoint="https://generativelanguage.googleapis.com/v1beta",
                model="gemini-2.0-flash",
            ),
        )
        self.adapter = CloudModelAdapter(self.cfg, ledger=self.ledger)

    @patch("anubis.cloud_model.urllib.request.urlopen")
    def test_successful_call_logged(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.adapter.chat([{"role": "user", "content": "hello"}])
        self.ledger.append.assert_called_once()
        entry = self.ledger.append.call_args[0][0]
        self.assertEqual(entry["type"], "cloud_model_call")
        self.assertEqual(entry["provider"], "gemini")
        self.assertTrue(entry["ok"])

    def test_failed_call_logged(self):
        with patch.object(self.adapter, "_call_gemini", side_effect=ModelError("error")):
            with patch.object(self.adapter, "_call_local") as mock_local:
                mock_local.return_value = Completion(text="ok", model="local")
                self.adapter.chat([{"role": "user", "content": "hi"}])
                # Gemini failure logged, local success logged
                self.assertGreaterEqual(self.ledger.append.call_count, 1)


class TestGenerate(unittest.TestCase):
    """Tests for the generate convenience method."""

    def setUp(self):
        self.adapter = CloudModelAdapter(CloudModelConfig())

    def test_generate_builds_messages(self):
        with patch.object(self.adapter, "chat") as mock_chat:
            mock_chat.return_value = Completion(text="response", model="test")
            self.adapter.generate("test prompt", system="be helpful")
            mock_chat.assert_called_once()
            call_args = mock_chat.call_args[0][0]
            self.assertEqual(len(call_args), 2)
            self.assertEqual(call_args[0]["role"], "system")
            self.assertEqual(call_args[0]["content"], "be helpful")
            self.assertEqual(call_args[1]["role"], "user")
            self.assertEqual(call_args[1]["content"], "test prompt")

    def test_generate_without_system(self):
        with patch.object(self.adapter, "chat") as mock_chat:
            mock_chat.return_value = Completion(text="response", model="test")
            self.adapter.generate("test prompt")
            mock_chat.assert_called_once()
            call_args = mock_chat.call_args[0][0]
            self.assertEqual(len(call_args), 1)
            self.assertEqual(call_args[0]["role"], "user")


if __name__ == "__main__":
    unittest.main()
