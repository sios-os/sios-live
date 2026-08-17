"""Tests for the improved Memory module — tiered memory, semantic recall,
access tracking, and auditable purge.

These tests use only the Python standard library and do not require Ollama
to be running. The semantic recall tests gracefully skip when embeddings
are unavailable (Ollama not running), since that is the documented
non-fatal fallback behavior.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.memory import Memory, _content_hash, _cosine_sim


class TestMemoryBasics(unittest.TestCase):
    """Verify backward compatibility with the original Memory interface."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-test-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_conversation(self):
        self.mem.save_message("user", "Hello ANUBIS")
        self.mem.save_message("assistant", "Hello Creator")
        msgs = self.mem.load_conversation()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[0]["content"], "Hello ANUBIS")
        self.assertEqual(msgs[1]["role"], "assistant")

    def test_save_and_load_mission(self):
        self.mem.save_mission({
            "mission_id": "test1",
            "skill_name": "checksum",
            "task": "write a checksum function",
            "success": True,
            "attempts": 1,
        })
        history = self.mem.load_mission_history()
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["success"])
        self.assertEqual(history[0]["skill_name"], "checksum")

    def test_facts_persistence(self):
        self.mem.set_fact("creator_name", "Storm")
        self.mem.update_preference("language", "Python")
        # Reload from disk
        mem2 = Memory(self.tmpdir)
        self.assertEqual(mem2.facts["creator_name"], "Storm")
        self.assertEqual(mem2.facts["preferences"]["language"], "Python")

    def test_clear_conversation(self):
        self.mem.save_message("user", "test message 1")
        self.mem.save_message("user", "test message 2")
        count = self.mem.clear_conversation()
        self.assertEqual(count, 2)
        msgs = self.mem.load_conversation()
        self.assertEqual(len(msgs), 0)

    def test_context_summary(self):
        self.mem.set_fact("creator_name", "Storm")
        self.mem.save_mission({
            "mission_id": "test1",
            "skill_name": "checksum",
            "task": "write a checksum",
            "success": True,
            "attempts": 1,
        })
        summary = self.mem.context_summary()
        self.assertIn("Storm", summary)
        self.assertIn("checksum", summary)

    def test_conversation_count_increments(self):
        self.mem.save_message("user", "message 1")
        self.mem.save_message("user", "message 2")
        self.mem.save_message("assistant", "response 1")
        # Only user messages increment total_conversations
        self.assertEqual(self.mem.facts["total_conversations"], 2)


