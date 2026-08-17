_r = interleave_lists([1, 3, 5], [2, 4, 6])
print("actual: " + str(_r))
assert _r == [1, 2, 3, 4, 5, 6]

_r = interleave_lists(['a', 'c'], ['b', 'd', 'e'])
print("actual: " + str(_r))
assert _r == ['a', 'b', 'c', 'd', 'e']

_r = interleave_lists([], [1, 2])
print("actual: " + str(_r))
assert _r == [1, 2]

print("TESTS PASSED")