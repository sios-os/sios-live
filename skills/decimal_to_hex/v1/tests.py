_r = decimal_to_hex(0)
print("actual: " + _r)
assert _r == "0"

_r = decimal_to_hex(255)
print("actual: " + _r)
assert _r == "FF"

_r = decimal_to_hex(16)
print("actual: " + _r)
assert _r == "10"

print("TESTS PASSED")