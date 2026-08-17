_r = max_in_list([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 5

_r = max_in_list([-5, -2, -8, -1])
print("actual: " + str(_r))
assert _r == -1

_r = max_in_list([])
print("actual: " + str(_r))
assert _r is None

print("TESTS PASSED")