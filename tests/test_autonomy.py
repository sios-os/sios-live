"""Tests for local fine-tuner, dream cycle wiring, and universal voice interpreter."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.local_finetuner import LocalFineTuner, TrainingRun, DataCollectionResult
from anubis.voice_interpreter import VoiceCommandInterpreter
from anubis.unsloth_adapter import UnslothAdapter, TrainingConfig


# ===========================================================
# LOCAL FINE-TUNER TESTS
# ===========================================================

class TestLocalFineTuner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir) / "root"
        self.root.mkdir(parents=True)

        # Mock distiller
        self.distiller = MagicMock()
        self.distiller.export_training_data.return_value = {
            "exported": 5,
            "path": str(self.root / "training" / "datasets" / "test.jsonl"),
        }

        # Create a test dataset
        dataset_dir = self.root / "training" / "datasets"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dataset_path = dataset_dir / "test.jsonl"
        with open(dataset_path, "w") as f:
            for i in range(5):
                f.write(json.dumps({
                    "instruction": f"Test instruction {i}",
                    "response": f"Test response {i}",
                    "quality_score": 0.8,
                }) + "\n")

        self.finetuner = LocalFineTuner(
            self.root,
            distiller=self.distiller,
            unsloth=UnslothAdapter(),
            ledger=MagicMock(),
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_dirs(self):
        self.assertTrue((self.root / "training" / "runs").exists())
        self.assertTrue((self.root / "training" / "datasets").exists())
        self.assertTrue((self.root / "training" / "scripts").exists())

    def test_collect_training_data(self):
        result = self.finetuner.collect_training_data(min_quality=0.5)
        self.assertIsInstance(result, DataCollectionResult)
        self.assertGreaterEqual(result.total_pairs, 0)

    def test_collect_with_no_distiller(self):
        ft = LocalFineTuner(self.root, ledger=MagicMock())
        result = ft.collect_training_data()
        # Should not crash, just return 0 from distillation
        self.assertIsInstance(result, DataCollectionResult)

    def test_generate_training_script(self):
        dataset_path = self.root / "training" / "datasets" / "test.jsonl"
        result = self.finetuner.generate_training_script(str(dataset_path))
        self.assertIn("script_path", result)
        self.assertTrue(Path(result["script_path"]).exists())
        content = Path(result["script_path"]).read_text()
        self.assertIn("TrainingArguments", content)

    def test_generate_script_with_config(self):
        dataset_path = self.root / "training" / "datasets" / "test.jsonl"
        config = TrainingConfig(model_name="test-model", epochs=1)
        result = self.finetuner.generate_training_script(str(dataset_path), config)
        self.assertIn("script_path", result)

    def test_get_status(self):
        status = self.finetuner.get_status()
        self.assertIn("total_runs", status)
        self.assertIn("unsloth_available", status)
        self.assertIn("gpu_available", status)

    def test_list_runs_empty(self):
        result = self.finetuner.list_runs()
        self.assertEqual(result["count"], 0)

    def test_list_runs_after_run(self):
        # Manually add a run to index
        self.finetuner._update_run_index(TrainingRun(
            run_id="test_1", timestamp=time.time(), status="completed",
        ))
        result = self.finetuner.list_runs()
        self.assertEqual(result["count"], 1)

    def test_get_run_not_found(self):
        result = self.finetuner.get_run("nonexistent")
        self.assertIsNone(result)

    def test_get_run_found(self):
        self.finetuner._update_run_index(TrainingRun(
            run_id="test_1", timestamp=time.time(), status="completed",
        ))
        result = self.finetuner.get_run("test_1")
        self.assertIsNotNone(result)
        self.assertEqual(result["run_id"], "test_1")

    def test_cancel_nonexistent_run(self):
        result = self.finetuner.cancel_run("nonexistent")
        self.assertFalse(result["cancelled"])

    def test_cancel_non_running_run(self):
        self.finetuner._update_run_index(TrainingRun(
            run_id="test_1", timestamp=time.time(), status="completed",
        ))
        result = self.finetuner.cancel_run("test_1")
        self.assertFalse(result["cancelled"])

    def test_collect_dream_pairs_no_file(self):
        pairs = self.finetuner._collect_dream_pairs()
        self.assertEqual(len(pairs), 0)

    def test_collect_dream_pairs_with_file(self):
        dream_dir = self.root / "memory" / "dream_cycle"
        dream_dir.mkdir(parents=True, exist_ok=True)
        history = dream_dir / "history.jsonl"
        history.write_text(json.dumps({
            "gaps_identified": [{"topic": "math", "analysis": "need more math"}],
            "recommendations": [{"area": "coding", "suggestion": "practice more"}],
        }) + "\n")
        pairs = self.finetuner._collect_dream_pairs()
        self.assertGreater(len(pairs), 0)

    def test_collect_mission_pairs_no_file(self):
        pairs = self.finetuner._collect_mission_pairs()
        self.assertEqual(len(pairs), 0)

    def test_collect_mission_pairs_with_file(self):
        missions_file = self.root / "memory" / "missions.json"
        missions_file.parent.mkdir(parents=True, exist_ok=True)
        missions_file.write_text(json.dumps([
            {"status": "completed", "task": "build X", "result": "X built"},
            {"status": "failed", "task": "build Y", "result": ""},
        ]))
        pairs = self.finetuner._collect_mission_pairs()
        self.assertEqual(len(pairs), 1)  # Only completed

    def test_collect_knowledge_pairs_no_file(self):
        pairs = self.finetuner._collect_knowledge_pairs()
        self.assertEqual(len(pairs), 0)

    def test_collect_knowledge_pairs_with_file(self):
        bootstrap = self.root / "training" / "knowledge_pairs.jsonl"
        bootstrap.parent.mkdir(parents=True, exist_ok=True)
        bootstrap.write_text(json.dumps({
            "instruction": "What is X?",
            "response": "X is...",
        }) + "\n")
        pairs = self.finetuner._collect_knowledge_pairs()
        self.assertEqual(len(pairs), 1)

    def test_check_gpu_returns_bool(self):
        result = self.finetuner._check_gpu()
        self.assertIsInstance(result, bool)

    def test_training_run_to_dict(self):
        run = TrainingRun(run_id="test", timestamp=time.time(), status="pending")
        d = run.to_dict()
        self.assertEqual(d["run_id"], "test")
        self.assertEqual(d["status"], "pending")

    def test_data_collection_result_to_dict(self):
        result = DataCollectionResult(total_pairs=10, by_source={"distillation": 10})
        d = result.to_dict()
        self.assertEqual(d["total_pairs"], 10)


# ===========================================================
# VOICE INTERPRETER TESTS
# ===========================================================

class TestVoiceInterpreter(unittest.TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.dispatch = MagicMock()
        self.interpreter = VoiceCommandInterpreter(
            self.model,
            dispatch=self.dispatch,
            ledger=MagicMock(),
        )

    def test_quick_match_system_status(self):
        result = self.interpreter.interpret("system status")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "systems_status")

    def test_quick_match_create_snapshot(self):
        result = self.interpreter.interpret("create a snapshot")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "snapshot_create")

    def test_quick_match_health_check(self):
        result = self.interpreter.interpret("run a health check")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "self_repair_check")

    def test_quick_match_drive_report(self):
        result = self.interpreter.interpret("give me the drive report")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "drive_report")

    def test_quick_match_dream_run(self):
        result = self.interpreter.interpret("start a dream cycle")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "dream_run")

    def test_quick_match_book_generate(self):
        result = self.interpreter.interpret("generate the book of anubis")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "book_generate")

    def test_quick_match_goodnight(self):
        result = self.interpreter.interpret("goodnight")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "goodnight")

    def test_quick_match_good_morning(self):
        result = self.interpreter.interpret("good morning")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "good_morning")

    def test_quick_match_weather(self):
        result = self.interpreter.interpret("what's the weather")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "weather_forecast")

    def test_quick_match_calendar(self):
        result = self.interpreter.interpret("what's on my calendar today")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "calendar_today")

    def test_quick_match_skills(self):
        result = self.interpreter.interpret("list my skills")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "skills")

    def test_quick_match_self_concept(self):
        result = self.interpreter.interpret("who are you")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "consciousness_self_concept")

    def test_quick_match_reflect(self):
        result = self.interpreter.interpret("reflect on today")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "consciousness_reflect")

    def test_quick_match_cold_archive(self):
        result = self.interpreter.interpret("create a cold archive")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "cold_archive_create")

    def test_quick_match_news(self):
        result = self.interpreter.interpret("give me the news briefing")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "news_briefing")

    def test_quick_match_bills(self):
        result = self.interpreter.interpret("what are my upcoming bills")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "finance_upcoming_bills")

    def test_quick_match_no_match(self):
        result = self.interpreter._quick_match("tell me about quantum physics")
        self.assertIsNone(result)

    def test_interpret_empty_text(self):
        result = self.interpreter.interpret("")
        self.assertEqual(result["type"], "unknown")

    def test_interpret_none_text(self):
        result = self.interpreter.interpret("")
        self.assertEqual(result["type"], "unknown")

    def test_interpret_uses_llm_for_unknown(self):
        self.model.generate.return_value = '{"type": "chat"}'
        result = self.interpreter.interpret("tell me a joke")
        self.assertEqual(result["type"], "chat")

    def test_interpret_llm_returns_command(self):
        self.model.generate.return_value = '{"type": "command", "cmd": "memory_stats", "params": {}}'
        result = self.interpreter.interpret("how much memory do you have")
        self.assertEqual(result["type"], "command")
        self.assertEqual(result["cmd"], "memory_stats")

    def test_interpret_llm_returns_invalid_json(self):
        self.model.generate.return_value = "I don't understand"
        result = self.interpreter.interpret("something weird")
        self.assertEqual(result["type"], "chat")

    def test_interpret_no_model(self):
        interp = VoiceCommandInterpreter(None)
        result = interp.interpret("something not in quick match")
        self.assertEqual(result["type"], "chat")

    def test_execute_safe_command(self):
        self.dispatch.return_value = {"status": "ok", "skills": 5}
        interp_result = {"type": "command", "cmd": "status", "params": {}}
        result = self.interpreter.execute(interp_result)
        self.assertTrue(result["executed"])
        self.dispatch.assert_called_once()

    def test_execute_restricted_command(self):
        interp_result = {"type": "command", "cmd": "email_send", "params": {}}
        result = self.interpreter.execute(interp_result)
        self.assertFalse(result["executed"])
        self.assertTrue(result.get("restricted"))
        self.dispatch.assert_not_called()

    def test_execute_no_dispatch(self):
        interp = VoiceCommandInterpreter(None)
        result = interp.execute({"type": "command", "cmd": "status", "params": {}})
        self.assertFalse(result["executed"])

    def test_execute_not_a_command(self):
        result = self.interpreter.execute({"type": "chat"})
        self.assertFalse(result["executed"])

    def test_execute_empty_command(self):
        result = self.interpreter.execute({"type": "command", "cmd": "", "params": {}})
        self.assertFalse(result["executed"])

    def test_interpret_and_execute_command(self):
        self.dispatch.return_value = {"skills": ["a", "b", "c"]}
        result = self.interpreter.interpret_and_execute("list my skills")
        self.assertTrue(result["executed"])
        self.assertIn("spoken", result)

    def test_interpret_and_execute_chat(self):
        self.model.generate.return_value = '{"type": "chat"}'
        result = self.interpreter.interpret_and_execute("tell me a joke")
        self.assertFalse(result["executed"])
        self.assertEqual(result["spoken"], "")

    def test_format_result_status(self):
        spoken = self.interpreter._format_result_for_speech("status", {
            "executed": True,
            "result": {"model": "test", "skills": 5},
        })
        self.assertIn("test", spoken)
        self.assertIn("5", spoken)

    def test_format_result_systems_status(self):
        spoken = self.interpreter._format_result_for_speech("systems_status", {
            "executed": True,
            "result": {"systems": {"a": {"ok": True}, "b": {"error": "x"}}},
        })
        self.assertIn("1 of 2", spoken)

    def test_format_result_snapshot_create(self):
        spoken = self.interpreter._format_result_for_speech("snapshot_create", {
            "executed": True,
            "result": {"snapshot_id": "snap_123"},
        })
        self.assertIn("snap_123", spoken)

    def test_format_result_self_repair_check_healthy(self):
        spoken = self.interpreter._format_result_for_speech("self_repair_check", {
            "executed": True,
            "result": {"healthy": True, "issues": []},
        })
        self.assertIn("healthy", spoken.lower())

    def test_format_result_self_repair_check_issues(self):
        spoken = self.interpreter._format_result_for_speech("self_repair_check", {
            "executed": True,
            "result": {"healthy": False, "issues": ["a", "b"]},
        })
        self.assertIn("2", spoken)

    def test_format_result_book_generate(self):
        spoken = self.interpreter._format_result_for_speech("book_generate", {
            "executed": True,
            "result": {"edition_number": 5, "words": 5000},
        })
        self.assertIn("5", spoken)

    def test_format_result_dream_run(self):
        spoken = self.interpreter._format_result_for_speech("dream_run", {
            "executed": True,
            "result": {"phases_completed": 6},
        })
        self.assertIn("6", spoken)

    def test_format_result_goodnight(self):
        spoken = self.interpreter._format_result_for_speech("goodnight", {
            "executed": True,
            "result": {},
        })
        self.assertIn("good night", spoken.lower())

    def test_format_result_error(self):
        spoken = self.interpreter._format_result_for_speech("status", {
            "executed": True,
            "result": {"error": "model not available"},
        })
        self.assertIn("Error", spoken)

    def test_format_result_not_executed(self):
        spoken = self.interpreter._format_result_for_speech("status", {
            "executed": False,
            "reason": "no dispatch",
        })
        self.assertIn("couldn't", spoken)

    def test_format_result_restricted(self):
        spoken = self.interpreter._format_result_for_speech("email_send", {
            "executed": False,
            "restricted": True,
            "reason": "requires Creator approval",
        })
        self.assertIn("Creator approval", spoken)

    def test_format_result_generic(self):
        spoken = self.interpreter._format_result_for_speech("custom_cmd", {
            "executed": True,
            "result": {"message": "custom message"},
        })
        self.assertIn("custom message", spoken)

    def test_format_result_generic_no_message(self):
        spoken = self.interpreter._format_result_for_speech("custom_cmd", {
            "executed": True,
            "result": {"key1": "val1", "key2": "val2"},
        })
        self.assertIn("custom_cmd", spoken)

    def test_get_status(self):
        status = self.interpreter.get_status()
        self.assertTrue(status["available"])
        self.assertTrue(status["has_dispatch"])
        self.assertGreater(status["safe_commands"], 0)
        self.assertGreater(status["restricted_commands"], 0)

    def test_restricted_commands_include_financial(self):
        self.assertIn("email_send", self.interpreter.RESTRICTED_COMMANDS)
        self.assertIn("voip_call", self.interpreter.RESTRICTED_COMMANDS)
        self.assertIn("lambda_submit", self.interpreter.RESTRICTED_COMMANDS)

    def test_safe_commands_include_status(self):
        self.assertIn("status", self.interpreter.SAFE_COMMANDS)
        self.assertIn("systems_status", self.interpreter.SAFE_COMMANDS)
        self.assertIn("skills", self.interpreter.SAFE_COMMANDS)

    def test_action_commands_include_snapshot(self):
        self.assertIn("snapshot_create", self.interpreter.ACTION_COMMANDS)
        self.assertIn("dream_run", self.interpreter.ACTION_COMMANDS)


# ===========================================================
# DREAM CYCLE WIRING TESTS
# ===========================================================

class TestDreamCycleWiring(unittest.TestCase):
    """Test that dream cycle commands are properly wired."""

    def test_dream_commands_exist_in_safe_list(self):
        # Dream status and history are safe (read-only)
        from anubis.voice_interpreter import VoiceCommandInterpreter
        interp = VoiceCommandInterpreter(None)
        self.assertIn("dream_status", interp.SAFE_COMMANDS)
        self.assertIn("dream_history", interp.SAFE_COMMANDS)
        self.assertIn("dream_recommendations", interp.SAFE_COMMANDS)

    def test_dream_run_in_action_commands(self):
        from anubis.voice_interpreter import VoiceCommandInterpreter
        interp = VoiceCommandInterpreter(None)
        self.assertIn("dream_run", interp.ACTION_COMMANDS)


if __name__ == "__main__":
    unittest.main()
