#!/usr/bin/env python3
"""Test the multi-file parser."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.skills import parse_project_proposal

# Test with marker format
sample = """<<<FILE: main.py>>>
```python
def hello():
    return 'hi'
```
<<<FILE: helpers.py>>>
```python
def world():
    return 'world'
```
<<<TESTS>>>
```python
from main import hello
from helpers import world
_r = hello()
print('actual:', _r)
assert _r == 'hi'
print('TESTS PASSED')
```
<<<END>>>
"""

code, tests, files = parse_project_proposal(sample)
print("=== Marker format ===")
print(f"CODE: {code[:60]!r}")
print(f"TESTS: {tests[:60]!r}")
print(f"FILES: {list(files.keys())}")
for k, v in files.items():
    print(f"  {k}: {v[:40]!r}")

# Test with markdown format
sample2 = """### FILE: main.py
```python
def hello():
    return 'hi'
```
### FILE: helpers.py
```python
def world():
    return 'world'
```
### TESTS
```python
from main import hello
_r = hello()
assert _r == 'hi'
print('TESTS PASSED')
```
"""

code2, tests2, files2 = parse_project_proposal(sample2)
print("\n=== Markdown format ===")
print(f"CODE: {code2[:60]!r}")
print(f"TESTS: {tests2[:60]!r}")
print(f"FILES: {list(files2.keys())}")
