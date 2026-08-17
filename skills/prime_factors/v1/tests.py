_r = prime_factors(18)
print("actual: " + str(_r))
assert _r == [2, 3, 3], "Test case 1 failed"

_r = prime_factors(100)
print("actual: " + str(_r))
assert _r == [2, 2, 5, 5], "Test case 2 failed"

_r = prime_factors(13)
print("actual: " + str(_r))
assert _r == [13], "Test case 3 failed"

print("TESTS PASSED")