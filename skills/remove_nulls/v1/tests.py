_r = remove_nulls([1, None, 2, None, 3])
print("actual: " + str(_r))
assert _r == [1, 2, 3]

_r = remove_nulls([None, None, None])
print("actual: " + str(_r))
assert _r == []

_r = remove_nulls([])
print("actual: " + str(_r))
assert _r == []

print("TESTS PASSED")