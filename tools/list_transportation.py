#!/usr/bin/env python3
"""List Transportation/Trades specialty IDs."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry
r = Registry(Path("registry"))
# Find the director id
for d in r.directors():
    if "transport" in d.director_id.lower() or "trade" in d.director_id.lower():
        print(f"Director: {d.director_id}: {d.name}")
specs = r.specialties_by_director("trades")
for s in specs:
    print(f"{s.specialty_id}: {s.canonical_name}")
print(f"Total: {len(specs)}")
