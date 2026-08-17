_r = binary_search([1, 2, 3, 4, 5], 3)
print("actual: " + str(_r))
assert _r == 2

_r = binary_search(['a', 'b', 'c', 'd'], 'c')
print("actual: " + str(_r))
assert _r == 2

_r = binary_search([10, 20, 30], 25)
print("actual: " + str(_r))
assert _r == -1

print("TESTS PASSED")