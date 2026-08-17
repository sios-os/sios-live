_r = hex_to_decimal("0")
print("actual: " + str(_r))
assert _r == 0

_r = hex_to_decimal("1A")
print("actual: " + str(_r))
assert _r == 26

_r = hex_to_decimal("FF")
print("actual: " + str(_r))
assert _r == 255

print("TESTS PASSED")