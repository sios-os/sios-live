_r = merge_sorted([1, 3, 5], [2, 4, 6])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5, 6]

_r = merge_sorted([], [1, 2, 3])
print("actual: " + str(_r))
assert _r == [1, 2, 3]

_r = merge_sorted([1, 2, 3], [])
print("actual: " + str(_r))
assert _r == [1, 2, 3]

_r = merge_sorted([], [])
print("actual: " + str(_r))
assert _r == []

print("TESTS PASSED")