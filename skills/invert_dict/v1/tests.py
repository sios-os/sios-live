_r = invert_dict({'a': 1, 'b': 2})
print("actual: " + str(_r))
assert _r == {1: 'a', 2: 'b'}

_r = invert_dict({})
print("actual: " + str(_r))
assert _r == {}

_r = invert_dict({1: 'a', 2: 'b', 3: 'c'})
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 2, 'c': 3}

print("TESTS PASSED")