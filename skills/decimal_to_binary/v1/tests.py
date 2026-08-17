_r = decimal_to_binary(0)
print("actual: " + _r)
assert _r == "0"

_r = decimal_to_binary(1)
print("actual: " + _r)
assert _r == "1"

_r = decimal_to_binary(2)
print("actual: " + _r)
assert _r == "10"

_r = decimal_to_binary(5)
print("actual: " + _r)
assert _r == "101"

_r = decimal_to_binary(10)
print("actual: " + _r)
assert _r == "1010"

_r = decimal_to_binary(255)
print("actual: " + _r)
assert _r == "11111111"

print("TESTS PASSED")