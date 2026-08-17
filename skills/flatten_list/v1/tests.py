_r = flatten_list([1, [2, 3], [[4, 5], 6]])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5, 6]

_r = flatten_list([[[]], [], [[]]])
print("actual: " + str(_r))
assert _r == []

_r = flatten_list([1, 2, 3])
print("actual: " + str(_r))
assert _r == [1, 2, 3]

print("TESTS PASSED")