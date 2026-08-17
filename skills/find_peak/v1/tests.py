_r = find_peak([1, 3, 20, 4, 1, 0])
print("actual: " + str(_r))
assert _r == 20

_r = find_peak([10, 20, 15, 2, 23, 90, 67])
print("actual: " + str(_r))
assert _r == 20 or _r == 90

_r = find_peak([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 5

_r = find_peak([5, 4, 3, 2, 1])
print("actual: " + str(_r))
assert _r == 5

_r = find_peak([100])
print("actual: " + str(_r))
assert _r == 100

print("TESTS PASSED")