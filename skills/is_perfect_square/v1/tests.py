_r = is_perfect_square(16)
print("actual: " + str(_r))
assert _r == True, "Test case 1 failed"

_r = is_perfect_square(14)
print("actual: " + str(_r))
assert _r == False, "Test case 2 failed"

_r = is_perfect_square(0)
print("actual: " + str(_r))
assert _r == True, "Test case 3 failed"

_r = is_perfect_square(1)
print("actual: " + str(_r))
assert _r == True, "Test case 4 failed"

_r = is_perfect_square(-4)
print("actual: " + str(_r))
assert _r == False, "Test case 5 failed"

print("TESTS PASSED")