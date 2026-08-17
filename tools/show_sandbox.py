#!/usr/bin/env python3
"""Report exactly what containment the sandbox achieves on this host."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.sandbox import Sandbox, SandboxPolicy  # noqa: E402

sbx = Sandbox(SandboxPolicy())
print(sbx.describe())
print()
for field_name, value in vars(sbx.isolation).items():
    print(f"  {field_name:<32} {value}")
print()

r = sbx.run_source("import os; print('uid', os.getuid(), 'euid', os.geteuid())")
print(f"probe run: {r.summary()}")
print(f"  stdout: {r.stdout.strip()}")
if r.stderr.strip():
    print(f"  stderr: {r.stderr.strip()[:300]}")
print(f"  fully_isolated: {r.fully_isolated}")
