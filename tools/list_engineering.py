#!/usr/bin/env python3
"""List Engineering & Design specialty IDs."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry
r = Registry(Path("registry"))
specs = r.specialties_by_director("engineering")
for s in specs:
    print(f"{s.specialty_id}: {s.canonical_name}")
print(f"Total: {len(specs)}")
