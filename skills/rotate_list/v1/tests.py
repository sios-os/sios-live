_r = rotate_list([1, 2, 3, 4, 5], 2)
print("actual: " + str(_r))
assert _r == [4, 5, 1, 2, 3]

_r = rotate_list([1, 2, 3, 4, 5], -2)
print("actual: " + str(_r))
assert _r == [3, 4, 5, 1, 2]

_r = rotate_list([1, 2, 3, 4, 5], 7)
print("actual: " + str(_r))
assert _r == [4, 5, 1, 2, 3]

_r = rotate_list([], 2)
print("actual: " + str(_r))
assert _r == []

print("TESTS PASSED")