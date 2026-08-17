_r = variance([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 2.0

_r = variance([])
print("actual: " + str(_r))
assert _r is None

_r = variance([10])
print("actual: " + str(_r))
assert _r == 0.0

print("TESTS PASSED")