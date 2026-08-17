#!/usr/bin/env python3
"""Test daemon initialization."""
import sys
sys.path.insert(0, ".")
try:
    from tools.anubis_daemon import AnubisDaemon
    d = AnubisDaemon()
    print("Daemon initialized OK")
    print(f"Registry: {d.registry.stats()}")
    print(f"Knowledge: {d.knowledge.stats()}")
    print(f"Identity: {d.identity.stats()}")
    print(f"Network: {d.network.stats()}")
    print(f"Egyptology: {d.egyptology.stats()}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
