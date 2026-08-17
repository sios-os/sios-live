_r = collatz_steps(1)
print("actual: " + str(_r))
assert _r == 0

_r = collatz_steps(6)
print("actual: " + str(_r))
assert _r == 8

_r = collatz_steps(7)
print("actual: " + str(_r))
assert _r == 16

print("TESTS PASSED")