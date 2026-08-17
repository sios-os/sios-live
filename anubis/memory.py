"""Persistent memory for ANUBIS.

Stores conversation history, mission outcomes, and learned patterns to disk
so ANUBIS retains context across daemon restarts.

Layout:
    memory/
        conversation.jsonl      — rolling conversation history
        missions.jsonl          — mission outcomes (success/failure, skill, attempts)
        facts.json              — extracted facts about the Creator and preferences
        long_term/              — archived/summarized entries (tiered memory)
            lt_<id>.json        — individual long-term memory objects
        embeddings_cache.json   — semantic embeddings for memory recall
        purge_log.jsonl         — audit trail of all archival/purge actions
        access_log.json         — access counts and last-accessed timestamps

Privacy: all memory is local. Nothing leaves the machine. The Creator can
inspect, edit, or wipe any of these files at any time.

Recovery law: nothing is silently deleted. Entries that age out of the
active conversation are summarized and archived to long_term/, with a
hash of the original content recorded in purge_log.jsonl.

Audit law: every archival, purge, or compression action is logged to
purge_log.jsonl with the original location, timestamp, reason, and
content hash.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

# Embedding configuration — reuses the same Ollama endpoint as semantic.py.
EMBEDDING_MODEL = os.environ.get("ANUBIS_EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.environ.get("ANUBIS_OLLAMA", "http://127.0.0.1:11434")
EMBED_DIM = 768

# Default aging thresholds (in days).
DEFAULT_ARCHIVE_DAYS = 30       # conversation entries older than this get archived
DEFAULT_STALE_DAYS = 90         # long-term entries not accessed for this long get compressed further


def _embed(text: str) -> list[float]:
    """Get embedding from local Ollama. Returns empty list on failure."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embeddings",
            data=json.dumps({"model": EMBEDDING_MODEL, "prompt": text[:2000]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data.get("embedding", [])
    except Exception:
        return []


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _content_hash(text: str) -> str:
    """SHA-256 hash of text content, for audit trail."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Memory:
    """Persistent memory store for ANUBIS.

    Tiered memory architecture:
      - Active tier: recent conversation entries in conversation.jsonl
      - Long-term tier: archived/summarized entries in long_term/
      - Semantic recall: embedding-based retrieval across both tiers

    All existing methods (load_conversation, save_message, save_mission,
    context_summary, etc.) remain backward-compatible. New methods:
      - recall(query, limit): semantic recall of past context
      - purge(archive_days): archive old entries with audit trail
      - stats(): entry counts, tier sizes, access patterns
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._conversation_path = self.root / "conversation.jsonl"
        self._missions_path = self.root / "missions.jsonl"
        self._facts_path = self.root / "facts.json"
        self._long_term_dir = self.root / "long_term"
        self._long_term_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings_path = self.root / "embeddings_cache.json"
        self._purge_log_path = self.root / "purge_log.jsonl"
        self._access_log_path = self.root / "access_log.json"
        self._facts: dict[str, Any] = self._load_facts()
        self._embeddings: dict[str, list[float]] = {}
        self._embed_meta: dict[str, dict[str, Any]] = {}
        self._embeddings_loaded = False
        self._access_log: dict[str, dict[str, Any]] = self._load_access_log()

    # ------------------------------------------------------------------ facts

    def _load_facts(self) -> dict[str, Any]:
        if self._facts_path.exists():
            try:
                data = json.loads(self._facts_path.read_text(encoding="utf-8"))
                # Handle both dict and list-of-dicts formats
                if isinstance(data, list):
                    # Convert list of {"key": ..., "value": ...} to dict
                    facts: dict[str, Any] = {}
                    for item in data:
                        if isinstance(item, dict) and "key" in item:
                            facts[item["key"]] = item.get("value")
                    # Ensure required keys exist
                    facts.setdefault("creator_name", "")
                    facts.setdefault("preferences", {})
                    facts.setdefault("first_seen", time.time())
                    facts.setdefault("total_conversations", 0)
                    facts.setdefault("total_missions", 0)
                    facts.setdefault("successful_missions", 0)
                    return facts
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "creator_name": "",
            "preferences": {},
            "first_seen": time.time(),
            "total_conversations": 0,
            "total_missions": 0,
            "successful_missions": 0,
        }

    def _save_facts(self) -> None:
        self._facts_path.write_text(
            json.dumps(self._facts, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @property
    def facts(self) -> dict[str, Any]:
        return self._facts

    def set_fact(self, key: str, value: Any) -> None:
        self._facts[key] = value
        self._save_facts()

    def update_preference(self, key: str, value: Any) -> None:
        if "preferences" not in self._facts:
            self._facts["preferences"] = {}
        self._facts["preferences"][key] = value
        self._save_facts()

    # ----------------------------------------------------------- access log

    def _load_access_log(self) -> dict[str, dict[str, Any]]:
        """Load access tracking data. Keys are entry IDs."""
        if self._access_log_path.exists():
            try:
                return json.loads(self._access_log_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_access_log(self) -> None:
        self._access_log_path.write_text(
            json.dumps(self._access_log, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _record_access(self, entry_id: str) -> None:
        """Increment access count and update last-accessed timestamp."""
        info = self._access_log.get(entry_id, {"count": 0, "last_accessed": 0})
        info["count"] = info.get("count", 0) + 1
        info["last_accessed"] = time.time()
        self._access_log[entry_id] = info
        self._save_access_log()

    # ----------------------------------------------------------- embeddings

    def _load_embeddings(self) -> None:
        """Load the memory embedding cache."""
        if self._embeddings_loaded:
            return
        if self._embeddings_path.exists():
            try:
                data = json.loads(self._embeddings_path.read_text(encoding="utf-8"))
                self._embeddings = data.get("embeddings", {})
                self._embed_meta = data.get("meta", {})
            except (json.JSONDecodeError, OSError):
                pass
        self._embeddings_loaded = True

    def _save_embeddings(self) -> None:
        data = {"embeddings": self._embeddings, "meta": self._embed_meta}
        self._embeddings_path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def _index_entry(self, entry_id: str, text: str, entry_type: str) -> None:
        """Embed and index a memory entry for semantic recall."""
        self._load_embeddings()
        if not text.strip():
            return
        emb = _embed(text)
        if emb:
            self._embeddings[entry_id] = emb
            self._embed_meta[entry_id] = {
                "text": text[:500],
                "type": entry_type,
                "indexed_at": time.time(),
            }
            self._save_embeddings()

    def _reindex_conversation(self) -> int:
        """Index all conversation entries not yet in the embedding cache.

        Returns the number of newly indexed entries.
        """
        self._load_embeddings()
        if not self._conversation_path.exists():
            return 0
        indexed = 0
        lines = self._conversation_path.read_text(encoding="utf-8").strip().splitlines()
        for i, line in enumerate(lines):
            entry_id = f"conv_{i}"
            if entry_id in self._embeddings:
                continue
            try:
                entry = json.loads(line)
                text = entry.get("content", "")
                if text.strip():
                    emb = _embed(text)
                    if emb:
                        self._embeddings[entry_id] = emb
                        self._embed_meta[entry_id] = {
                            "text": text[:500],
                            "type": "conversation",
                            "indexed_at": time.time(),
                        }
                        indexed += 1
            except (json.JSONDecodeError, KeyError):
                continue
        if indexed:
            self._save_embeddings()
        return indexed

    # ----------------------------------------------------------- conversation

    def load_conversation(self, limit: int = 20) -> list[dict[str, str]]:
        """Load recent conversation history as message dicts."""
        if not self._conversation_path.exists():
            return []
        messages = []
        lines = self._conversation_path.read_text(encoding="utf-8").strip().splitlines()
        for line in lines[-limit * 2:]:  # each exchange is 2 lines (user + assistant)
            try:
                entry = json.loads(line)
                messages.append({
                    "role": entry["role"],
                    "content": entry["content"],
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return messages

    def save_message(self, role: str, content: str) -> None:
        """Append a message to the conversation log and index it."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        with open(self._conversation_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        if role == "user":
            self._facts["total_conversations"] = (
                self._facts.get("total_conversations", 0) + 1
            )
            self._save_facts()
        # Index the new message for semantic recall (best-effort, non-blocking)
        try:
            with open(self._conversation_path, encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
            entry_id = f"conv_{line_count - 1}"
            self._index_entry(entry_id, content, "conversation")
        except Exception:
            pass  # embedding failure is non-fatal

    def clear_conversation(self) -> int:
        """Wipe conversation history. Returns number of messages cleared.

        The cleared entries are logged to purge_log.jsonl for audit, but
        not archived (the Creator explicitly requested deletion).
        """
        if not self._conversation_path.exists():
            return 0
        lines = self._conversation_path.read_text(encoding="utf-8").strip().splitlines()
        count = len(lines)
        # Audit the clear action
        hashes = []
        for line in lines:
            try:
                entry = json.loads(line)
                hashes.append(_content_hash(entry.get("content", "")))
            except json.JSONDecodeError:
                continue
        self._log_purge({
            "action": "cleared",
            "source": "conversation",
            "entry_count": count,
            "original_hashes": hashes,
            "reason": "Creator requested clear",
        })
        self._conversation_path.unlink()
        # Remove conversation embeddings from cache
        self._load_embeddings()
        conv_keys = [k for k in self._embeddings if k.startswith("conv_")]
        for k in conv_keys:
            self._embeddings.pop(k, None)
            self._embed_meta.pop(k, None)
        if conv_keys:
            self._save_embeddings()
        return count

    # -------------------------------------------------------------- missions

    def save_mission(self, mission: dict[str, Any]) -> None:
        """Record a mission outcome."""
        entry = {
            **mission,
            "timestamp": time.time(),
        }
        with open(self._missions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self._facts["total_missions"] = self._facts.get("total_missions", 0) + 1
        if mission.get("success"):
            self._facts["successful_missions"] = (
                self._facts.get("successful_missions", 0) + 1
            )
        self._save_facts()
        # Index mission for semantic recall
        try:
            with open(self._missions_path, encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
            entry_id = f"mission_{line_count - 1}"
            text = f"{mission.get('skill_name', '?')}: {mission.get('task', '')}"
            self._index_entry(entry_id, text, "mission")
        except Exception:
            pass

    def load_mission_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Load recent mission outcomes."""
        if not self._missions_path.exists():
            return []
        lines = self._missions_path.read_text(encoding="utf-8").strip().splitlines()
        missions = []
        for line in lines[-limit:]:
            try:
                missions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return missions

    # ----------------------------------------------------------- long-term

    def _archive_entries(
        self, entries: list[dict[str, Any]], source: str, reason: str
    ) -> str:
        """Archive entries to the long-term tier with a summary.

        Returns the long-term entry ID.
        """
        lt_id = f"lt_{int(time.time() * 1000)}_{source}"
        # Create a summary from the entries
        contents = [e.get("content", str(e)) for e in entries]
        combined = " ".join(contents)
        # Simple compression: take first 500 chars of each entry, joined
        summary = " | ".join(c[:200] for c in contents)[:2000]
        original_hashes = [_content_hash(c) for c in contents]

        lt_entry = {
            "id": lt_id,
            "source": source,
            "reason": reason,
            "original_timestamp": entries[0].get("timestamp", time.time()) if entries else time.time(),
            "archived_timestamp": time.time(),
            "summary": summary,
            "entry_count": len(entries),
            "original_hashes": original_hashes,
        }
        lt_path = self._long_term_dir / f"{lt_id}.json"
        lt_path.write_text(
            json.dumps(lt_entry, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # Index the summary for semantic recall
        self._index_entry(lt_id, summary, "long_term")
        # Audit the archival
        self._log_purge({
            "action": "archived",
            "source": source,
            "entry_count": len(entries),
            "original_hashes": original_hashes,
            "long_term_id": lt_id,
            "reason": reason,
        })
        return lt_id

    def _load_long_term_entries(self) -> list[dict[str, Any]]:
        """Load all long-term memory entries."""
        entries = []
        for path in sorted(self._long_term_dir.glob("lt_*.json")):
            try:
                entries.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return entries

    # ----------------------------------------------------------- purge log

    def _log_purge(self, record: dict[str, Any]) -> None:
        """Append a record to the purge log (audit trail)."""
        entry = {**record, "timestamp": time.time()}
        with open(self._purge_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def load_purge_log(self, limit: int = 50) -> list[dict[str, Any]]:
        """Load recent purge log entries."""
        if not self._purge_log_path.exists():
            return []
        lines = self._purge_log_path.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    # ----------------------------------------------------------- semantic recall

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Semantic recall of past context.

        Searches both active conversation entries and long-term archived
        entries using embedding similarity. Returns the most relevant
        past context for the given query.

        Falls back to returning empty list if embeddings are unavailable
        (e.g. Ollama not running). This is non-fatal — the caller can
        still use load_conversation for recent context.
        """
        self._load_embeddings()
        if not self._embeddings:
            # Try to index conversation entries if cache is empty
            self._reindex_conversation()
            self._load_embeddings()
        if not self._embeddings:
            return []

        query_emb = _embed(query)
        if not query_emb:
            return []

        scores: list[tuple[str, float]] = []
        for entry_id, emb in self._embeddings.items():
            sim = _cosine_sim(query_emb, emb)
            scores.append((entry_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for entry_id, score in scores[:limit]:
            meta = self._embed_meta.get(entry_id, {})
            # Record access for long-term entries (for stale detection)
            if entry_id.startswith("lt_"):
                self._record_access(entry_id)
            results.append({
                "entry_id": entry_id,
                "score": round(score, 4),
                "type": meta.get("type", "unknown"),
                "text": meta.get("text", ""),
            })
        return results

    # ----------------------------------------------------------- purge/archive

    def purge(self, archive_days: int = DEFAULT_ARCHIVE_DAYS) -> dict[str, int]:
        """Archive old conversation entries to the long-term tier.

        Entries older than archive_days are summarized and moved to
        long_term/. The original entries are removed from
        conversation.jsonl, but their content hashes are recorded in
        purge_log.jsonl for audit and recovery.

        Before archiving, training pairs are extracted from the
        conversation entries via the KnowledgeDistiller and queued
        for future fine-tuning runs. This turns garbage collection
        into active learning.

        Returns a summary of what was archived (and distilled).
        """
        if not self._conversation_path.exists():
            return {"archived": 0, "remaining": 0, "long_term_created": 0}

        cutoff = time.time() - (archive_days * 86400)
        lines = self._conversation_path.read_text(encoding="utf-8").strip().splitlines()
        to_archive: list[dict[str, Any]] = []
        to_keep: list[str] = []
        for line in lines:
            try:
                entry = json.loads(line)
                if entry.get("timestamp", 0) < cutoff:
                    to_archive.append(entry)
                else:
                    to_keep.append(line)
            except json.JSONDecodeError:
                to_keep.append(line)  # keep unparseable lines rather than losing them

        if not to_archive:
            return {"archived": 0, "remaining": len(to_keep), "long_term_created": 0}

        # Distill training pairs before archiving
        distilled = 0
        try:
            from .distillation import KnowledgeDistiller
            distiller = KnowledgeDistiller(
                queue_path=self.root / "distillation_queue.jsonl",
            )
            result = distiller.distill(to_archive)
            distilled = result.pairs_queued
        except Exception:
            # Distillation failure should not block purge
            distilled = 0

        # Group archived entries into batches of 10 for summarization
        lt_created = 0
        for i in range(0, len(to_archive), 10):
            batch = to_archive[i:i + 10]
            self._archive_entries(batch, "conversation", f"aged out (>{archive_days} days)")
            lt_created += 1

        # Rewrite conversation.jsonl with only the kept entries
        self._conversation_path.write_text(
            "\n".join(to_keep) + ("\n" if to_keep else ""), encoding="utf-8"
        )

        return {
            "archived": len(to_archive),
            "remaining": len(to_keep),
            "long_term_created": lt_created,
            "distilled_pairs": distilled,
        }

    def rebuild_index(self) -> dict[str, Any]:
        """Rebuild the embedding index after purges.

        Removes embedding cache entries for archived/deleted conversation
        entries and rebuilds the index to prevent fragmentation. This
        should be called after purge() to maintain retrieval quality.

        Uses the VectorIndex from anubis.vector_index for efficient
        similarity search if available, otherwise just cleans the
        embedding cache.
        """
        t0 = time.monotonic()
        removed = 0

        # Get current conversation entry IDs (line-based: conv_0, conv_1, ...)
        current_ids: set[str] = set()
        if self._conversation_path.exists():
            lines = self._conversation_path.read_text(encoding="utf-8").strip().splitlines()
            for i in range(len(lines)):
                current_ids.add(f"conv_{i}")

        # Add long-term entry IDs
        lt_entries = self._load_long_term_entries()
        for lt in lt_entries:
            eid = lt.get("id", "")
            if eid:
                current_ids.add(eid)

        # Remove embeddings for entries that no longer exist
        self._load_embeddings()
        stale_keys = [k for k in self._embeddings if k not in current_ids]
        for key in stale_keys:
            del self._embeddings[key]
            removed += 1

        # Save cleaned embeddings
        if stale_keys:
            self._save_embeddings()

        # Clear access log for removed entries
        stale_access = [k for k in self._access_log if k not in current_ids]
        for key in stale_access:
            del self._access_log[key]
        if stale_access:
            self._save_access_log()

        elapsed = time.monotonic() - t0
        return {
            "removed_stale": removed,
            "remaining_embeddings": len(self._embeddings),
            "duration_s": round(elapsed, 3),
        }

    # ----------------------------------------------------------- stats

    def stats(self) -> dict[str, Any]:
        """Return memory statistics for monitoring and the daemon."""
        conv_count = 0
        if self._conversation_path.exists():
            with open(self._conversation_path, encoding="utf-8") as f:
                conv_count = sum(1 for _ in f)
        mission_count = 0
        if self._missions_path.exists():
            with open(self._missions_path, encoding="utf-8") as f:
                mission_count = sum(1 for _ in f)
        lt_entries = self._load_long_term_entries()
        purge_count = 0
        if self._purge_log_path.exists():
            with open(self._purge_log_path, encoding="utf-8") as f:
                purge_count = sum(1 for _ in f)
        self._load_embeddings()
        # Access pattern stats
        access_counts = [v.get("count", 0) for v in self._access_log.values()]
        avg_access = sum(access_counts) / len(access_counts) if access_counts else 0
        return {
            "conversation_entries": conv_count,
            "mission_entries": mission_count,
            "long_term_entries": len(lt_entries),
            "purge_log_entries": purge_count,
            "indexed_entries": len(self._embeddings),
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": EMBED_DIM,
            "facts": {
                "creator_name": self._facts.get("creator_name", ""),
                "total_conversations": self._facts.get("total_conversations", 0),
                "total_missions": self._facts.get("total_missions", 0),
                "successful_missions": self._facts.get("successful_missions", 0),
                "preferences_count": len(self._facts.get("preferences", {})),
            },
            "access_patterns": {
                "tracked_entries": len(self._access_log),
                "avg_access_count": round(avg_access, 2),
            },
        }

    # ---------------------------------------------------------------- summary

    def context_summary(self) -> str:
        """A brief summary for the system prompt so ANUBIS has memory context."""
        parts = []
        if self._facts.get("creator_name"):
            parts.append(f"The Creator's name is {self._facts['creator_name']}.")
        total_conv = self._facts.get("total_conversations", 0)
        total_mis = self._facts.get("total_missions", 0)
        successful = self._facts.get("successful_missions", 0)
        if total_conv > 0:
            parts.append(
                f"You have had {total_conv} conversations with the Creator, "
                f"run {total_mis} missions ({successful} successful)."
            )
        prefs = self._facts.get("preferences", {})
        if prefs:
            pref_strs = [f"{k}: {v}" for k, v in prefs.items()]
            parts.append("Creator preferences: " + ", ".join(pref_strs))
        # Recent mission context
        recent = self.load_mission_history(3)
        if recent:
            parts.append("Recent missions:")
            for m in recent:
                status = "succeeded" if m.get("success") else "failed"
                parts.append(
                    f"  - {m.get('skill_name', '?')}: {status} "
                    f"({m.get('attempts', '?')} attempts)"
                )
        # Long-term memory count
        lt_entries = self._load_long_term_entries()
        if lt_entries:
            parts.append(f"You have {len(lt_entries)} long-term memory archives from past conversations.")
        if not parts:
            return ""
        return "\n".join(parts)
