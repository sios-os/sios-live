_r = average_list([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == 3.0

_r = average_list([])
print("actual: " + str(_r))
assert _r == 0

_r = average_list([-10, 10])
print("actual: " + str(_r))
assert _r == 0

print("TESTS PASSED")