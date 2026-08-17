_r = median_list([3, 1, 4, 1, 5, 9, 2])
print("actual: " + str(_r))
assert _r == 3

_r = median_list([10, 20, 30, 40, 50])
print("actual: " + str(_r))
assert _r == 30.0

_r = median_list([])
print("actual: " + str(_r))
assert _r is None

print("TESTS PASSED")