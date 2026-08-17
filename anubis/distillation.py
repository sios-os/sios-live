"""Knowledge distillation during the Midnight Purge.

Instead of just archiving old conversation entries, this module
extracts prompt-response pairs from the day's conversations and
prepares them as training data for micro-fine-tuning runs.

The distillation process:
1. Collect conversation entries from the purge window
2. Group user/assistant exchanges into prompt-response pairs
3. Summarize structural coding lessons into clear training pairs
4. Queue the pairs for a micro-fine-tuning run
5. Log to the evidence ledger

This turns garbage collection into active learning — the system
bakes its daily discoveries directly into its neural weights during
the purge hours, freeing up the vector index while retaining knowledge.

Training pairs are stored in a queue file and require Creator
approval before actual fine-tuning is executed (per the constitution).
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class TrainingPair:
    """A single prompt-response training pair."""
    prompt: str
    response: str
    source_id: str = ""
    category: str = "general"  # general, coding, reasoning, factual
    quality_score: float = 0.0
    created_at: float = 0.0
    pair_hash: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.pair_hash:
            h = hashlib.sha256(
                f"{self.prompt}:{self.response}".encode("utf-8")
            ).hexdigest()
            self.pair_hash = h[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "response": self.response,
            "source_id": self.source_id,
            "category": self.category,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
            "pair_hash": self.pair_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingPair":
        return cls(
            prompt=data.get("prompt", ""),
            response=data.get("response", ""),
            source_id=data.get("source_id", ""),
            category=data.get("category", "general"),
            quality_score=data.get("quality_score", 0.0),
            created_at=data.get("created_at", 0.0),
            pair_hash=data.get("pair_hash", ""),
        )


@dataclass
class DistillationResult:
    """Result of a distillation run."""
    pairs_extracted: int = 0
    pairs_queued: int = 0
    pairs_skipped: int = 0
    categories: dict[str, int] = field(default_factory=dict)
    duration_s: float = 0.0


class KnowledgeDistiller:
    """Extract training pairs from conversation entries.

    Used during the Midnight Purge to convert daily conversations
    into structured training data for micro-fine-tuning.
    """

    def __init__(
        self,
        queue_path: str | Path = "memory/distillation_queue.jsonl",
        ledger: Ledger | None = None,
    ) -> None:
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger

    def _classify_pair(self, prompt: str, response: str) -> str:
        """Classify a training pair by category."""
        combined = (prompt + " " + response).lower()
        if any(w in combined for w in ["def ", "class ", "import ", "function", "code", "bug", "error"]):
            return "coding"
        if any(w in combined for w in ["because", "therefore", "step ", "reason", "logic", "analysis"]):
            return "reasoning"
        if any(w in combined for w in ["what is", "who is", "when did", "where is", "fact"]):
            return "factual"
        return "general"

    def _score_quality(self, prompt: str, response: str) -> float:
        """Score the quality of a training pair (0.0 to 1.0).

        Higher scores for:
        - Longer, more detailed responses
        - Prompts that are clear questions
        - Responses that contain code or structured info
        """
        score = 0.0
        # Response length (up to 0.3)
        resp_len = len(response)
        if resp_len > 200:
            score += 0.3
        elif resp_len > 50:
            score += 0.15
        elif resp_len > 10:
            score += 0.05

        # Prompt clarity (up to 0.2)
        if "?" in prompt or any(w in prompt.lower() for w in ["how", "what", "why", "explain"]):
            score += 0.2

        # Code presence (up to 0.2)
        if "def " in response or "class " in response or "```" in response:
            score += 0.2

        # Structured response (up to 0.15)
        if any(w in response for w in ["1.", "2.", "3.", "- ", "* "]):
            score += 0.15

        # Not too short (up to 0.15)
        if len(prompt) > 10:
            score += 0.15

        return min(score, 1.0)

    def extract_pairs(
        self, entries: list[dict[str, Any]]
    ) -> list[TrainingPair]:
        """Extract training pairs from conversation entries.

        Groups user/assistant exchanges into prompt-response pairs.
        Only pairs with both a meaningful prompt and response are kept.
        """
        pairs: list[TrainingPair] = []
        i = 0
        while i < len(entries) - 1:
            current = entries[i]
            next_entry = entries[i + 1]

            # Look for user → assistant pairs
            if (
                current.get("role") == "user"
                and next_entry.get("role") == "assistant"
            ):
                prompt = current.get("content", "").strip()
                response = next_entry.get("content", "").strip()

                # Skip trivial pairs
                if len(prompt) < 5 or len(response) < 5:
                    i += 2
                    continue

                category = self._classify_pair(prompt, response)
                quality = self._score_quality(prompt, response)

                pair = TrainingPair(
                    prompt=prompt,
                    response=response,
                    source_id=f"conv_{i}",
                    category=category,
                    quality_score=quality,
                )
                pairs.append(pair)
                i += 2
            else:
                i += 1

        return pairs

    def queue_pairs(
        self,
        pairs: list[TrainingPair],
        *,
        min_quality: float = 0.2,
    ) -> int:
        """Add training pairs to the distillation queue.

        Only pairs above min_quality are queued. Existing pairs
        (by hash) are skipped to prevent duplicates.
        """
        # Load existing hashes
        existing_hashes: set[str] = set()
        if self.queue_path.exists():
            for line in self.queue_path.read_text(encoding="utf-8").strip().splitlines():
                try:
                    entry = json.loads(line)
                    existing_hashes.add(entry.get("pair_hash", ""))
                except json.JSONDecodeError:
                    continue

        queued = 0
        with open(self.queue_path, "a", encoding="utf-8") as f:
            for pair in pairs:
                if pair.quality_score < min_quality:
                    continue
                if pair.pair_hash in existing_hashes:
                    continue
                f.write(json.dumps(pair.to_dict(), ensure_ascii=False) + "\n")
                existing_hashes.add(pair.pair_hash)
                queued += 1

        return queued

    def distill(
        self,
        entries: list[dict[str, Any]],
        *,
        min_quality: float = 0.2,
    ) -> DistillationResult:
        """Full distillation pipeline: extract, score, queue.

        Args:
            entries: Conversation entries to distill
            min_quality: Minimum quality score to queue a pair

        Returns:
            DistillationResult with counts and stats
        """
        t0 = time.monotonic()
        pairs = self.extract_pairs(entries)
        queued = self.queue_pairs(pairs, min_quality=min_quality)

        categories: dict[str, int] = {}
        for pair in pairs:
            categories[pair.category] = categories.get(pair.category, 0) + 1

        # Log to evidence ledger
        if self.ledger:
            self.ledger.append({
                "event": "distillation",
                "pairs_extracted": len(pairs),
                "pairs_queued": queued,
                "pairs_skipped": len(pairs) - queued,
                "categories": categories,
            })

        return DistillationResult(
            pairs_extracted=len(pairs),
            pairs_queued=queued,
            pairs_skipped=len(pairs) - queued,
            categories=categories,
            duration_s=round(time.monotonic() - t0, 3),
        )

    def load_queue(self) -> list[TrainingPair]:
        """Load all queued training pairs."""
        if not self.queue_path.exists():
            return []
        pairs = []
        for line in self.queue_path.read_text(encoding="utf-8").strip().splitlines():
            try:
                pairs.append(TrainingPair.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                continue
        return pairs

    def clear_queue(self) -> int:
        """Clear the distillation queue. Returns count cleared."""
        if not self.queue_path.exists():
            return 0
        count = 0
        for _ in self.queue_path.read_text(encoding="utf-8").strip().splitlines():
            count += 1
        self.queue_path.unlink()
        return count

    def export_training_data(
        self,
        output_path: str | Path,
        *,
        category: str | None = None,
        min_quality: float = 0.0,
    ) -> dict[str, Any]:
        """Export queued pairs as a training dataset (JSONL format).

        Args:
            output_path: Where to write the dataset
            category: Filter by category (None = all)
            min_quality: Minimum quality score

        Returns:
            Export stats
        """
        pairs = self.load_queue()
        exported = 0
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                if category and pair.category != category:
                    continue
                if pair.quality_score < min_quality:
                    continue
                # Standard instruction-tuning format
                record = {
                    "instruction": pair.prompt,
                    "output": pair.response,
                    "category": pair.category,
                    "quality": pair.quality_score,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                exported += 1

        return {
            "exported": exported,
            "total_available": len(pairs),
            "output_path": str(output_path),
        }

    def stats(self) -> dict[str, Any]:
        """Return distillation queue statistics."""
        pairs = self.load_queue()
        categories: dict[str, int] = {}
        avg_quality = 0.0
        for pair in pairs:
            categories[pair.category] = categories.get(pair.category, 0) + 1
            avg_quality += pair.quality_score
        if pairs:
            avg_quality /= len(pairs)
        return {
            "queued_pairs": len(pairs),
            "categories": categories,
            "avg_quality": round(avg_quality, 3),
            "queue_path": str(self.queue_path),
        }
