#!/usr/bin/env python3
"""List Society & Government specialty IDs."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry
r = Registry(Path("registry"))
specs = r.specialties_by_director("society")
for s in specs:
    print(f"{s.specialty_id}: {s.canonical_name}")
print(f"Total: {len(specs)}")
