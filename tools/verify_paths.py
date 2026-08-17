#!/usr/bin/env python3
"""Verify daemon path resolution."""
import sys
from pathlib import Path

# Simulate what the daemon does
ROOT = Path(__file__).resolve().parents[1]
print(f"ROOT: {ROOT}")
print(f"knowledge exists: {(ROOT / 'knowledge').exists()}")
print(f"skills exists: {(ROOT / 'skills').exists()}")
print(f"identity exists: {(ROOT / 'identity').exists()}")
print(f"evidence exists: {(ROOT / 'evidence').exists()}")
print(f"registry exists: {(ROOT / 'registry').exists()}")
print(f"court exists: {(ROOT / 'court').exists()}")
print(f"policy exists: {(ROOT / 'policy').exists()}")
print(f"memory exists: {(ROOT / 'memory').exists()}")
print(f"mission_queue exists: {(ROOT / 'mission_queue').exists()}")
