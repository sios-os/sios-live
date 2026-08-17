_r = fibonacci(10)
print("actual: " + str(_r))
assert _r == 55

_r = fibonacci(1)
print("actual: " + str(_r))
assert _r == 1

_r = fibonacci(0)
print("actual: " + str(_r))
assert _r == 0

print("TESTS PASSED")