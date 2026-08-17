#!/usr/bin/env python3
"""Test the persistent mission queue with autonomous work."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.queue import MissionQueue
from anubis.loop import SelfDevelopmentLoop
from anubis.model import OllamaAdapter
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.sandbox import Sandbox, SandboxPolicy

ROOT = Path(".")
queue = MissionQueue(ROOT / "mission_queue")

print("=== MISSION QUEUE TEST ===")
print()

# Clear old entries
removed = queue.clear_completed()
print(f"Cleared {removed} old entries")
print()

# Add a batch of missions
MISSIONS = [
    ("power_of_two", "Write a function that returns 2 raised to the power n"),
    ("is_perfect_square", "Write a function that checks if a number is a perfect square"),
    ("sum_of_digits", "Write a function that sums the digits of an integer"),
    ("collatz_steps", "Write a function that returns the number of Collatz conjecture steps to reach 1"),
    ("is_armstrong", "Write a function that checks if a number is an Armstrong number"),
]

print("--- Adding missions to queue ---")
ids = queue.add_batch(MISSIONS)
print(f"  Added {len(ids)} missions")
print()

# Show queue stats
stats = queue.stats()
print(f"  Queue stats: {stats}")
print()

# Process the queue
print("--- Processing queue ---")
model = OllamaAdapter("qwen2.5-coder:7b", require_tools=False)
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
sandbox = Sandbox(SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20))
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=3)

existing = set(library.names())
processed = 0
promoted = 0
skipped = 0
failed = 0

while True:
    mission = queue.next_pending()
    if mission is None:
        break

    # Skip if skill already exists
    if mission.skill_name in existing:
        queue.mark_skipped(mission.mission_id)
        skipped += 1
        print(f"  SKIP {mission.skill_name} (already in library)")
        continue

    queue.mark_running(mission.mission_id)
    print(f"  RUNNING {mission.skill_name}...")
    result = loop.run_mission(mission.task, mission.skill_name)

    if result.success:
        queue.mark_completed(mission.mission_id, result=f"promoted v{result.skill.version}")
        promoted += 1
        existing.add(mission.skill_name)
        print(f"    -> PROMOTED (v{result.skill.version})")
    else:
        queue.mark_failed(mission.mission_id, error=result.denied_reason or "failed")
        failed += 1
        print(f"    -> FAILED: {result.denied_reason}")

    processed += 1

print()
print("--- Queue Results ---")
print(f"  Processed: {processed}")
print(f"  Promoted: {promoted}")
print(f"  Skipped: {skipped}")
print(f"  Failed: {failed}")
print()

# Final stats
stats = queue.stats()
print(f"  Final queue stats: {stats}")
print()

# Show all missions
print("--- All Missions ---")
for m in queue.all_missions():
    print(f"  {m.skill_name:20s} {m.status:10s} {m.result or m.error}")
print()

print(f"  Total skills in library: {len(library.names())}")
print()
print("=== MISSION QUEUE TEST COMPLETE ===")
