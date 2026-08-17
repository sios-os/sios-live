_r = min_in_list([3, 1, 4, 1, 5, 9])
print("actual: " + str(_r))
assert _r == 1

_r = min_in_list([-2, -5, -3, -8, -6])
print("actual: " + str(_r))
assert _r == -8

_r = min_in_list([])
print("actual: " + str(_r))
assert _r is None

print("TESTS PASSED")