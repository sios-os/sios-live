_r = chunk_list_size([1, 2, 3, 4, 5], 2)
print("actual: " + str(_r))
assert _r == [[1, 2], [3, 4], [5]], "Test with normal case failed"

_r = chunk_list_size([], 3)
print("actual: " + str(_r))
assert _r == [], "Test with empty list failed"

try:
    _r = chunk_list_size([1, 2, 3], -1)
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Size must be greater than 0", "Test with error case failed"

print("TESTS PASSED")