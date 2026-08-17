#!/usr/bin/env python3
"""Curate ANUBIS persistent memory — review and organize."""
import sys
sys.path.insert(0, ".")
import json
from pathlib import Path

ROOT = Path("memory")

print("=== MEMORY CURATION ===")
print()

# 1. Facts
print("--- Facts ---")
facts_path = ROOT / "facts.json"
if facts_path.exists():
    raw = json.loads(facts_path.read_text())
    # Normalize to list of dicts
    if isinstance(raw, dict):
        facts = [{"key": k, "value": v} for k, v in raw.items()]
    elif isinstance(raw, list):
        facts = raw
    else:
        facts = []
    print(f"  Total facts: {len(facts)}")
    for i, f in enumerate(facts[:10]):
        if isinstance(f, dict):
            print(f"    {i+1}. {f.get('key', '?')}: {str(f.get('value', ''))[:80]}")
        else:
            print(f"    {i+1}. {str(f)[:80]}")
    if len(facts) > 10:
        print(f"    ... and {len(facts) - 10} more")
else:
    facts = []
    print("  No facts file")
print()

# 2. Conversations
print("--- Conversations ---")
conv_path = ROOT / "conversation.jsonl"
if conv_path.exists():
    lines = conv_path.read_text().strip().splitlines()
    print(f"  Total conversation entries: {len(lines)}")
    # Show last few
    for line in lines[-3:]:
        try:
            entry = json.loads(line)
            role = entry.get("role", "?")
            content = entry.get("content", "")[:80]
            print(f"    [{role}] {content}")
        except:
            pass
else:
    print("  No conversation file")
print()

# 3. Missions
print("--- Mission History ---")
missions_path = ROOT / "missions.jsonl"
if missions_path.exists():
    lines = missions_path.read_text().strip().splitlines()
    print(f"  Total mission records: {len(lines)}")
    success = 0
    failed = 0
    for line in lines:
        try:
            m = json.loads(line)
            if m.get("success"):
                success += 1
            else:
                failed += 1
        except:
            pass
    print(f"  Successful: {success}")
    print(f"  Failed: {failed}")
    # Show last few
    for line in lines[-3:]:
        try:
            m = json.loads(line)
            status = "SUCCESS" if m.get("success") else "FAILED"
            print(f"    [{status}] {m.get('skill_name', '?')}: {m.get('task', '')[:60]}")
        except:
            pass
else:
    print("  No missions file")
print()

# 4. Add curated facts about the current system state
print("--- Adding Curated Facts ---")
new_facts = [
    {"key": "creator_name", "value": "Storm", "category": "identity"},
    {"key": "creator_enrolled", "value": True, "category": "identity"},
    {"key": "successor_name", "value": "Ethan Pace", "category": "identity"},
    {"key": "successor_relationship", "value": "Family", "category": "identity"},
    {"key": "knowledge_docs", "value": 550, "category": "knowledge"},
    {"key": "knowledge_claims", "value": 15677, "category": "knowledge"},
    {"key": "knowledge_directors", "value": 14, "category": "knowledge"},
    {"key": "knowledge_specialties", "value": 268, "category": "knowledge"},
    {"key": "skills_count", "value": 23, "category": "capabilities"},
    {"key": "semantic_search", "value": True, "category": "intelligence"},
    {"key": "embedding_model", "value": "nomic-embed-text", "category": "intelligence"},
    {"key": "embedding_dim", "value": 768, "category": "intelligence"},
    {"key": "court_reviews", "value": 1, "category": "governance"},
    {"key": "court_model_upgrade", "value": "qwen2.5-coder:14b on probation", "category": "governance"},
    {"key": "policy_mandates", "value": 3, "category": "governance"},
    {"key": "ledger_entries", "value": 247, "category": "governance"},
    {"key": "training_corpus_size", "value": 49, "category": "training"},
]

# Merge with existing facts
existing_facts = facts if facts else []
existing_keys = {f.get("key") for f in existing_facts if isinstance(f, dict)}
# Add only new facts
for nf in new_facts:
    if nf["key"] not in existing_keys:
        existing_facts.append(nf)
        print(f"  + {nf['key']}: {nf['value']}")
    else:
        # Update existing
        for f in existing_facts:
            if isinstance(f, dict) and f.get("key") == nf["key"]:
                f["value"] = nf["value"]
                f["category"] = nf["category"]
                break
        print(f"  ~ {nf['key']}: {nf['value']} (updated)")

facts_path.write_text(json.dumps(existing_facts, indent=2))
print()
print(f"  Total curated facts: {len(existing_facts)}")
print()

print("=== MEMORY CURATION COMPLETE ===")
