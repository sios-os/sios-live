_r = quick_sort([3, 6, 8, 10, 1, 2, 1])
print("actual: " + str(_r))
assert _r == [1, 1, 2, 3, 6, 8, 10]

_r = quick_sort([])
print("actual: " + str(_r))
assert _r == []

_r = quick_sort([5])
print("actual: " + str(_r))
assert _r == [5]

_r = quick_sort([9, 7, 5, 3, 1])
print("actual: " + str(_r))
assert _r == [1, 3, 5, 7, 9]

print("TESTS PASSED")