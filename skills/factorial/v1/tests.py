_r = factorial(5)
print("actual: " + str(_r))
assert _r == 120

_r = factorial(0)
print("actual: " + str(_r))
assert _r == 1

try:
    _r = factorial(-1)
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Input must be a non-negative integer"

print("TESTS PASSED")