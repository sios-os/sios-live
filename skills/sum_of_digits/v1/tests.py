_r = sum_of_digits(123)
print("actual: " + str(_r))
assert _r == 6

_r = sum_of_digits(-456)
print("actual: " + str(_r))
assert _r == 15

_r = sum_of_digits(0)
print("actual: " + str(_r))
assert _r == 0

print("TESTS PASSED")