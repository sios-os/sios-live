_r = matrix_transpose([[1, 3], [2, 4]])
print("actual: " + str(_r))
assert _r == [[1, 2], [3, 4]], "Test case 1 failed"

_r = matrix_transpose([[1, 4], [2, 5], [3, 6]])
print("actual: " + str(_r))
assert _r == [[1, 2, 3], [4, 5, 6]], "Test case 2 failed"

_r = matrix_transpose([])
print("actual: " + str(_r))
assert _r == [], "Test case 3 failed"

print("TESTS PASSED")