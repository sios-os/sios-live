_r = std_deviation([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 1.4142135623730951

_r = std_deviation([10, 12, 23, 23, 16, 23, 21, 16])
print("actual: " + str(_r))
assert _r == 4.898979485566356

_r = std_deviation([])
print("actual: " + str(_r))
assert _r == 0.0

print("TESTS PASSED")