class TestLongTermMemory(unittest.TestCase):
    """Tests for the long-term memory tier."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-lt-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_long_term_dir_created(self):
        lt_dir = Path(self.tmpdir) / "long_term"
        self.assertTrue(lt_dir.exists())
        self.assertTrue(lt_dir.is_dir())

    def test_purge_archives_old_entries(self):
        # Save some messages with old timestamps
        for i in range(5):
            entry = {
                "role": "user",
                "content": f"old message {i}",
                "timestamp": time.time() - (40 * 86400),  # 40 days ago
            }
            with open(self.mem._conversation_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        # Save a recent message
        self.mem.save_message("user", "recent message")

        result = self.mem.purge(archive_days=30)
        self.assertEqual(result["archived"], 5)
        self.assertEqual(result["remaining"], 1)
        self.assertGreater(result["long_term_created"], 0)

        # Verify long-term entries were created
        lt_entries = self.mem._load_long_term_entries()
        self.assertGreater(len(lt_entries), 0)
        self.assertIn("summary", lt_entries[0])
        self.assertIn("original_hashes", lt_entries[0])
        self.assertEqual(lt_entries[0]["entry_count"], 5)

    def test_purge_keeps_recent_entries(self):
        self.mem.save_message("user", "recent message 1")
        self.mem.save_message("user", "recent message 2")
        result = self.mem.purge(archive_days=30)
        self.assertEqual(result["archived"], 0)
        self.assertEqual(result["remaining"], 2)

    def test_purge_empty_conversation(self):
        result = self.mem.purge(archive_days=30)
        self.assertEqual(result["archived"], 0)
        self.assertEqual(result["remaining"], 0)


class TestAuditablePurge(unittest.TestCase):
    """Tests for the purge audit trail (audit immutable law)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-audit-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_purge_log_created_on_archive(self):
        # Create old entries
        for i in range(3):
            entry = {
                "role": "user",
                "content": f"old message {i}",
                "timestamp": time.time() - (40 * 86400),
            }
            with open(self.mem._conversation_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        self.mem.purge(archive_days=30)

        log = self.mem.load_purge_log()
        self.assertGreater(len(log), 0)
        self.assertEqual(log[0]["action"], "archived")
        self.assertEqual(log[0]["source"], "conversation")
        self.assertIn("original_hashes", log[0])
        self.assertIn("long_term_id", log[0])
        self.assertEqual(len(log[0]["original_hashes"]), 3)

    def test_purge_log_created_on_clear(self):
        self.mem.save_message("user", "message to clear")
        self.mem.clear_conversation()

        log = self.mem.load_purge_log()
        self.assertGreater(len(log), 0)
        self.assertEqual(log[0]["action"], "cleared")
        self.assertEqual(log[0]["reason"], "Creator requested clear")
        self.assertIn("original_hashes", log[0])

    def test_purge_log_has_timestamps(self):
        self.mem.save_message("user", "test")
        self.mem.clear_conversation()
        log = self.mem.load_purge_log()
        self.assertIn("timestamp", log[0])
        self.assertGreater(log[0]["timestamp"], 0)

    def test_content_hash_deterministic(self):
        h1 = _content_hash("test content")
        h2 = _content_hash("test content")
        h3 = _content_hash("different content")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64)  # SHA-256 hex


class TestAccessTracking(unittest.TestCase):
    """Tests for access count and last-accessed tracking."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-access-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_access_log_file_created(self):
        # Access log file should exist after first save
        self.mem.save_message("user", "test")
        # Access log may be empty but the path should be set
        self.assertTrue(hasattr(self.mem, "_access_log_path"))

    def test_record_access_increments(self):
        self.mem._record_access("test_entry_1")
        self.mem._record_access("test_entry_1")
        self.assertEqual(self.mem._access_log["test_entry_1"]["count"], 2)
        self.assertGreater(self.mem._access_log["test_entry_1"]["last_accessed"], 0)

    def test_access_log_persists(self):
        self.mem._record_access("test_entry_1")
        mem2 = Memory(self.tmpdir)
        self.assertIn("test_entry_1", mem2._access_log)
        self.assertEqual(mem2._access_log["test_entry_1"]["count"], 1)


class TestStats(unittest.TestCase):
    """Tests for the memory stats endpoint."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-stats-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stats_basic(self):
        self.mem.save_message("user", "test message")
        self.mem.save_mission({
            "mission_id": "test1",
            "skill_name": "test_skill",
            "task": "test task",
            "success": True,
            "attempts": 1,
        })
        stats = self.mem.stats()
        self.assertEqual(stats["conversation_entries"], 1)
        self.assertEqual(stats["mission_entries"], 1)
        self.assertEqual(stats["long_term_entries"], 0)
        self.assertIn("embedding_model", stats)
        self.assertIn("facts", stats)
        self.assertEqual(stats["facts"]["total_missions"], 1)

    def test_stats_after_purge(self):
        # Create old entries and purge
        for i in range(5):
            entry = {
                "role": "user",
                "content": f"old message {i}",
                "timestamp": time.time() - (40 * 86400),
            }
            with open(self.mem._conversation_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        self.mem.purge(archive_days=30)
        stats = self.mem.stats()
        self.assertGreater(stats["long_term_entries"], 0)
        self.assertGreater(stats["purge_log_entries"], 0)


class TestCosineSim(unittest.TestCase):
    """Tests for the cosine similarity helper."""

    def test_identical_vectors(self):
        a = [1.0, 2.0, 3.0]
        sim = _cosine_sim(a, a)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        sim = _cosine_sim(a, b)
        self.assertAlmostEqual(sim, 0.0, places=5)

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 2.0]
        sim = _cosine_sim(a, b)
        self.assertEqual(sim, 0.0)


