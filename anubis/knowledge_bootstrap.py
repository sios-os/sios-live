"""Knowledge bootstrapping — convert existing knowledge into training data.

ANUBIS has 550+ knowledge documents but an empty distillation queue. This
module bootstraps training data by converting existing knowledge into
prompt-response training pairs, so ANUBIS can start training without
needing weeks of conversations first.

Conversion strategies:
1. **Title → Content** — Document title as prompt, content as response
2. **Question → Answer** — Generate questions from content, use content as answer
3. **Summary → Detail** — Generate a summary as prompt, full content as response
4. **Code → Explanation** — For code-heavy docs, code as prompt, explanation as response
5. **Cross-domain** — Mix knowledge from different domains for reasoning tasks

This produces initial training pairs that give ANUBIS a starting dataset
for his first fine-tune. The quality is lower than conversation-derived
pairs (no real interaction), but it's enough to bootstrap.

Uses only the Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


# --------------------------------------------------------------------- types


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


@dataclass
class BootstrapResult:
    """Result of a bootstrapping run."""
    total_documents: int = 0
    pairs_generated: int = 0
    pairs_by_category: dict[str, int] = field(default_factory=dict)
    pairs_by_strategy: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def duration_s(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "pairs_generated": self.pairs_generated,
            "pairs_by_category": self.pairs_by_category,
            "pairs_by_strategy": self.pairs_by_strategy,
            "errors": self.errors,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_s": round(self.duration_s, 2),
        }


# --------------------------------------------------------------- bootstrap


class KnowledgeBootstrapper:
    """Converts existing knowledge documents into training pairs.

    This is a one-time (or periodic) operation that fills the distillation
    queue with initial training data from the knowledge library.
    """

    ACTOR = "anubis.bootstrap"

    def __init__(
        self,
        root: str | Path,
        *,
        model: ModelLike | None = None,
        ledger: Any | None = None,
        max_pairs_per_doc: int = 3,
        max_total_pairs: int = 5000,
    ) -> None:
        self.root = Path(root)
        self.model = model
        self.ledger = ledger
        self.max_pairs_per_doc = max_pairs_per_doc
        self.max_total_pairs = max_total_pairs

        self._knowledge_dir = self.root / "knowledge"
        self._queue_path = self.root / "distillation_queue.jsonl"

    def bootstrap(self) -> BootstrapResult:
        """Run the bootstrapping process.

        Scans all knowledge documents and converts them into training pairs.
        """
        result = BootstrapResult(started_at=time.time())

        if not self._knowledge_dir.exists():
            result.errors.append("Knowledge directory does not exist")
            result.completed_at = time.time()
            return result

        # Find all knowledge documents
        docs = self._scan_documents()
        result.total_documents = len(docs)

        if not docs:
            result.errors.append("No knowledge documents found")
            result.completed_at = time.time()
            return result

        # Generate training pairs
        pairs: list[dict[str, Any]] = []
        for doc in docs:
            if len(pairs) >= self.max_total_pairs:
                break
            try:
                doc_pairs = self._convert_document(doc)
                # Only add up to max_total_pairs
                remaining = self.max_total_pairs - len(pairs)
                pairs.extend(doc_pairs[:remaining])
            except Exception as exc:
                result.errors.append(f"Error processing {doc['title']}: {exc}")

        # Write to distillation queue
        written = self._write_pairs(pairs)
        result.pairs_generated = written

        # Categorize
        for p in pairs:
            cat = p.get("category", "general")
            result.pairs_by_category[cat] = result.pairs_by_category.get(cat, 0) + 1
            strat = p.get("strategy", "unknown")
            result.pairs_by_strategy[strat] = result.pairs_by_strategy.get(strat, 0) + 1

        result.completed_at = time.time()

        self._log("bootstrap.complete", result.to_dict())
        return result

    def _scan_documents(self) -> list[dict[str, Any]]:
        """Scan the knowledge directory for documents."""
        docs: list[dict[str, Any]] = []

        # Look for .md and .txt files
        for ext in ("*.md", "*.txt", "*.json"):
            for path in self._knowledge_dir.rglob(ext):
                try:
                    content = path.read_text(encoding="utf-8")
                    if not content.strip():
                        continue

                    # Extract title from filename or first heading
                    title = path.stem.replace("_", " ").title()
                    if content.startswith("#"):
                        first_line = content.split("\n")[0]
                        title = first_line.lstrip("# ").strip()

                    # Determine category from path
                    rel_path = path.relative_to(self._knowledge_dir)
                    parts = rel_path.parts
                    category = parts[0] if len(parts) > 1 else "general"

                    docs.append({
                        "title": title,
                        "content": content,
                        "path": str(path),
                        "category": category,
                    })
                except Exception:
                    continue

        return docs

    def _convert_document(self, doc: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert a single document into training pairs.

        Uses multiple strategies to generate diverse training data.
        """
        pairs: list[dict[str, Any]] = []
        title = doc["title"]
        content = doc["content"]
        category = doc["category"]

        # Strategy 1: Title → Content (always)
        pairs.append({
            "prompt": f"Explain {title}.",
            "response": content[:2000],  # cap response length
            "category": self._map_category(category),
            "strategy": "title_to_content",
            "quality_score": 0.5,
            "source_id": doc["path"],
        })

        # Strategy 2: Question → Answer (if model available)
        if self.model is not None and len(pairs) < self.max_pairs_per_doc:
            qa_pairs = self._generate_qa_pairs(title, content, category)
            pairs.extend(qa_pairs)

        # Strategy 3: Summary → Detail (heuristic, no model needed)
        if len(pairs) < self.max_pairs_per_doc:
            summary = self._extract_summary(content)
            if summary and summary != content[:200]:
                pairs.append({
                    "prompt": f"Summarize {title}.",
                    "response": summary,
                    "category": self._map_category(category),
                    "strategy": "summary_to_detail",
                    "quality_score": 0.4,
                    "source_id": doc["path"],
                })

        # Strategy 4: Code → Explanation (for code-heavy docs)
        if len(pairs) < self.max_pairs_per_doc:
            code_blocks = self._extract_code_blocks(content)
            for block in code_blocks[:1]:  # one per doc
                pairs.append({
                    "prompt": f"What does this code do?\n```\n{block[:500]}\n```",
                    "response": f"This code is from {title}. It demonstrates "
                                f"concepts related to {category}.",
                    "category": "coding",
                    "strategy": "code_to_explanation",
                    "quality_score": 0.3,
                    "source_id": doc["path"],
                })

        # Strategy 5: Cross-domain reasoning (if content has lists/structures)
        if len(pairs) < self.max_pairs_per_doc:
            reasoning = self._generate_reasoning_pair(title, content, category)
            if reasoning:
                pairs.append(reasoning)

        return pairs[:self.max_pairs_per_doc]

    def _generate_qa_pairs(
        self, title: str, content: str, category: str
    ) -> list[dict[str, Any]]:
        """Generate question-answer pairs using the model."""
        pairs: list[dict[str, Any]] = []

        # Use the model to generate questions about the content
        prompt = (
            f"Based on this document about {title}:\n"
            f"{content[:1500]}\n\n"
            "Generate 2 specific questions that can be answered from this "
            "content. Output as a JSON array of question strings."
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": QA_GEN_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
                timeout=60.0,
            )
            questions = self._parse_json_array(completion.text)
            for q in questions[:2]:
                if isinstance(q, str) and len(q) > 10:
                    pairs.append({
                        "prompt": q,
                        "response": content[:1500],
                        "category": self._map_category(category),
                        "strategy": "question_to_answer",
                        "quality_score": 0.6,
                        "source_id": f"generated:{title}",
                    })
        except Exception:
            pass

        return pairs

    def _extract_summary(self, content: str) -> str:
        """Extract a summary from content (first paragraph or first few lines)."""
        lines = content.strip().split("\n")
        # Skip title and find first substantive paragraph
        summary_lines: list[str] = []
        in_paragraph = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_paragraph and summary_lines:
                    break
                continue
            if stripped.startswith("#"):
                continue
            summary_lines.append(stripped)
            in_paragraph = True
            if len(summary_lines) >= 3:
                break
        return " ".join(summary_lines) if summary_lines else ""

    def _extract_code_blocks(self, content: str) -> list[str]:
        """Extract code blocks from markdown content."""
        blocks: list[str] = []
        in_block = False
        current: list[str] = []
        for line in content.split("\n"):
            if line.startswith("```"):
                if in_block:
                    blocks.append("\n".join(current))
                    current = []
                    in_block = False
                else:
                    in_block = True
            elif in_block:
                current.append(line)
        return blocks

    def _generate_reasoning_pair(
        self, title: str, content: str, category: str
    ) -> dict[str, Any] | None:
        """Generate a reasoning training pair from structured content."""
        # Look for lists or comparisons in the content
        list_items = re.findall(r"^[-*]\s+(.+)$", content, re.MULTILINE)
        if len(list_items) < 3:
            return None

        prompt = f"What are the key aspects of {title}?"
        response = "\n".join(f"- {item}" for item in list_items[:10])
        return {
            "prompt": prompt,
            "response": response,
            "category": "reasoning",
            "strategy": "structured_reasoning",
            "quality_score": 0.4,
            "source_id": f"reasoning:{title}",
        }

    def _map_category(self, domain: str) -> str:
        """Map a knowledge domain to a training category."""
        domain_lower = domain.lower()
        coding_domains = {"computing", "programming", "software", "code"}
        reasoning_domains = {"mathematics", "logic", "philosophy"}
        knowledge_domains = {"science", "history", "geography"}

        if any(d in domain_lower for d in coding_domains):
            return "coding"
        if any(d in domain_lower for d in reasoning_domains):
            return "reasoning"
        return "knowledge"

    def _write_pairs(self, pairs: list[dict[str, Any]]) -> int:
        """Write training pairs to the distillation queue."""
        try:
            from .distillation import TrainingPair
            self._queue_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing to avoid duplicates
            existing_hashes: set[str] = set()
            if self._queue_path.exists():
                for line in self._queue_path.read_text(encoding="utf-8").splitlines():
                    try:
                        data = json.loads(line)
                        existing_hashes.add(data.get("pair_hash", ""))
                    except json.JSONDecodeError:
                        continue

            written = 0
            with open(self._queue_path, "a", encoding="utf-8") as f:
                for p in pairs:
                    tp = TrainingPair(
                        prompt=p["prompt"],
                        response=p["response"],
                        category=p.get("category", "general"),
                        quality_score=p.get("quality_score", 0.5),
                        source_id=p.get("source_id", "bootstrap"),
                    )
                    if tp.pair_hash in existing_hashes:
                        continue
                    f.write(json.dumps(tp.to_dict()) + "\n")
                    existing_hashes.add(tp.pair_hash)
                    written += 1

            return written
        except Exception:
            return 0

    def _parse_json_array(self, text: str) -> list[Any]:
        """Extract a JSON array from text."""
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = text.replace("```", "")
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            data = json.loads(text[start:end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# --------------------------------------------------------------- prompt

QA_GEN_SYSTEM = """\
You are generating questions for a knowledge base. The questions should be \
specific, answerable from the provided content, and cover different aspects \
of the topic. Output a valid JSON array of question strings.
"""
