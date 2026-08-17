#!/usr/bin/env python3
"""Test parser with the actual model output format."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.skills import parse_project_proposal

# Actual output from qwen2.5-coder:7b in loop context
raw = """```python
# FILE: main.py
def parse_csv_line(line, delimiter=','):
    import helpers
    fields = []
    in_quotes = False
    current_field = ''
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == delimiter and not in_quotes:
            fields.append(helpers.strip_quotes(current_field))
            current_field = ''
        else:
            current_field += char
    
    fields.append(helpers.strip_quotes(current_field))
    return fields

# FILE: helpers.py
def strip_quotes(field):
    if field.startswith('"') and field.endswith('"'):
        return field[1:-1]
    return field

# TESTS
from main import parse_csv_line
from helpers import strip_quotes

_r = parse_csv_line('field1,"field2,with,commas","field3"')
print("actual: " + str(_r))
assert _r == ['field1', 'field2,with,commas', 'field3']
print("TESTS PASSED")
```"""

code, tests, files = parse_project_proposal(raw)
print("=== PARSED RESULT ===")
print(f"MAIN CODE ({len(code)} chars):")
print(code)
print(f"\nTESTS ({len(tests)} chars):")
print(tests)
print(f"\nEXTRA FILES: {list(files.keys())}")
for k, v in files.items():
    print(f"  {k} ({len(v)} chars):")
    print(f"    {v}")
