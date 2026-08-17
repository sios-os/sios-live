#!/usr/bin/env python3
"""Test documentation generation and backup."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.docs import DocGenerator
from anubis.backup import BackupManager

ROOT = Path(".")

# Generate docs
print("=== DOCUMENTATION GENERATION ===")
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
registry = Registry(ROOT / "registry")
kb = KnowledgeBase(ROOT / "knowledge", registry)

gen = DocGenerator(library, ledger, kb, registry)
files = gen.generate_all(ROOT / "docs")
print(f"Generated {len(files)} documentation files:")
for fname, path in files.items():
    size = Path(path).stat().st_size
    print(f"  {fname}: {size} bytes")
print()

# Create backup
print("=== BACKUP ===")
backup = BackupManager(ROOT, ROOT / "backups")
result = backup.create_backup(label="full_system")
print(f"Backup created: {result['backup_path']}")
print(f"  Size: {result['size_mb']} MB")
print(f"  Checksum: {result['checksum'][:24]}...")
print(f"  Dirs: {', '.join(result['dirs'])}")
print()

# List backups
print("--- Available Backups ---")
for b in backup.list_backups():
    print(f"  {b['name']}: {b['size_mb']} MB, label='{b['label']}'")
print()

print("=== DONE ===")
