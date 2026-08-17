#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.skills import SkillLibrary
lib = SkillLibrary(Path("skills"))
names = lib.names()
print(f"Skills: {len(names)}")
