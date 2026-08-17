_r = unique_preserve_order([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5], "Test with no duplicates failed"

_r = unique_preserve_order([1, 2, 2, 3, 4, 4, 5])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5], "Test with duplicates failed"

_r = unique_preserve_order([])
print("actual: " + str(_r))
assert _r == [], "Test with empty list failed"

print("TESTS PASSED")