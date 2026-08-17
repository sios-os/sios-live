_r = chunk_list([1, 2, 3, 4, 5, 6, 7], 2)
print("actual: " + str(_r))
assert _r == [[1, 2], [3, 4], [5, 6], [7]], "Test case 1 failed"

_r = chunk_list([1, 2, 3, 4, 5, 6, 7], 3)
print("actual: " + str(_r))
assert _r == [[1, 2, 3], [4, 5, 6], [7]], "Test case 2 failed"

_r = chunk_list([1, 2, 3, 4, 5, 6, 7], 10)
print("actual: " + str(_r))
assert _r == [[1, 2, 3, 4, 5, 6, 7]], "Test case 3 failed"

_r = chunk_list([], 2)
print("actual: " + str(_r))
assert _r == [], "Test case 4 failed"

_r = chunk_list([1], 1)
print("actual: " + str(_r))
assert _r == [[1]], "Test case 5 failed"

try:
    _r = chunk_list([1, 2, 3, 4, 5, 6, 7], 0)
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Size must be greater than 0", "Test case 6 failed"

print("TESTS PASSED")