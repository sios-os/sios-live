_r = range_list([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 4

_r = range_list([-5, -1, 0, 3, 9])
print("actual: " + str(_r))
assert _r == 14

_r = range_list([10])
print("actual: " + str(_r))
assert _r == 0

_r = range_list([])
print("actual: " + str(_r))
assert _r is None

print("TESTS PASSED")