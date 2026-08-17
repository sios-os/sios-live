"""Tamper-evident evidence ledger.

Book II doctrine requires audit to be mandatory and non-waivable. Book 15
requires that "definition of done requires reproducible evidence, not a
demonstration or assertion."

Implementation: append-only JSONL with a SHA-256 hash chain. Each entry binds
the hash of its own canonical payload to the hash of the previous entry, so any
edit, deletion, or reordering of history breaks verification at that point and
every point after it.

This ledger is also, deliberately, a training corpus. Each self-development
attempt records the task, the reasoning, the code produced, and whether it
passed -- which is exactly the shape needed to fine-tune ANUBIS on his own
history once sufficient VRAM is available.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

GENESIS_HASH = "0" * 64


def _canonical(obj: Any) -> bytes:
    """Deterministic serialization. Key order and separators are fixed so the
    same logical content always hashes identically."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Entry:
    seq: int
    ts: float
    actor: str
    action: str
    payload: dict[str, Any]
    payload_hash: str
    prev_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "ts": self.ts,
            "actor": self.actor,
            "action": self.action,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
        }

    @staticmethod
    def compute_hash(
        seq: int, ts: float, actor: str, action: str, payload_hash: str, prev_hash: str
    ) -> str:
        return _sha256(
            _canonical(
                {
                    "seq": seq,
                    "ts": ts,
                    "actor": actor,
                    "action": action,
                    "payload_hash": payload_hash,
                    "prev_hash": prev_hash,
                }
            )
        )


class VerificationError(Exception):
    """Raised when the ledger's hash chain does not verify."""


class Ledger:
    """Append-only hash-chained ledger.

    Thread-safe. Durability uses flush + fsync so an entry that has been
    acknowledged survives power loss -- Book 07 requires no silent data loss.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq, self._head = self._recover()

    # ---------------------------------------------------------------- state

    def _recover(self) -> tuple[int, str]:
        """Read the tail to establish current sequence and head hash."""
        if not self.path.exists():
            return -1, GENESIS_HASH
        seq, head = -1, GENESIS_HASH
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                seq, head = rec["seq"], rec["entry_hash"]
        return seq, head

    @property
    def head(self) -> str:
        return self._head

    @property
    def length(self) -> int:
        return self._seq + 1

    # ---------------------------------------------------------------- write

    def append(self, actor: str, action: str, payload: dict[str, Any]) -> Entry:
        with self._lock:
            seq = self._seq + 1
            ts = time.time()
            payload_hash = _sha256(_canonical(payload))
            prev_hash = self._head
            entry_hash = Entry.compute_hash(
                seq, ts, actor, action, payload_hash, prev_hash
            )
            entry = Entry(
                seq=seq,
                ts=ts,
                actor=actor,
                action=action,
                payload=payload,
                payload_hash=payload_hash,
                prev_hash=prev_hash,
                entry_hash=entry_hash,
            )
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry.to_dict(), ensure_ascii=False, default=str) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            self._seq, self._head = seq, entry_hash
            return entry

    # ----------------------------------------------------------------- read

    def __iter__(self) -> Iterator[Entry]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                yield Entry(
                    seq=rec["seq"],
                    ts=rec["ts"],
                    actor=rec["actor"],
                    action=rec["action"],
                    payload=rec["payload"],
                    payload_hash=rec["payload_hash"],
                    prev_hash=rec["prev_hash"],
                    entry_hash=rec["entry_hash"],
                )

    def verify(self) -> tuple[bool, str]:
        """Verify the full chain.

        Returns (ok, message). On failure the message names the first bad
        sequence number, so corruption can be localized rather than merely
        detected.
        """
        expected_prev = GENESIS_HASH
        expected_seq = 0
        count = 0

        for entry in self:
            if entry.seq != expected_seq:
                return False, (
                    f"sequence break at {entry.seq}: expected {expected_seq}"
                )
            recomputed_payload = _sha256(_canonical(entry.payload))
            if recomputed_payload != entry.payload_hash:
                return False, (
                    f"payload altered at seq {entry.seq}: "
                    f"stored={entry.payload_hash[:12]} actual={recomputed_payload[:12]}"
                )
            if entry.prev_hash != expected_prev:
                return False, (
                    f"chain break at seq {entry.seq}: "
                    f"prev={entry.prev_hash[:12]} expected={expected_prev[:12]}"
                )
            recomputed_entry = Entry.compute_hash(
                entry.seq,
                entry.ts,
                entry.actor,
                entry.action,
                entry.payload_hash,
                entry.prev_hash,
            )
            if recomputed_entry != entry.entry_hash:
                return False, f"entry hash mismatch at seq {entry.seq}"

            expected_prev = entry.entry_hash
            expected_seq += 1
            count += 1

        return True, f"chain verified: {count} entries, head={expected_prev[:12]}"

    # ------------------------------------------------------------- analysis

    def training_records(self) -> Iterator[dict[str, Any]]:
        """Yield successful self-development attempts as fine-tuning samples.

        Only promoted skills are emitted: these are attempts that were gated,
        executed, tested, and accepted -- i.e. verified-good behavior. Failed
        attempts stay in the ledger for audit but are not presented as
        exemplars to learn from.
        """
        for entry in self:
            if entry.action != "skill.promoted":
                continue
            p = entry.payload
            task = p.get("task")
            code = p.get("code")
            if not task or not code:
                continue
            yield {
                "seq": entry.seq,
                "task": task,
                "code": code,
                "reasoning": p.get("reasoning", ""),
                "skill": p.get("name"),
                "evidence_hash": entry.payload_hash,
            }
