#!/usr/bin/env python3
"""Export the evidence ledger as a fine-tuning training corpus."""
import sys
sys.path.insert(0, ".")
import json
from pathlib import Path
from anubis.ledger import Ledger
from anubis.skills import SkillLibrary

ROOT = Path(".")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
library = SkillLibrary(ROOT / "skills")

print("=== TRAINING CORPUS EXPORT ===")
print()

# 1. Export ledger entries as training exemplars
training_records = list(ledger.training_records())
print(f"Ledger entries: {ledger.length}")
print(f"Training exemplars: {len(training_records)}")
print()

# 2. Build the training corpus
corpus = {
    "metadata": {
        "system": "SIOS ANUBIS",
        "exported_from": "evidence ledger",
        "total_ledger_entries": ledger.length,
        "total_training_exemplars": len(training_records),
        "format": "instruction-completion pairs for fine-tuning",
    },
    "exemplars": [],
}

for record in training_records:
    exemplar = {
        "instruction": record.get("task", ""),
        "completion": record.get("code", ""),
        "metadata": {
            "skill_name": record.get("skill_name", ""),
            "attempt": record.get("attempt", 0),
            "passed": record.get("passed", False),
            "model": record.get("model", ""),
            "failure_reason": record.get("failure_reason", ""),
        },
    }
    if exemplar["instruction"] and exemplar["completion"]:
        corpus["exemplars"].append(exemplar)

# 3. Add skill library as additional training data
skills_data = []
for s in library.iter_current():
    skill_data = {
        "instruction": f"Write a function called {s.name}",
        "completion": s.code,
        "metadata": {
            "skill_name": s.name,
            "version": s.version,
            "model": s.provenance.model,
            "attempt": s.provenance.attempt,
            "hash": s.artifact_hash[:24],
            "type": "promoted_skill",
        },
    }
    skills_data.append(skill_data)

corpus["skills"] = skills_data
corpus["metadata"]["total_promoted_skills"] = len(skills_data)

# 4. Write the corpus
output_path = ROOT / "evidence" / "training_corpus.json"
with open(output_path, "w") as f:
    json.dump(corpus, f, indent=2, ensure_ascii=False)

print(f"Training corpus written to: {output_path}")
print(f"  Total exemplars: {len(corpus['exemplars'])}")
print(f"  Promoted skills: {len(skills_data)}")
print()

# 5. Show sample exemplars
print("--- Sample Exemplars ---")
for ex in corpus["exemplars"][:3]:
    print(f"  Task: {ex['instruction'][:80]}")
    print(f"  Passed: {ex['metadata']['passed']}")
    print(f"  Model: {ex['metadata']['model']}")
    print()

print("--- Sample Skills ---")
for sk in skills_data[:3]:
    print(f"  {sk['metadata']['skill_name']} v{sk['metadata']['version']}")
    print(f"    Code length: {len(sk['completion'])} chars")
    print()

# 6. Stats
print("=== CORPUS STATS ===")
passed = sum(1 for e in corpus["exemplars"] if e["metadata"]["passed"])
failed = sum(1 for e in corpus["exemplars"] if not e["metadata"]["passed"])
print(f"  Passed exemplars: {passed}")
print(f"  Failed exemplars: {failed}")
print(f"  Promoted skills: {len(skills_data)}")
print(f"  Total training pairs: {len(corpus['exemplars']) + len(skills_data)}")
print()
print("This corpus can be used to fine-tune ANUBIS on his own history.")
print("Format: instruction-completion pairs compatible with LoRA/QLoRA fine-tuning.")
