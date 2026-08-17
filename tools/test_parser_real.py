#!/usr/bin/env python3
"""Test parser with actual model output."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.skills import parse_project_proposal

# Actual output from qwen2.5-coder:7b
raw = """```python
# <<<FILE: main.py>>>
from helpers import strip_quotes

def parse_csv_line(line, delimiter=','):
    result = []
    in_quote = False
    current_field = ''
    
    for char in line:
        if char == '"':
            in_quote = not in_quote
        elif char == delimiter and not in_quote:
            result.append(strip_quotes(current_field))
            current_field = ''
        else:
            current_field += char
    
    result.append(strip_quotes(current_field))
    return result

# <<<FILE: helpers.py>>>
def strip_quotes(field):
    if field.startswith('"') and field.endswith('"'):
        return field[1:-1]
    return field

# <<<TESTS>>>
from main import parse_csv_line
from helpers import strip_quotes

_r = parse_csv_line('field1,"field2,with,comma",field3')
print("actual: " + str(_r))
assert _r == ['field1', 'field2,with,comma', 'field3']
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
    print(f"  {k} ({len(v)} chars): {v[:60]!r}")
