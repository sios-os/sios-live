_r = binary_to_decimal("0")
print("actual: " + str(_r))
assert _r == 0

_r = binary_to_decimal("1")
print("actual: " + str(_r))
assert _r == 1

_r = binary_to_decimal("1010")
print("actual: " + str(_r))
assert _r == 10

_r = binary_to_decimal("11111111")
print("actual: " + str(_r))
assert _r == 255

print("TESTS PASSED")