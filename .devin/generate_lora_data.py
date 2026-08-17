"""Generate LoRA fine-tune training data from all available sources.

Combines:
1. Constitutional training pairs (laws and governance)
2. Distilled conversation pairs (from evidence ledger)
3. Knowledge bootstrap pairs (from 804 knowledge documents)
4. Dream cycle insights (from dream history)
5. Mission results (from mission archive)

Outputs a single JSONL file ready for LoRA fine-tuning.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

root = Path(".")
output_pairs = []

# 1. Constitutional training pairs
print("=== 1. Constitutional Training Pairs ===")
const_path = root / "memory" / "constitutional_training"
if const_path.exists():
    for f in sorted(const_path.glob("*.jsonl")):
        for line in f.open(encoding="utf-8"):
            pair = json.loads(line)
            output_pairs.append(pair)
    print(f"  Loaded {len(output_pairs)} constitutional pairs")
else:
    print("  No constitutional pairs found — run constitutional_training_export first")

# 2. Distilled conversation pairs
print("=== 2. Distilled Conversation Pairs ===")
distill_count = 0
try:
    from anubis.distillation import KnowledgeDistiller
    distiller = KnowledgeDistiller(root / "memory" / "distillation", ledger=None)
    queue = distiller.load_queue()
    for item in queue:
        pair = {
            "pair_id": item.get("pair_id", ""),
            "messages": [
                {"role": "user", "content": item.get("prompt", "")},
                {"role": "assistant", "content": item.get("response", "")},
            ],
            "category": item.get("category", "general"),
            "source": "distillation",
        }
        output_pairs.append(pair)
        distill_count += 1
    print(f"  Loaded {distill_count} distilled pairs")
except Exception as e:
    print(f"  Distillation error: {e}")

# 3. Knowledge bootstrap pairs
print("=== 3. Knowledge Bootstrap Pairs ===")
bootstrap_count = 0
try:
    from anubis.knowledge_bootstrap import KnowledgeBootstrapper
    bootstrapper = KnowledgeBootstrapper(root)
    pairs = bootstrapper.generate_training_pairs(limit=100)
    for pair in pairs:
        output_pairs.append({
            "pair_id": pair.get("pair_id", ""),
            "messages": [
                {"role": "user", "content": pair.get("prompt", "")},
                {"role": "assistant", "content": pair.get("response", "")},
            ],
            "category": "knowledge",
            "source": "bootstrap",
        })
        bootstrap_count += 1
    print(f"  Loaded {bootstrap_count} knowledge pairs")
except Exception as e:
    print(f"  Knowledge bootstrap error: {e}")

# 4. Dream cycle insights
print("=== 4. Dream Cycle Insights ===")
dream_count = 0
dream_path = root / "memory" / "dream_cycle.json"
if dream_path.exists():
    try:
        dream_data = json.loads(dream_path.read_text(encoding="utf-8"))
        for cycle in dream_data.get("cycles", []):
            for insight in cycle.get("insights", []):
                pair = {
                    "pair_id": f"dream_{cycle.get('cycle_id', '')}_{insight.get('id', '')}",
                    "messages": [
                        {"role": "user", "content": f"What did you learn about {insight.get('area', 'this topic')}?"},
                        {"role": "assistant", "content": insight.get("description", "")},
                    ],
                    "category": "dream_insight",
                    "source": "dream_cycle",
                }
                output_pairs.append(pair)
                dream_count += 1
        print(f"  Loaded {dream_count} dream insight pairs")
    except Exception as e:
        print(f"  Dream cycle error: {e}")
else:
    print("  No dream cycle data found")

# 5. Mission results
print("=== 5. Mission Results ===")
mission_count = 0
mission_path = root / "memory" / "missions.jsonl"
if mission_path.exists():
    try:
        for line in mission_path.open(encoding="utf-8"):
            mission = json.loads(line)
            if mission.get("status") == "completed":
                pair = {
                    "pair_id": f"mission_{mission.get('mission_id', '')}",
                    "messages": [
                        {"role": "user", "content": f"Complete this task: {mission.get('task', '')}"},
                        {"role": "assistant", "content": mission.get("result", mission.get("output", ""))},
                    ],
                    "category": "mission",
                    "source": "mission_archive",
                }
                output_pairs.append(pair)
                mission_count += 1
        print(f"  Loaded {mission_count} mission pairs")
    except Exception as e:
        print(f"  Mission archive error: {e}")
else:
    print("  No mission archive found")

# Write combined output
print()
print("=== Writing Combined Training Data ===")
output_path = root / "memory" / "lora_training_data.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for pair in output_pairs:
        f.write(json.dumps(pair, ensure_ascii=False) + "\n")

print(f"Total training pairs: {len(output_pairs)}")
print(f"Output: {output_path}")
print()

# Summary by source
sources = {}
for p in output_pairs:
    src = p.get("source", "unknown")
    sources[src] = sources.get(src, 0) + 1
print("By source:")
for src, count in sorted(sources.items()):
    print(f"  {src}: {count}")

# Summary by category
cats = {}
for p in output_pairs:
    cat = p.get("category", "unknown")
    cats[cat] = cats.get(cat, 0) + 1
print("By category:")
for cat, count in sorted(cats.items()):
    print(f"  {cat}: {count}")

print()
print("=== LoRA Training Data Generation Complete ===")
print("To fine-tune: use this JSONL with Unsloth or peft on a GPU machine")
print("The actual fine-tune requires Creator approval (MAIN_ENGINE change)")
