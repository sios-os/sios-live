#!/usr/bin/env python3
"""Test the knowledge updater with real proposals."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.knowledge import KnowledgeBase
from anubis.registry import Registry
from anubis.knowledge_updater import KnowledgeUpdater

ROOT = Path(".")
registry = Registry(ROOT / "registry")
kb = KnowledgeBase(ROOT / "knowledge", registry)
updater = KnowledgeUpdater(kb, registry)

print("=== KNOWLEDGE UPDATER TEST ===")
print()

# Proposal 1: A well-corroborated document about Python programming
print("--- Proposal 1: Python Programming (should verify) ---")
content1 = """# Python Programming Fundamentals

- Python is a high-level programming language
- Python supports object-oriented programming
- Python uses indentation for code blocks
- Python has a dynamic type system
- Python supports functional programming with lambda functions
- Python includes a standard library with modules for file I/O
- Python is interpreted, not compiled
- Python supports exception handling with try/except blocks
- Python uses garbage collection for memory management
"""
p1 = updater.propose(
    specialty_id="computing_software_engineering",
    title="Python Programming Fundamentals",
    content=content1,
)
print(f"  ID: {p1.proposal_id}")
print(f"  Status: {p1.status}")
print(f"  Claims extracted: {p1.claims_extracted}")
print(f"  Claims verified: {p1.claims_verified}")
if p1.rejection_reason:
    print(f"  Rejection: {p1.rejection_reason}")
print()

# Proposal 2: A document with mostly unique claims
print("--- Proposal 2: Niche Technical Specs (may have low verification) ---")
content2 = """# Retro Microcomputer Specifications

- The ZX-81 microcomputer uses a Z80A CPU running at 3.25 MHz
- The TRS-80 Model I has 4KB of RAM expandable to 48KB
- The Commodore VIC-20 has a 6502 CPU at 1.02 MHz
- The Apple IIe has a 65C02 CPU at 1.023 MHz
- The Atari 800XL has a 6502C CPU at 1.79 MHz
"""
p2 = updater.propose(
    specialty_id="computing_computer_science",
    title="Retro Microcomputer Specifications",
    content=content2,
)
print(f"  ID: {p2.proposal_id}")
print(f"  Status: {p2.status}")
print(f"  Claims extracted: {p2.claims_extracted}")
print(f"  Claims verified: {p2.claims_verified}")
if p2.rejection_reason:
    print(f"  Rejection: {p2.rejection_reason}")
print()

# Try to approve and promote proposal 1
if p1.status == "verified":
    print("--- Approving and promoting Proposal 1 ---")
    ok = updater.approve(p1.proposal_id)
    print(f"  Approved: {ok}")
    result = updater.promote(p1.proposal_id)
    print(f"  Promoted: {result}")
    print()

# Stats
print("--- Updater Stats ---")
stats = updater.stats()
print(f"  Total proposals: {stats['total_proposals']}")
print(f"  Verified: {stats['verified']}")
print(f"  Approved: {stats['approved']}")
print(f"  Promoted: {stats['promoted']}")
print(f"  Rejected: {stats['rejected']}")
print()

print("=== KNOWLEDGE UPDATER TEST COMPLETE ===")
