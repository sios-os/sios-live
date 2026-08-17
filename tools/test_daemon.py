#!/usr/bin/env python3
"""Quick test of the ANUBIS daemon initialization."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.anubis_daemon import AnubisDaemon

d = AnubisDaemon()
print("daemon init OK")
print(f"skills: {len(d.library.names())}")
print(f"ledger: {d.ledger.length}")
print(f"sandbox: {d.sandbox.describe()}")
health = d._check_model()
print(f"model present: {health.get('model_present', False)}")
if health.get("model_present"):
    print(f"model: {health.get('model')}")
