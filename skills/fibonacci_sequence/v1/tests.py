_r = fibonacci_sequence(5)
print("actual: " + str(_r))
assert _r == [0, 1, 1, 2, 3], "Test case 1 failed"

_r = fibonacci_sequence(1)
print("actual: " + str(_r))
assert _r == [0], "Test case 2 failed"

_r = fibonacci_sequence(0)
print("actual: " + str(_r))
assert _r == [], "Test case 3 failed"

_r = fibonacci_sequence(10)
print("actual: " + str(_r))
assert _r == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34], "Test case 4 failed"

print("TESTS PASSED")