class TestSemanticRecall(unittest.TestCase):
    """Tests for semantic recall. These gracefully skip when Ollama is not
    running, since embedding-based recall is a non-fatal enhancement."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-recall-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_recall_returns_list(self):
        # Should return a list even when embeddings are unavailable
        results = self.mem.recall("test query")
        self.assertIsInstance(results, list)

    def test_recall_empty_when_no_data(self):
        results = self.mem.recall("test query")
        self.assertEqual(len(results), 0)

    def test_recall_does_not_crash_without_ollama(self):
        # This test verifies graceful degradation when Ollama is not running
        self.mem.save_message("user", "Hello ANUBIS, how are you?")
        # recall should not raise even if embedding fails
        try:
            results = self.mem.recall("greeting")
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"recall() should not raise when Ollama is unavailable: {e}")


class TestEmbeddingCache(unittest.TestCase):
    """Tests for the embedding cache persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-emb-")
        self.mem = Memory(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_embeddings_path_set(self):
        self.assertTrue(hasattr(self.mem, "_embeddings_path"))
        self.assertEqual(self.mem._embeddings_path.name, "embeddings_cache.json")

    def test_embeddings_loaded_lazily(self):
        # Embeddings should not be loaded until first access
        self.assertFalse(self.mem._embeddings_loaded)
        self.mem._load_embeddings()
        self.assertTrue(self.mem._embeddings_loaded)

    def test_save_and_load_embeddings(self):
        # Manually add an embedding and save
        self.mem._load_embeddings()
        self.mem._embeddings["test_id"] = [0.1, 0.2, 0.3]
        self.mem._embed_meta["test_id"] = {"text": "test", "type": "conversation"}
        self.mem._save_embeddings()

        # Reload from disk
        mem2 = Memory(self.tmpdir)
        mem2._load_embeddings()
        self.assertIn("test_id", mem2._embeddings)
        self.assertEqual(mem2._embeddings["test_id"], [0.1, 0.2, 0.3])
        self.assertEqual(mem2._embed_meta["test_id"]["text"], "test")


class TestRebuildIndex(unittest.TestCase):
    """Tests for the rebuild_index method (prevents fragmentation after purge)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="anubis-mem-rebuild-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_rebuild_empty(self):
        mem = Memory(self.tmpdir)
        result = mem.rebuild_index()
        self.assertEqual(result["removed_stale"], 0)

    def test_rebuild_removes_stale_embeddings(self):
        mem = Memory(self.tmpdir)
        # Add an embedding for a non-existent entry
        mem._embeddings["ghost_id"] = [0.1] * 768
        mem._embed_meta["ghost_id"] = {"text": "ghost"}
        mem._save_embeddings()
        # Rebuild should remove it
        result = mem.rebuild_index()
        self.assertEqual(result["removed_stale"], 1)
        self.assertNotIn("ghost_id", mem._embeddings)

    def test_rebuild_preserves_existing_entries(self):
        mem = Memory(self.tmpdir)
        mem.save_message("user", "hello world")
        # Conversation entries use line-based IDs: conv_0, conv_1, ...
        entry_id = "conv_0"
        # Add embedding for it
        mem._embeddings[entry_id] = [0.1] * 768
        mem._embed_meta[entry_id] = {"text": "hello world"}
        mem._save_embeddings()
        # Rebuild should preserve it
        result = mem.rebuild_index()
        self.assertEqual(result["removed_stale"], 0)
        self.assertIn(entry_id, mem._embeddings)


if __name__ == "__main__":
    unittest.main()
