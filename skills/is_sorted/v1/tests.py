_r = is_sorted([1, 2, 3, 4, 5])
print("actual: " + str(_r))
assert _r == True

_r = is_sorted([5, 4, 3, 2, 1])
print("actual: " + str(_r))
assert _r == False

_r = is_sorted([1, 1, 1, 1, 1])
print("actual: " + str(_r))
assert _r == True

_r = is_sorted([])
print("actual: " + str(_r))
assert _r == True

_r = is_sorted([7])
print("actual: " + str(_r))
assert _r == True

print("TESTS PASSED")