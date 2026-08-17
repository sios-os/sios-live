_r = sum_even_numbers([1, 2, 3, 4, 5, 6])
print("actual: " + str(_r))
assert _r == 12

_r = sum_even_numbers([-2, -1, 0, 1, 2])
print("actual: " + str(_r))
assert _r == 0

_r = sum_even_numbers([7, 9, 11])
print("actual: " + str(_r))
assert _r == 0

print("TESTS PASSED")