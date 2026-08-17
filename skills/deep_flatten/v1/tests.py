_r = deep_flatten([1, [2, 3], [4, [5, 6]]])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5, 6]

_r = deep_flatten(['a', ['b', 'c'], ['d', ['e', 'f']]])
print("actual: " + str(_r))
assert _r == ['a', 'b', 'c', 'd', 'e', 'f']

_r = deep_flatten([[], [1, [], 2], 3])
print("actual: " + str(_r))
assert _r == [1, 2, 3]

print("TESTS PASSED")