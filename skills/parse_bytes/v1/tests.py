# Normal case
_r = parse_bytes("1.5KB")
print("actual:", _r)
assert _r == 1536

# Edge case with no decimal
_r = parse_bytes("2MB")
print("actual:", _r)
assert _r == 2097152

# Error case with invalid unit
try:
    _r = parse_bytes("3XYZ")
except ValueError as e:
    print("caught expected error:", e)

# Error case with no number
try:
    _r = parse_bytes("KB")
except ValueError as e:
    print("caught expected error:", e)

print("TESTS PASSED")