"""Persistent mission queue — ANUBIS works through missions while you're away.

Missions are persisted to disk so they survive restarts. ANUBIS can:
  - Add missions to the queue
  - Process them one at a time
  - Pause and resume
  - Skip missions that are already in the skill library

This enables autonomous work: you queue up 20 missions before bed,
and ANUBIS works through them overnight, promoting only what passes.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QueuedMission:
    mission_id: str
    skill_name: str
    task: str
    status: str = "pending"  # pending, running, completed, failed, skipped
    added_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    result: str = ""
    error: str = ""


class MissionQueue:
    """Persistent mission queue for autonomous work."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._queue_file = self.root / "mission_queue.json"
        self._missions: list[QueuedMission] = []
        self._load()

    def _load(self) -> None:
        if self._queue_file.exists():
            data = json.loads(self._queue_file.read_text(encoding="utf-8"))
            for m in data:
                self._missions.append(QueuedMission(
                    mission_id=m.get("mission_id", ""),
                    skill_name=m.get("skill_name", ""),
                    task=m.get("task", ""),
                    status=m.get("status", "pending"),
                    added_at=m.get("added_at", 0),
                    started_at=m.get("started_at", 0),
                    completed_at=m.get("completed_at", 0),
                    result=m.get("result", ""),
                    error=m.get("error", ""),
                ))

    def _save(self) -> None:
        self._queue_file.write_text(
            json.dumps([
                {
                    "mission_id": m.mission_id,
                    "skill_name": m.skill_name,
                    "task": m.task,
                    "status": m.status,
                    "added_at": m.added_at,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                    "result": m.result,
                    "error": m.error,
                }
                for m in self._missions
            ], indent=2),
            encoding="utf-8",
        )

    def add(self, skill_name: str, task: str) -> str:
        """Add a mission to the queue."""
        import hashlib
        mid = hashlib.sha256(f"{skill_name}:{task}:{time.time()}".encode()).hexdigest()[:16]
        mission = QueuedMission(
            mission_id=mid,
            skill_name=skill_name,
            task=task,
            added_at=time.time(),
        )
        self._missions.append(mission)
        self._save()
        return mid

    def add_batch(self, missions: list[tuple[str, str]]) -> list[str]:
        """Add multiple missions. Returns list of mission IDs."""
        ids = []
        for skill_name, task in missions:
            mid = self.add(skill_name, task)
            ids.append(mid)
        return ids

    def next_pending(self) -> QueuedMission | None:
        """Get the next pending mission."""
        for m in self._missions:
            if m.status == "pending":
                return m
        return None

    def mark_running(self, mission_id: str) -> None:
        for m in self._missions:
            if m.mission_id == mission_id:
                m.status = "running"
                m.started_at = time.time()
                self._save()
                return

    def mark_completed(self, mission_id: str, result: str = "") -> None:
        for m in self._missions:
            if m.mission_id == mission_id:
                m.status = "completed"
                m.completed_at = time.time()
                m.result = result
                self._save()
                return

    def mark_failed(self, mission_id: str, error: str = "") -> None:
        for m in self._missions:
            if m.mission_id == mission_id:
                m.status = "failed"
                m.completed_at = time.time()
                m.error = error
                self._save()
                return

    def mark_skipped(self, mission_id: str) -> None:
        for m in self._missions:
            if m.mission_id == mission_id:
                m.status = "skipped"
                m.completed_at = time.time()
                self._save()
                return

    def stats(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for m in self._missions:
            counts[m.status] = counts.get(m.status, 0) + 1
        return {
            "total": len(self._missions),
            "by_status": counts,
            "pending": counts.get("pending", 0),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
        }

    def all_missions(self) -> list[QueuedMission]:
        return list(self._missions)

    def clear_completed(self) -> int:
        """Remove completed/failed/skipped missions. Returns count removed."""
        before = len(self._missions)
        self._missions = [m for m in self._missions if m.status == "pending" or m.status == "running"]
        removed = before - len(self._missions)
        self._save()
        return removed
