_r = sum_list([1, 2, 3])
print("actual: " + str(_r))
assert _r == 6

_r = sum_list([])
print("actual: " + str(_r))
assert _r == 0

_r = sum_list([-1, -2, -3])
print("actual: " + str(_r))
assert _r == -6

print("TESTS PASSED")