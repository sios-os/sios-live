#!/usr/bin/env python3
"""List Health & Medicine specialty IDs."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry
r = Registry(Path("registry"))
for d in r.directors():
    if "health" in d.director_id.lower() or "medic" in d.director_id.lower():
        print(f"Director: {d.director_id}: {d.name}")
        specs = r.specialties_by_director(d.director_id)
        for s in specs:
            print(f"  {s.specialty_id}: {s.canonical_name}")
        print(f"  Total: {len(specs)}")
