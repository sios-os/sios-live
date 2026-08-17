#!/usr/bin/env python3
"""List all knowledge directors and their specialties."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.registry import Registry

r = Registry(Path("registry"))
for d in r.directors():
    specs = r.specialties_by_director(d.director_id)
    print(f"\n{d.name} ({len(specs)} specialties)")
    print(f"  {d.description}")
    print(f"  Charter: {d.charter}")
    for s in specs[:15]:
        print(f"    - {s.canonical_name}")
    if len(specs) > 15:
        print(f"    ... and {len(specs) - 15} more")
