#!/usr/bin/env python3
"""List Mind & Behavior specialty IDs."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry
r = Registry(Path("registry"))
for s in r.specialties_by_director("mind"):
    print(f"{s.specialty_id}: {s.canonical_name}")
