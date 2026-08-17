_r = power_of_two(0)
print("actual: " + str(_r))
assert _r == 1, "Expected 1"

_r = power_of_two(5)
print("actual: " + str(_r))
assert _r == 32, "Expected 32"

_r = power_of_two(-1)
print("actual: " + str(_r))
assert _r == 0.5, "Expected 0.5"

print("TESTS PASSED")