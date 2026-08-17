_r = bubble_sort([64, 34, 25, 12, 22, 11, 90])
print("actual: " + str(_r))
assert _r == [11, 12, 22, 25, 34, 64, 90], "Test with normal case failed"

_r = bubble_sort([])
print("actual: " + str(_r))
assert _r == [], "Test with empty list failed"

_r = bubble_sort([1])
print("actual: " + str(_r))
assert _r == [1], "Test with single element list failed"

_r = bubble_sort([3, 2, 1])
print("actual: " + str(_r))
assert _r == [1, 2, 3], "Test with reverse sorted list failed"

_r = bubble_sort([1, 3, 2])
print("actual: " + str(_r))
assert _r == [1, 2, 3], "Test with already sorted list failed"

print("TESTS PASSED")