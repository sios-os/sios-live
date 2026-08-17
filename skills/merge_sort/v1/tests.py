_r = merge_sort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5])
print("actual: " + str(_r))
assert _r == [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]

_r = merge_sort([])
print("actual: " + str(_r))
assert _r == []

_r = merge_sort([7])
print("actual: " + str(_r))
assert _r == [7]

_r = merge_sort([-3, -1, -4, -1, -5, -9, -2, -6, -5, -3, -5])
print("actual: " + str(_r))
assert _r == [-9, -6, -5, -5, -5, -4, -3, -3, -2, -1, -1]

print("TESTS PASSED")